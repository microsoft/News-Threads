import pandas as pd
import configparser
from . import get_epsilon_cluster_filename, get_common_config


def build_hierarchy(config: configparser.SectionProxy):
    hierarchyMaxEpsilon = get_common_config()['HierarchyMaxEpsilon']

    dfprior = pd.read_csv(get_epsilon_cluster_filename(config, 0), header=None).set_index(1)
    dfcurrent = pd.read_csv(get_epsilon_cluster_filename(config, 1), header=None).set_index(1)
    joined = dfcurrent.join(dfprior, lsuffix='_' + str(1), rsuffix='_' + str(0))
    for x in range(2, int(hierarchyMaxEpsilon) + 1):
        dfcurrent = pd.read_csv(get_epsilon_cluster_filename(config, x), header=None).set_index(1)
        joined = dfcurrent.join(joined, lsuffix='_' + str(x), rsuffix='_' + str(x-1))
    joined.to_csv(config['IntermediateClusterHierarchyFileName'])

    # Re-read the intermediate file
    df = pd.read_csv(config['IntermediateClusterHierarchyFileName'])

    hash_edges = {}
    for row in df.iterrows():
        # Maximal clusters starting at 53
        prevcluster = row[1]['0_' + hierarchyMaxEpsilon]

        if prevcluster == -1:
            continue
        for x in range(int(hierarchyMaxEpsilon), -1, -1):
            nextcluster = row[1]['0_' + str(x)]
            if nextcluster == -1:
                docid = row[1][0]
                hash_edges[str(prevcluster) + '_' + str(x+1) + ',' + str(docid)] = 1
                break
            ky = str(prevcluster) + '_' + str(x+1) + ',' + str(nextcluster) + '_' + str(x)
            if ky not in hash_edges:
                hash_edges[ky] = 0
            hash_edges[ky] += 1

            # Build the last stage of the graph if we make it to layer 0
            if x == 0:
                docid = row[1][0]
                ky = str(nextcluster) + '_' + str(x) + ',' + str(docid)
                hash_edges[ky] = 1
            prevcluster = nextcluster

    fout = open(config['OutputHierarchyGraphEdgesFileName'], 'w')
    for edge in hash_edges:
        fout.write(edge + ',' + str(hash_edges[edge]) + '\n')
    fout.close()
