import configparser


def get_dataset_config() -> configparser.SectionProxy:
    """Retrieves the configuration section for the currenty dataset.  Dataset is specified in the
    'Common' config section"""
    parser = configparser.ConfigParser()
    parser.read('news_threads.conf')
    dataset_name: str = parser['Common']['DatasetName']
    return parser[dataset_name]  # Returns the config section for the current dataset


def get_common_config() -> configparser.SectionProxy:
    """Retrieves the common configuration section."""
    parser = configparser.ConfigParser()
    parser.read('news_threads.conf')
    return parser['Common']


def get_epsilon_cluster_filename(section: configparser.SectionProxy, epsilon: int) -> str:
    """Retrieves the cluster filename for a specific epsilon."""
    parser = section.parser
    dataset_name = parser['Common']['DatasetName']
    return parser.get(dataset_name, 'OutputEpsilonClustersFileNames', vars={'epsilon': str(epsilon)})
