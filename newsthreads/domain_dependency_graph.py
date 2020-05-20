import configparser
import csv
from datetime import datetime
from dateutil.parser import parse
from typing import Dict, Tuple
import os
from . import get_logger

logger = get_logger(os.path.basename(__file__))


def domain_dependency_graph(config: configparser.SectionProxy):
    logger.info("Calculating the domain dependency graph")
    logger.info("Reading sentence fragments")
    # First find the origin doc / domain associated with each sentence
    # Load up hash table on sentences
    fin = open(config['OutputSentenceFragmentSummariesFileName'], 'r')
    hash_sent: Dict[str, Dict[str, int]] = {}
    fin.readline()
    for line in fin:
        (docid, sent, sentnum) = line.strip().split(',')
        if sent not in hash_sent:
            hash_sent[sent] = {}
        hash_sent[sent][docid] = 0

    fin.close()

    csv.field_size_limit(2**23)

    # load up hash table on documents
    logger.info("Reading the column filtered intermediate file")
    fin = open(config['IntermediateColumnFilteredFileName'], 'r', encoding='utf-8')
    fin.readline()  # Skip header
    csvreader = csv.reader(fin)
    hash_doc: Dict[str, Tuple[str, datetime]] = {}
    for line2 in csvreader:
        (documentId, firstScrapedDate, title, domain, text) = line2
        dateinfo: datetime = parse(firstScrapedDate)
        hash_doc[documentId] = (domain, dateinfo)

    fin.close()

    # for each sentence, find the earliest document
    logger.info("Finding the first occurrence of each sentence")
    hash_sentorigin = {}
    for ky in hash_sent:
        earliestdate = None
        earliestdoc = ''
        for docid in hash_sent[ky]:
            if earliestdate is None:
                earliestdate = hash_doc[docid][1]
                earliestdoc = docid
                hash_sentorigin[ky] = (earliestdoc, earliestdate, hash_doc[docid][0])
            elif earliestdate > hash_doc[docid][1]:
                earliestdate = hash_doc[docid][1]
                earliestdoc = docid
                # tore the sentence id origin: docid, date, URI, rootdomain
                hash_sentorigin[ky] = (earliestdoc, earliestdate, hash_doc[docid][0])

    # Finally, for each sentence for each root domain, find the source domain.  We want to know which domains
    # copy from other domains
    logger.info("Finding the source domain for each sentence in each domain.")
    hash_depgraph: Dict[str, Dict[str, int]] = {}
    hash_sentgraph: Dict[str, Dict[str, int]] = {}
    for sentid in hash_sent:
        # origin domain
        for docid in hash_sent[sentid]:
            srcdomain = hash_doc[docid][0]
            destdomain = hash_sentorigin[sentid][2]
            ky = srcdomain + ',' + destdomain
            if ky not in hash_depgraph:
                hash_depgraph[ky] = {}
                hash_sentgraph[ky] = {}
            # only weight once per article
            hash_depgraph[ky][docid] = 0
            hash_sentgraph[ky][sentid] = 0

    logger.info("Writing domain graph")
    fout = open(config['OutputDomainGraphFileName'], 'w')
    fout.write('Source,Target,Weight\n')
    vertex_hash_doc: Dict[str, int] = {}
    vtx_orig_doc = {}
    for ky in hash_depgraph:
        fout.write(ky + ',' + str(len(hash_depgraph[ky])) + '\n')
        svtx = ky.split(',')[0]
        if svtx not in vertex_hash_doc:
            vertex_hash_doc[svtx] = 0
            vtx_orig_doc[svtx] = 0
        vertex_hash_doc[svtx] += len(hash_depgraph[ky])
        # Self loop - so original
        if ky.split(',')[1] == ky.split(',')[0]:
            vtx_orig_doc[svtx] += len(hash_depgraph[ky])
    fout.close()

    logger.info("Writing domain graph sentence counts")
    vertex_hash_sent: Dict[str, int] = {}
    vtx_orig_sent = {}
    fout = open(config['OutputDomainGraphSentenceCountFileName'], 'w')
    fout.write('Source,Target,Weight\n')
    for ky in hash_sentgraph:
        fout.write(ky + ',' + str(len(hash_sentgraph[ky])) + '\n')
        svtx = ky.split(',')[0]
        if svtx not in vertex_hash_sent:
            vertex_hash_sent[svtx] = 0
            vtx_orig_sent[svtx] = 0
        vertex_hash_sent[svtx] += len(hash_sentgraph[ky])
        # pull the weight off the self loop
        if ky.split(',')[1] == ky.split(',')[0]:
            vtx_orig_sent[svtx] += len(hash_sentgraph[ky])
    fout.close()

    # Build out compositional data per vertex and write it out to file
    logger.info("Writing sentence origins")
    fout = open(config['OutputSentenceOriginFileName'], 'w')
    for ky in hash_sentorigin:
        fout.write(ky + ',' + hash_sentorigin[ky][2] + '\n')
    fout.close()
