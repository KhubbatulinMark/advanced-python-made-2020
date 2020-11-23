"""Inverted Index Module

This module is designed to work with inverted index.
This module is based on the class Inverted index. It contains the logic of inverted index work.
it allows you to load from a file, save, and query the inverted index.

This file can also be imported as a module and contains the following
functions:

	* load_documents - load documents from file
	* build_inverted_index - create Inverted Index from documents
	* main - the main function of the script
"""
import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType, ArgumentTypeError
from io import TextIOWrapper
from collections import defaultdict
from typing import List
import logging

from storage_policy import StructPolicy

logger = logging.getLogger(__name__)

DEFAULT_DATASET_PATH = "wikipedia_sample"
DEFAULT_INDEX_PATH = "inverted.index"

class EncodedFileType(FileType):
    """TODO
    """

    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding=self._encoding)
                return stdin
            if 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding=self._encoding)
                return stdout
            msg = 'argument "-" with mode %r' % self._mode
            raise ValueError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as Exception:
            message = "can't open '%s': %s"
            raise ArgumentTypeError(message % (string, Exception)) from Exception

class InvertedIndex:
    """This class describes an Inverted Index
    ----------
    Attributes

    term2doc : dict
        Dictionary: [term] = [document`s id list]

    Methods

    query(words list)
        Returns a list of documents containing the requested words
    dump(filepath str)
        Save index to disk
    load(words list)
        This class method allows you to load an index from a file.
    """

    def __init__(self):
        self.term2doc = defaultdict()

    def __eq__(self, other):
        if not isinstance(other, InvertedIndex):
            return False
        return self.term2doc == other.term2doc

    def dump(self, filepath: str, storage_policy=StructPolicy) -> None:
        """Save index to disk function

        :param
        ---------
        filepath : str
            The path where the index is saved
        storage_policy : object
            The storage policy
        """
        logger.info("Dump inverted index to %s", filepath)
        storage_policy.dump(self.term2doc, filepath)

    @classmethod
    def load(cls, filepath: str, storage_policy=StructPolicy) -> object:
        """This class method allows you to load an index from a file.
        Once loaded it will return an inverted index class object.

        :param
        ---------
        filepath : str
            Inverted index file path
        storage_policy : object
            The storage policy
        :return
        ---------
        dict
            Dictionary type - key: document id, value: list of words in this document
        """
        logger.info("Loading inverted index from %s", filepath)
        index = InvertedIndex()
        index.term2doc = storage_policy.load(filepath)

        return index

    def query(self, words: List) -> List:
        """Returns a list of documents containing the requested words

        :param
        ---------
        words : list
            List of the words to be contained in the document
        :return
        ---------
        list
            List of the documents that contain the requested words
        """
        assert isinstance(words, list), (
            "Words should be provided with a list of words, but user provided:",
            f"{repr(words)}"
        )
        logger.debug("Query inverted index with request %s", (repr(words)))
        doc_id = set()
        first = True
        for word in words:
            if word not in self.term2doc.keys():
                continue
            if first:
                doc_id.update(self.term2doc[word])
                first = False
            else:
                doc_id.intersection_update(set(self.term2doc[word]))
        return list(doc_id)


def build_inverted_index(documents: dict) -> object:
    """Inverted Index building function

    :param
    ---------
    documents : dict
        Dictionary type - key: document id, value: list of words in this documents
    :return
    ---------
    object
        Built InveretedIndex object
    """
    logger.info("Building inverted index for provided documents....")
    index = InvertedIndex()
    index.term2doc = defaultdict(list)
    for doc_id, words in documents.items():
        for word in set(words.split()):
            if word not in index.term2doc.keys():
                index.term2doc[word].append(doc_id)
            if doc_id not in index.term2doc[word]:
                index.term2doc[word].append(doc_id)
    return index

def load_documents(filepath: str) -> dict:
    """This class method allows you to load an index from a file.
    Reads documents from a file and returns a dictionary of word lists across documents.

    :param
    ---------
    filepath : str
        Documents filepath
    :return
    ---------
    dict
        Dictionary type - key: document id, value: document text
    """
    logger.info("Loading documents from file...")
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = [line for line in file.readlines() if line.strip()]

    documents = {}
    for line in lines:
        doc_id, content = line.split('\t', maxsplit=1)
        documents[int(doc_id)] = ''.join(content).strip()
    return documents

def build_callback(arguments):
    """Callback for building inverted index"""
    dataset_path = (arguments.dataset)
    documents = load_documents(dataset_path)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(arguments.inverted_index_filepath)

def query_callback(arguments):
    return process_queries(arguments.inverted_index_filepath, arguments.query_file)

def process_queries(inverted_index_filepath, query_file):
    """Сallback for queries to the invested index"""
    logger.debug("Read queries from %s", inverted_index_filepath)
    inverted_index = InvertedIndex.load(inverted_index_filepath)
    for query in query_file:
        query = query.strip()
        document_ids = inverted_index.query([query])
        logger.debug("%s", document_ids)

def setup_parser(parser):
    """Function for setup the parser"""
    sub_parsers = parser.add_subparsers(help="choose command")

    build_parse = sub_parsers.add_parser(
        "build",
        help="Build index and save in binary into hard drive",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    build_parse.add_argument(
        "-d", "--dataset", dest="dataset",
        help="Path to dataset to load, default path is %(default)s",
        metavar='DATASET', default=DEFAULT_DATASET_PATH,
    )
    build_parse.add_argument(
        "-o", "--output", dest="inverted_index_filepath",
        help="Path to store inverted index in a binary format, default path is %(default)s",
        metavar='OUTPUT', default=DEFAULT_INDEX_PATH,
    )
    build_parse.set_defaults(callback=build_callback)

    query_parse = sub_parsers.add_parser(
        "query",
        help="query inverted index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    query_parse.add_argument(
        "-i", "--input", dest="inverted_index_filepath",
        help="Path to load inverted index, default path is %(default)s",
        metavar='INDEX', default=DEFAULT_INDEX_PATH,
    )
    query_parse.add_argument(
        "-q", "--query", dest="query",
        help="Query to run against inverted index",
        metavar='WORDS', required=False, nargs="+",
    )
    query_file_group = query_parse.add_mutually_exclusive_group(required=False)
    query_file_group.add_argument(
        "--query-file-utf8", dest="query_file",
        type=EncodedFileType('r', encoding='utf-8'),
        default=TextIOWrapper(sys.stdin.buffer, encoding='utf-8'),
        help="""Query to run against inverted index from file \
                with uft8 encode""",
    )
    query_file_group.add_argument(
        "--query-file-cp1251", dest="query_file",
        type=EncodedFileType('r', encoding='cp1251'),
        default=TextIOWrapper(sys.stdin.buffer, encoding='cp1251'),
        help="""Query to run against inverted index from file \
                  with cp1251 encode""",
    )
    query_parse.set_defaults(callback=query_callback)

def setup_logger():
    #logger = logging.getLogger('task_khubbatulin_mark_inverted_index')
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG
    )

def main():
    """Main function of the module"""
    setup_logger()
    parser = ArgumentParser(
        prog="inverted-index",
        description="Tool to build, dump, load and query inverted index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)

if __name__ == "__main__":
    main()
