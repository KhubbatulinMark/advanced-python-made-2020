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
import struct
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType, ArgumentError
from io import TextIOWrapper
from collections import defaultdict
from typing import List

DEFAULT_DATASET_PATH = "wikipedia_sample"
DEFAULT_INDEX_PATH = "inverted.index"

class EncodedFileType(FileType):

    def __call__(self, string):
        if string == '-':
            if 'r' in self._mode:
                return sys.stdin



class InvertedIndex:
    """This class describes an Inverted Index
    ----------
	Attributes
	----------
	term2doc : dict
		Dictionary: [term] = [document`s id list]

	Methods
	-------
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

    def dump(self, filepath: str) -> None:
        """Save index to disk function

        :param
        ---------
        filepath : str
            The path where the index is saved
        """
        print(f"Dump inverted index to {filepath}", file=sys.stderr)
        with open(filepath, 'wb') as file:
            count = struct.pack('>i', len(self.term2doc))
            file.write(count)
            for key in self.term2doc:
                key_encoded = key.encode('utf-8')
                key_len = len(key_encoded)
                key_len_bin = struct.pack('>h', key_len)
                file.write(key_len_bin)

                format_str = '>' + str(key_len) + 's'
                key_str_bin = struct.pack(format_str, key_encoded)
                file.write(key_str_bin)

                doc_len = len(self.term2doc[key])
                doc_len_bin = struct.pack('>h', doc_len)
                file.write(doc_len_bin)

                for doc_id in self.term2doc[key]:
                    doc_id_bin = struct.pack('>h', doc_id)
                    file.write(doc_id_bin)

    @classmethod
    def load(cls, filepath: str) -> object:
        """This class method allows you to load an index from a file.
        Once loadedm it will return an inverted index class object.

        :param
        ---------
        filepath : str
            Inverted index file path
        :return
        ---------
        dict
            Dictionary type - key: document id, value: list of words in this document
        """
        print(f"Loading inverted index from {filepath}", file=sys.stderr)
        index = InvertedIndex()
        with open(filepath, 'rb') as file:
            count_bin = file.read(4)
            count = struct.unpack('>i', count_bin)[0]
            index.term2doc = defaultdict(list)
            for _ in range(count):
                key_len_pack = file.read(2)
                key_len = struct.unpack('>h', key_len_pack)[0]

                format_str = '>' + str(key_len) + 's'
                decoding_str = file.read(key_len)
                bin_str = struct.unpack(format_str, decoding_str)[0]
                key = bin_str.decode('utf-8')

                index_len_pack = file.read(2)
                index_len = struct.unpack('>h', index_len_pack)[0]

                decoding_list = file.read(2 * index_len)
                format_int = '>' + str(index_len) + 'h'
                doc_id_list = list(struct.unpack(format_int, decoding_list))
                index.term2doc[key] = doc_id_list

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
        content = line.split('\t')
        documents[int(content[0])] = ''.join(content[1:]).strip()
    return documents

def build_callback(arguments):
    """Callback for building inverted index"""
    dataset_path = (arguments.dataset)
    documents = load_documents(dataset_path)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(arguments.index)

def query_callback(arguments):
    """Сallback for queries to the invested index"""
    for query in arguments.query_file:

    inverted_index = InvertedIndex.load(arguments.input)
    document_ids = inverted_index.query(arguments.query)
    print(*document_ids)

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
        "-o", "--output", dest="index",
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
        "-i", "--input", dest="input",
        help="Path to load inverted index, default path is %(default)s",
        metavar='INDEX', default=DEFAULT_INDEX_PATH,
    )
    query_parse.add_argument(
        "-q", "--query", dest="query",
        help="Query to run against inverted index",
        metavar='WORDS', required=False, nargs="+",
    )
    query_file_group = query_parse.add_mutually_exclusive_group(required=True)
    query_file_group.add_argument(
        "--query-file-utf8", dest="query_file", type=FileType('r', encoding='utf-8'),
        default=TextIOWrapper(sys.stdin.buffer, encoding='utf-8'),
        help="""Query to run against inverted index from file 
                with uft8 encode""", required=False,
    )
    query_file_group.add_argument(
        "--query-file-cp1251", dest="query_file", type=FileType('r', encoding='cp1251'),
        default=TextIOWrapper(sys.stdin.buffer, encoding='cp1251'),
        help="""Query to run against inverted index from file 
                  with cp1251 encode""",
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
