# First we can build out an LSH Jaccard distance matrix from all docs to all other docs
# Maybe we build at different granularities... then we maybe look at sentence level diffs?
# Sent2vec / doc2vec as well?

# goal being able to detect major forks and modifications on those forks

import csv
import string
import pickle
from sklearn.cluster import DBSCAN
from . import get_epsilon_cluster_filename, get_logger
import os
from datasketch import MinHash
from multiprocessing import Pool, Value
from typing import List, Tuple, Dict
from scipy.sparse import csr_matrix, lil_matrix

csv.field_size_limit(2**23)

translator = str.maketrans('', '', string.punctuation)

logger = get_logger(os.path.basename(__file__))

totalCalculationsPerformed: Value = Value('i', 0)


def chunk_list(list: List[str], chunkSize: int) -> List[Tuple[int, List[str]]]:
    """Converts a list into an iterable of lists where each list of of one chunk size"""
    result: List[Tuple[int, List[str]]] = []
    for index in range(0, len(list), chunkSize):
        result.append((index, list[index:(index + chunkSize)]))
    return result


def build_minhash(config):
    fin = open(config['InputDocumentFileName'], 'r', encoding='utf-8')
    fin.readline()
    csvreader = csv.reader(fin, delimiter=',', escapechar='\\')
    arryHash: Dict[str, MinHash] = {}
    counter = 0
    linenumber = 0
    hash_dup: Dict[str, int] = {}
    fout = open(config['IntermediateColumnFilteredFileName'], 'w', encoding='utf-8', newline='')
    csvwriter = csv.writer(fout)
    csvwriter.writerow(['DocId', 'FirstScrapeDate', 'Title', 'Domain', 'Text'])

    logger.info('Writing column filtered document CSV and generating MinHashes for each document')

    for line in csvreader:
        linenumber += 1
        (canonical_url, title, doc_id, domain, text, first_scrape_date) = line[0:6]
        csvwriter.writerow([doc_id, first_scrape_date, title, domain, text])
        document_key = doc_id
        ky = canonical_url + ':' + title
        if ky in hash_dup:
            # Skip if we've seen this before
            continue

        hash_dup[ky] = 0
        body = title + ' ' + text
        body = body.translate(translator)

        arryHash[document_key] = MinHash(num_perm=256)
        for word in set(body.encode('utf-8').lower().split()):
            arryHash[document_key].update(word)
        counter += 1
        if counter % 1000 == 0:
            logger.info(f'Created {counter:n} MinHash objects from documents')

    id_list: list = list(sorted(arryHash.keys()))
    pickle.dump(id_list, open(config['IntermediateDocIdListFileName'], 'wb'), protocol=4)
    fout.close()
    return (id_list, arryHash)


def _create_partial_csr_matrix(
        arryHash: Dict[str, MinHash],
        totalCalculations: int,
        x_ids: List[str],
        x_offset: int,
        y_ids: List[str],
        y_offset: int) -> csr_matrix:
    x_counter = x_offset
    thread_counter = 0
    allpairs: lil_matrix = lil_matrix((len(arryHash), len(arryHash)))
    LOG_COUNTER_STEP = 200000
    for x_key in x_ids:
        y_counter = y_offset
        for y_key in y_ids:
            if y_key < x_key:
                jaccard = 1 - arryHash[x_key].jaccard(arryHash[y_key])
                if jaccard == 0:
                    jaccard = 0.000000001
                if jaccard < 0.6:
                    allpairs[y_counter, x_counter] = jaccard
                    allpairs[x_counter, y_counter] = jaccard
            else:
                continue
            thread_counter += 1
            if thread_counter % LOG_COUNTER_STEP == 0:
                # Log the total cross-thread counter and increment it by the current in-thread value
                with totalCalculationsPerformed.get_lock():
                    totalCalculationsPerformed.value += LOG_COUNTER_STEP
                    logger.info(f'Performed {thread_counter:n} jaccard calculations in this thread.  Performed '
                                f'{totalCalculationsPerformed.value:n} total calculations out of {totalCalculations:n}')
            y_counter += 1
        x_counter += 1
    # Add the number of calculations since we last logged
    totalCalculationsPerformed.value += thread_counter
    return csr_matrix(allpairs)


def calculate_jaccard(config, id_list, arryHash: Dict[str, MinHash]):
    totalCalculations = len(arryHash) * len(arryHash)
    logger.info(f'Total jaccard calculations to perform: {totalCalculations:n}')
    split_id_list: List[Tuple[int, List[str]]] = chunk_list(id_list, 20000)

    def _collect_results(initial: csr_matrix, result: csr_matrix):
        if initial is not None:
            return initial + result
        else:
            return result

    pool = Pool()
    create_csr_args: List[Tuple[Dict[str, MinHash], int, List[str], int, List[str], int]] = []
    for (x_offset, x_ids) in split_id_list:
        for (y_offset, y_ids) in split_id_list:
            create_csr_args.append(
                (
                    arryHash,
                    totalCalculations,
                    x_ids,
                    x_offset,
                    y_ids,
                    y_offset,
                )
            )
    result_matrix_list: List[csr_matrix] = pool.starmap(_create_partial_csr_matrix, create_csr_args)

    logger.info(f"Merging {len(result_matrix_list)} csr_matrices")
    csr_allpairs: csr_matrix = None
    for matrix in result_matrix_list:
        csr_allpairs = _collect_results(csr_allpairs, matrix)
    logger.info("Launched all CSR matrix jobs")
    pool.close()
    pool.join()
    logger.info(f"Saving CSR matrix")
    pickle.dump(csr_allpairs, open(config['IntermediatePairwiseDistanceCsrFileName'], 'wb'), protocol=4)
    logger.info('Finished generating jaccard calculations')


def _perform_dbscan(eps: int, config, dockeys, csr_allpairs):
    logger.info(f'Generating DBSCAN for epsilon {eps:n}')
    epsilon = eps * 0.01 + 0.00000001
    clusterer = DBSCAN(eps=epsilon, min_samples=2, metric='precomputed')
    clusterer.fit(csr_allpairs)
    fout = open(get_epsilon_cluster_filename(config, eps), 'w')
    lbls = zip(clusterer.labels_, list(dockeys))

    for lbl in lbls:
        _ = fout.write(str(lbl[0]) + ',' + str(lbl[1]) + '\n')
    fout.close()
    # get the max number of clusters from the run and store it so we can visualize the curve sweep
    return (eps, max(clusterer.labels_))


def perform_dbscan(config):
    dockeys = pickle.load(open(config['IntermediateDocIdListFileName'], 'rb'))
    csr_allpairs = pickle.load(open(config['IntermediatePairwiseDistanceCsrFileName'], 'rb'))
    maximumEpsilonToGenerate = 99
    logger.info(f'Generating DBSCAN results '
                f'for {maximumEpsilonToGenerate:n} epsilons starting at {maximumEpsilonToGenerate:n}')

    pool = Pool()
    perform_dbscan_args: List[Tuple[int, config, List[str], csr_matrix]] = []
    for eps in range(maximumEpsilonToGenerate, -1, -1):
        perform_dbscan_args.append(
            (
                eps,
                config,
                dockeys,
                csr_allpairs,
            )
        )
    dbscan_result_list: List[Tuple[int, int]] = pool.starmap(_perform_dbscan, perform_dbscan_args)
    pool.close()
    pool.join()

    logger.info('Finished DBSCAN for all epsilons')

    logger.info("Writing Epsilon and Clusters CSV")
    fout = open(config['OutputEpsilonClusterFileName'], 'w')
    for (epsilon, cluster_count) in dbscan_result_list:
        fout.write(str(epsilon) + ',' + str(cluster_count) + '\n')
    fout.close()
