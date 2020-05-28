
# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Introduction 
The News Threads project analyzes news articles to help find similarities between news articles and trace news provenance across time.

# Getting Started
## Prerequisites
* Python 3.6 or newer
* Data in the correct input format.
* Change the input data path in news_threads.conf.
* The news_threads.conf file contains information about the config format.

## Data Format
* Input data is a single CSV named documents.csv with news articles in the folder specified in news_threads.conf
* Format is: (canonical_url, title, doc_id, domain, text, first_scrape_date)
* You may change the format by modifying the "build_minhash" method in dbscan.py
* Additional fields are ignored by default
* Field description:
    * **canonical_url**: URL of the news article
    * **title**: Title of the news article
    * **doc_id**: A unique ID for the article.  This may be text or numeric.
    * **domain**: Domain on which the article was published.  "apnews.com", "cnn.com", etc.
    * **text**: Article text
    * **first_scrape_date**: Date the web crawler first downloaded the article.

## Linux
1. run "make init" from the root of the folder to build a Python virtual environment with all dependencies
2. Type "source .env/bin/activate" to launch the virtual environment.
3. Type "python -m newsthreads" to run the news threads pipeline

## Windows
1. "python -m venv .env"
2. ".env\Scripts\activate.bat"
3. "pip3 install -r requirements.txt"
4. Type "python -m newsthreads" to run the news threads pipeline

# Output files
* **document_metadata.csv**: "documentId, firstScrapedDate, title" for every document.  This puts the document into a standard format so other pieces of code can read it.
* **hierarchy_graph_edges.csv**: This file contains two row formats intermingled.  The purpose of this file is to determine the hierarchy of clusters by epsilon value (which clusters are parents of other clusters).
    * Leaf-rows: These rows have documents that no longer fall in a cluster at a specific epsilon value.  The format is:  "previousClusterId_previousEpsilon, documentId, 1"
    * Non-leaf rows:  Clusters in these rows are not leafs in the hierarchy.  The format is: "previousClusterId_previousEpsilon, clusterId_epsilon, count"
        * previousClusterId: ID of the cluster that is the parent of the current cluster in the hierarchy.
        * previousEpsilon: Epsilon at which the previous cluster was generated.
        * clusterId: ID of the current cluster.  This cluster is a subset of the parent cluster.
        * epsilon:  Epsilon at which the current cluster was generated.  This will be previousEpsilon - 1.
        * count: Weight of the link between previousClusterId and clusterId at their respective epsilons.  Higher weight means more documents are in the child cluster.
* Clusters (DBSCAN)
    * **epsilon-cluster.csv**: "epsilon, clusterCount" Number of unique clusters at each epsilon.
    * **clusters_%(epsilon)s.csv**: "clusterId, document id" for all documents that are in clusters at the epsilon specified by the file name.
    * **joined_cluster_labels.csv**: "clusterid,docid,epsilon" for each document at every epsilon level at which the document has a cluster.
* Sentences
    * **fragment_summaries.csv**: "docid,sent_id,sentnum" for every sentence where the sentnum is the zero-based index of the sentence within the document.  A sentnum of "0" means that it is the first sentence in the document.  A sentnum of "1" means that it is the second sentence in the document.  Etc.
    * **fragment_metadata.csv**: "docid,date,domain" for every document referenced by fragment_summaries.csv.  Date is the web crawler scrape date.
    * **sentence_id_lookup.csv**: "text, sentence_id" for every unique sentence.
* News/Domain Graph outputs
    * **domain_graph_sentence_count.csv**: "Source,Target,Weight" 
        * Source is a domain that has news articles
        * "Target" is a domain that has news articles that were copied by the "Source" domain.
        * "Weight" is the number of sentences that "Source" copied from "Target". 
    * **sentence_origin.csv**: "sent_id, domain" where the domain is the internet domain where the sentence was first seen by the crawler.
    * **domain_graph.csv**: "Source,Target,Weight"
        * Source is a domain that has news articles
        * Target is a domain that has news articles that were copied by the "Source" domain.
        * Weight is the number of documents that "Source" copied from "Target".

