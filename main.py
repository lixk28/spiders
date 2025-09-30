import os
import logging
import argparse


def setup_logging():
    LOGS_PATH = os.getenv('LOGS_PATH', 'logs')
    if os.path.exists(LOGS_PATH) and os.path.isdir(LOGS_PATH):
        pass
    else:
        os.makedirs(LOGS_PATH)


def parse_args():
    parser = argparse.ArgumentParser()

    return parser.parse_args()

def main(args):
    pass

if __name__ == "__main__":
    args = parse_args()
    main(args)
