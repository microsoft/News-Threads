import csv
import sklearn.feature_extraction.text
import numpy
import configparser
from . import get_epsilon_cluster_filename, get_common_config, get_logger
from typing import Dict, Tuple, List, Optional
import os

logger = get_logger(os.path.basename(__file__))


def combine_cluster_labels(config: configparser.SectionProxy):
    # If you have a partially-processed dataset disable the parts you have
    # already done
    write_joined_cluster_labels = True
    write_cluster_epsilon_representative_docid = True

    logger.info("Reading intermediate file")
    hierarchyMaxEpsilon: int = int(get_common_config()['HierarchyMaxEpsilon'])
    csv.field_size_limit(2**23)

    fin = open(config['IntermediateColumnFilteredFileName'], 'r', encoding='utf-8')
    fin.readline()
    fout = open(config['OutputDocumentMetadataFileName'], 'w', encoding='utf-8', newline='')

    logger.info("Writing document metadata file")
    csvreader = csv.reader(fin, delimiter=',')
    csvwriter = csv.writer(fout, delimiter=',')
    csvwriter.writerow(['documentId, firstScrapedDate, title'])
    hash_doc = {}
    for line in csvreader:
        (documentId, firstScrapedDate, title, domain, text) = line
        hash_doc[documentId] = title
        csvwriter.writerow([documentId, firstScrapedDate, title])
    fout.close()
    fin.close()

    logger.info("Finished writing document metadata")

    fin = open(get_epsilon_cluster_filename(config, hierarchyMaxEpsilon), 'r')
    hash_clusterhit = {}
    for line2 in fin:
        clusterid = int(line2.split(',')[0])
        docid = line2.split(',')[1].strip()

        hash_clusterhit[docid] = str(clusterid)

    fin.close()

    if write_joined_cluster_labels:
        logger.info("Writing joined cluster labels")
        fout = open(config['OutputJoinedClusterLabelsFileName'], 'w')
        fout.write('clusterid,docid,epsilon\n')
        hash_clustereps: Dict[Tuple[str, int], List[str]] = {}
        hash_clusterstats: Dict[Tuple[str, int], int] = {}
        for x in range(0, int(hierarchyMaxEpsilon) + 1):
            fin = open(get_epsilon_cluster_filename(config, x), 'r')
            for line3 in fin:
                # Get the epsilon and the clusterid
                clusterid = int(line3.split(',')[0])

                ky = (str(x), clusterid)
                # Track the size of the cluster
                if ky not in hash_clusterstats:
                    hash_clusterstats[ky] = 0
                # for computing size later
                hash_clusterstats[ky] += 1

                docid = line3.split(',')[1].strip()

                if ky not in hash_clustereps:
                    hash_clustereps[ky] = []
                hash_clustereps[ky].append(docid)
                fout.write(line3.strip() + ',' + str(x) + '\n')
            fin.close()
        fout.close()

    if write_cluster_epsilon_representative_docid:
        logger.info("Writing cluster epsilon representative docids")
        fout = open(config['IntermediateClusterEpsilonRepresentativeDocId'], 'w', encoding='utf-8')
        _ = fout.write('epsilon,clusterid,representativedocid,ancestorclusterid,size,titlesummary\n')
        for ky2 in hash_clustereps:
            repdoc: Optional[str] = None
            maxtitlehits = 0
            hash_titles = {}
            bow_arry = []
            # Skip the -1 clusters.  These are nodes/documents that do not fit in a cluster
            if ky2[1] == -1:
                continue
            # iterate through for each cluster/eps pairing and get the most frequently occuring title
            for doc in hash_clustereps[ky2]:
                title = hash_doc[doc]
                bow_arry.append(title)
                if repdoc is None:
                    repdoc = doc
                    maxtitlehits = 1
                    hash_titles[title] = (doc, 1)
                    continue
                else:
                    if title in hash_titles:
                        pair = hash_titles[title]
                        hits = 1 + pair[1]
                        if hits > maxtitlehits:
                            maxtitlehits = hits
                            repdoc = pair[0]
                            # save the incremented value
                            hash_titles[title] = (pair[0], hits)
                    else:
                        hash_titles[title] = (doc, 1)
            count_vec = sklearn.feature_extraction.text.CountVectorizer('content', stop_words='english')
            try:
                model = count_vec.fit(bow_arry)
                invmodel = {v: k for k, v in model.vocabulary_.items()}
                fit_matrix = count_vec.transform(bow_arry)

                # can make this a lot faster if we just sum by column!
                # Summation by column
                topterms = []
                columnsums = fit_matrix.sum(axis=0)
                # Get the top items

                arryidx = numpy.array(columnsums)[0]
                # Sort the array by index - keep the top 10 terms
                sortedarry = numpy.flip(numpy.argsort(arryidx), axis=0)[0:10]
                # Then pull out the vocab terms
                for vocab_key in sortedarry:
                    topterms.append(invmodel[vocab_key])
                # Join them together for a summary
                termconcat2 = '\t'.join(topterms)
            except Exception:
                termconcat2 = ''

            _ = fout.write(f'{str(ky2[0])},{str(ky2[1])},{repdoc},{str(hash_clusterhit[str(repdoc)])},'
                           f'{str(hash_clusterstats[ky2])},{termconcat2}\n')
        fout.close()
        logger.info("Finished combine_cluster_labels")
