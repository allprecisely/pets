import logging
import sys


def init_logger(log_level=logging.INFO):
    root_logger = logging.getLogger()
    formatter = logging.Formatter("%(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(log_level)

    # file_handler = logging.FileHandler(filename="tmp.log")

    root_logger.addHandler(stdout_handler)
    # root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)
