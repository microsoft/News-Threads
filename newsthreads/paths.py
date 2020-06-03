import os
import sys
import configparser
from . import get_logger

logger = get_logger(os.path.basename(__file__))


def ensure_paths_exist(config: configparser.SectionProxy):
    """Ensures that input data and output paths exist"""
    output_path = config['OutputPath']
    intermediate_path = config['IntermediatePath']
    input_file = config['InputDocumentFileName']
    if not os.path.exists(intermediate_path):
        logger.info(f"Creating path {intermediate_path}")
        os.makedirs(intermediate_path)
    if not os.path.exists(output_path):
        logger.info(f"Creating path {output_path}")
        os.makedirs(output_path)

    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} does not exist")
        sys.exit(1)  # Force interpreter to exit after error message above
