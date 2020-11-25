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


from storage_policy import StructPolicy

DEFAULT_DATASET_PATH = "../data/wik"
DEFAULT_INDEX_PATH = "../data/inverted.index"

class EncodedFileType(FileType):
    """Сhanged FileType
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

    def __repr__(self):
        args = self._mode, self._bufsize
        kwargs = [('encoding', self._encoding), ('errors', self._errors)]
        args_str = ', '.join([repr(arg) for arg in args if arg != -1] +
                             ['%s=%r' % (kw, arg) for kw, arg in kwargs
                              if arg is not None])
        return '%s(%s)' % (type(self).__name__, args_str)

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
        print(f"Dump inverted index to {filepath}", file=sys.stderr)
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
        print(f"Loading inverted index from {filepath}", file=sys.stderr)
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
        print(f"Query inverted index with request {repr(words)}", file=sys.stderr)
        doc_id = set()
        first = True
        for word in words:
            if word not in self.term2doc.keys():
                doc_id = []
                break
            if first:
                doc_id.update(self.term2doc[word])
                first = False
            else:
                doc_id.intersection_update(set(self.term2doc[word]))
        return sorted(list(doc_id))


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
    print("Building inverted index for provided documents....", file=sys.stderr)
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
    print("Loading documents from file...", file=sys.stderr)
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = [line for line in file.readlines() if line.strip()]

    documents = {}
    for line in lines:
        doc_id, content = line.split('\t', maxsplit=1)
        documents[int(doc_id)] = ''.join(content).strip()
    return documents

def build_callback(arguments):
    """Callback for building inverted index"""
    return process_build(arguments.dataset_filepath, arguments.inverted_index_filepath)

def process_build(dataset_filepath, inverted_index_filepath):
    """Process for building inverted index and dump"""
    print(f"Read documents from {dataset_filepath}", file=sys.stderr)
    documents = load_documents(dataset_filepath)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(inverted_index_filepath)

def query_callback(arguments):
    """Сallback for queries to the invested index"""
    if arguments.query:
        return process_querie_from_cli(arguments.inverted_index_filepath, arguments.query)
    return process_queries_from_files(arguments.inverted_index_filepath, arguments.query_file)

def process_querie_from_cli(inverted_index_filepath, query_list):
    """Process for query callback if query from CLI"""
    print(f"Queries is {query_list}", file=sys.stderr)
    inverted_index = InvertedIndex.load(inverted_index_filepath)
    for queries in query_list:
        document_ids = inverted_index.query(queries)
        answers = list(map(str, document_ids))
        print(','.join(answers))

def process_queries_from_files(inverted_index_filepath, query_file):
    """Process for query callback if query from file"""
    print(f"Read queries from {inverted_index_filepath}", file=sys.stderr)
    inverted_index = InvertedIndex.load(inverted_index_filepath)
    for query in query_file:
        query_words = query.strip().split()
        document_ids = inverted_index.query(query_words)
        answers = list(map(str, document_ids))
        print(','.join(answers))

def setup_parser(parser):
    """Function for setup the parser"""
    sub_parsers = parser.add_subparsers(help="choose command")

    build_parse = sub_parsers.add_parser(
        "build",
        help="Build index and save in binary into hard drive",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    build_parse.add_argument(
        "-d", "--dataset", dest="dataset_filepath",
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
        "-i", "--index", dest="inverted_index_filepath",
        help="Path to load inverted index, default path is %(default)s",
        metavar='INDEX', default=DEFAULT_INDEX_PATH,
    )
    query_parse.add_argument(
        "-q", "--query", dest="query",
        help="Query to run against inverted index",
        metavar='WORDS', required=False, nargs='+',
        action='append'
    )
    query_file_group = query_parse.add_mutually_exclusive_group(required=False)
    query_file_group.add_argument(
        "--query-file-cp1251", dest="query_file",
        type=EncodedFileType('r', encoding='cp1251'),
        default=TextIOWrapper(sys.stdin.buffer, encoding='cp1251'),
        help="""Query to run against inverted index from file \
                  with cp1251 encode""",
    )
    query_file_group.add_argument(
        "--query-file-utf8", dest="query_file",
        type=EncodedFileType('r', encoding='utf-8'),
        default=TextIOWrapper(sys.stdin.buffer, encoding='utf-8'),
        help="""Query to run against inverted index from file \
                with uft8 encode""",
    )
    query_parse.set_defaults(callback=query_callback)

def main():
    """Main function of the module"""
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