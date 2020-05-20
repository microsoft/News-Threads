import logging


def get_logger(logger_name: str) -> logging.Logger:
    logging.basicConfig(
        format='%(asctime)s %(name)s [%(process)d-%(threadName)s] %(levelname)-4s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    return logging.getLogger(logger_name)
