#!/usr/bin/env python3
"""Stackoverflow Analytics Module

This module is designed to make stackoverflow analytic.
This module is based on the class StackoverflowAnalytics. It contains the methods for
making Stackoverflow analytic.

This file can also be imported as a module and contains the following
functions:
	* load_dataset - load dataset from file
	* build_analitycs - create StackoverflowAnalytic from documents
	* main - the main function of the script
"""
import re
import csv
from collections import defaultdict
import json
from typing import List, Dict
import logging
import logging.config
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import xml.etree.ElementTree as et
import yaml

APPLICATION_NAME = "task_Hubbatulin_Mark_stackoverflow_analytics"
DEFAULT_LOGGING_CONF_FILEPATH = "logging.conf.yml"
logger = logging.getLogger(APPLICATION_NAME)

DEFAULT_DATASET = "stackoverflow_posts_sample.xml"
DEFAULT_STOPWORDS = "stop_words_en.txt"
DEFAULT_QUIRIES = "query_sample_1.csv"


class StackoverflowAnalytics:
    """This class stackoverflow site analysis

    ----------
    Attributes
    word2top : dict
        Dictionary: [word] = ['year': score, 'year': score....]

    Methods

    query(start_year, end_year, top_k)
        Returns a dict of answers on queries
        {'start': start_year, 'end': end_year, 'top': [('word_1': score_1), ...]}
    """

    def __init__(self, stopwords: str):
        self.word2top = defaultdict(list)
        self.stopwords = []
        if stopwords:
            with open(stopwords, 'r', encoding='koi8-r') as fin:
                self.stopwords = [word.strip() for word in fin.readlines()]

    def __eq__(self, other):
        if not isinstance(other, dict):
            return False
        return self.word2top == other

    def query(self, start_year: int, end_year: int, top_n: int) -> Dict:
        """Request for analytics for a period
        :param
        ---------
        start_year : int
            Analysis start year
        end_year : int
            Analysis end year
        top_n : int
            Top m for word`s with highest score
        :return
        ---------
        dict
            Returns a dictionary with top words
             {'start': start_year, 'end': end_year, 'top': [('word_1': score_1), ...]}
        """
        logger.debug('got query "%s,%s,%s"', start_year, end_year, top_n)
        answer = defaultdict(int)
        for key, values in self.word2top.items():
            for value in values:
                if start_year <= value[0] <= end_year:
                    answer[key] += value[1]

        answer = sorted(answer.items(), key=lambda x: (-x[1], x[0]))
        if len(answer) < top_n:
            logger.warning(
                'not enough data to answer, found %s words out of %s for period "%s,%s"',
                len(answer), top_n, start_year, end_year
            )
        answer = [list(x) for x in answer[:top_n]]
        answer = {"start": start_year, "end": end_year, "top": answer}
        return answer


def load_dataset(filepath: str) -> List:
    """This function load dataset
    Function load dataset from XML file and return list of dictionaries with required data.

    :param
    ---------
    filepath : str
        Dataset filepath
    :return
    ---------
    List
        List type - list of dict [{'score': int, 'year': int, 'title': str}, ...]
    """
    logger.info("process XML dataset")
    with open(filepath, 'r', encoding='utf-8') as fin:
        lines = [line.strip() for line in fin.readlines()]
    dataset = []
    for line in lines:
        tree = et.fromstring(line)
        if tree.attrib['PostTypeId'] == '1':
            score = int(tree.attrib['Score'])
            title = tree.attrib['Title']
            year = int(tree.attrib['CreationDate'].split('-')[0])
            dataset.append(
                {
                    'score': score,
                    'year': year,
                    'title': title
                    }
            )
    return dataset


def build_analitycs(dataset: list, stopwords_filepath: str) -> object:
    """This function create Stackoverflow Object for queries
    :param
    ---------
    dataset : list
        List of the questions from Stackoverflow
    stopwords_filepath : str
        Path to stopwords
    :return
    ---------
    object
        Stackoverflow_Analytics object for queries
    """
    analytics = StackoverflowAnalytics(stopwords_filepath)
    analytics.word2top = defaultdict(list)
    for row in dataset:
        words = re.findall(r"\w+", row['title'].lower())
        for word in set(words):
            word = word.strip()
            if word not in analytics.stopwords:
                analytics.word2top[word].append((row['year'], row['score']))

    return analytics


def process_build(filepath, stopwords):
    """Process for building Analytics"""
    dataset = load_dataset(filepath)
    analitycs = build_analitycs(dataset, stopwords)
    logger.info("ready to serve queries")
    return analitycs


def process_queries(filepath):
    """Process for loading queries"""
    queries = []
    with open(filepath, "r") as fin:
        reader = csv.reader(fin)
        for row in reader:
            queries.append({'start_year': int(row[0]),
                            'end_year': int(row[1]),
                            'top_N': int(row[2])})
    return queries


def stackoverflow_callback(arguments):
    """Main stackoverflow callback"""
    analitycs = process_build(arguments.dataset_filepath, arguments.stopwords_filepath)
    queries = process_queries(arguments.queries)
    for query in queries:
        answer = analitycs.query(query['start_year'], query['end_year'], query['top_N'])
        print(json.dumps(answer))
    logger.info("finish processing queries")


def setup_parser(parser):
    """Function for setup the parser"""
    parser.add_argument(
        "-qst", "--questions", dest="dataset_filepath",
        help="Path to dataset to load, default path is %(default)s",
        metavar='DATASET', default=DEFAULT_DATASET,
    )
    parser.add_argument(
        "-s", "--stop-words", dest="stopwords_filepath",
        help="Path to stopwords to load, default path is %(default)s",
        metavar='STOPWORDS', default=DEFAULT_STOPWORDS,
    )
    parser.add_argument(
        "-q", "--queries", dest="queries",
        help="Path to queries to load, default path is %(default)s",
        metavar='QUERIES', default=DEFAULT_STOPWORDS,
    )
    parser.set_defaults(callback=stackoverflow_callback)


def setup_logging(filepath=DEFAULT_LOGGING_CONF_FILEPATH):
    """Setup logging configurations from file"""
    with open(filepath) as config_fin:
        logging.config.dictConfig(yaml.safe_load(config_fin))


def main():
    """Main function of the module"""
    setup_logging()
    parser = ArgumentParser(
        prog="Stackoverflow analytics",
        description="The application provides answers to questions \
                            about the most popular topics for discussion for the specified period",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()
