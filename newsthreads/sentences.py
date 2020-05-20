# File #1: Fragment, FragmentId
# File #2: fragmentid, docid, date, domain, fragmentposition

import configparser
from typing import Dict, List, Tuple
import csv
import nltk.data
import string


def process_sentences(config: configparser.SectionProxy):
    csv.field_size_limit(2**23)
    fin = open(config['IntermediateColumnFilteredFileName'], 'r', encoding='utf-8')
    csvreader = csv.reader(fin)
    nltk.download('punkt')
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    translator = str.maketrans('', '', string.punctuation)

    doc_meta: Dict[str, Tuple[str, str]] = {}
    hash_sent: Dict[str, Dict[str, int]] = {}
    dict_sent: Dict[str, int] = {}
    sentCtr = 0
    linectr = 0
    for line in csvreader:
        (documentId, firstScrapedDate, title, domain, text) = line
        linectr += 1
        if linectr % 10000 == 0:
            print(linectr)
        sentences = sent_detector.tokenize(text.lower())

        lstsent: List[str] = list(map(lambda x: x.translate(translator), sentences))
        doc_meta[documentId] = (firstScrapedDate, domain)
        hash_sent[documentId] = {}
        sentnum = 0
        for sent in lstsent:
            if len(sent.split()) > 8:
                # Chunk off the sentence
                hash_sent[documentId][sent] = sentnum
                sentnum += 1
                if sent not in dict_sent:
                    dict_sent[sent] = sentCtr
                    sentCtr += 1

    fin.close()

    fout = open(config['OutputSentenceFragmentSummariesFileName'], 'w', encoding='utf-8')
    fout.write('docid,sent,sentnum\n')
    fout2 = open(config['OutputSentenceFragmentMetaFileName'], 'w')
    fout2.write('docid,date,domain\n')

    print('writing out')
    # next, from the perspective of the doc, find all derived and related content
    for outerdoc in hash_sent:
        for sent in hash_sent[outerdoc]:
            if sent in dict_sent:
                # docid, date, domain, sentence
                fout.write(outerdoc + ',' + str(dict_sent[sent]) + ',' + str(hash_sent[outerdoc][sent]) + '\n')
        fout2.write(outerdoc + ',' + doc_meta[outerdoc][0] + ',' + doc_meta[outerdoc][1] + '\n')
    fout.close()
    fout2.close()

    fout = open(config['OutputSentenceIdLookupFileName'], 'w', encoding='utf-8')
    for ky in dict_sent:
        fout.write(str(dict_sent[ky]) + ',' + str(ky) + '\n')
    fout.close()
    # sentence and ngram
