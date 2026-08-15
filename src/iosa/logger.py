import logging
from pathlib import Path

Path('logs').mkdir(exist_ok=True)


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:  # avoid duplicate handlers if called more than once
        return logger

    file_handler = logging.FileHandler('logs/iosa.log')
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


if __name__ == '__main__':
    logger = setup_logger('iosa.test')
    logger.info('This is a test log message.')
    logger.warning('This is a warning log message.')