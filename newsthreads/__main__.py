from . import get_dataset_config, build_minhash, calculate_jaccard, perform_dbscan, combine_cluster_labels, \
    process_sentences, domain_dependency_graph, build_hierarchy
import configparser
import locale

config: configparser.SectionProxy = get_dataset_config()

locale.setlocale(locale.LC_ALL, '')  # Set locale so we get separators in numeric number formats

(id_list, arryHash) = build_minhash(config)
calculate_jaccard(config, id_list, arryHash)
perform_dbscan(config)

combine_cluster_labels(config)

process_sentences(config)

domain_dependency_graph(config)

build_hierarchy(config)
