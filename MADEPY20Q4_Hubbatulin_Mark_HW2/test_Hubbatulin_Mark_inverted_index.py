from textwrap import dedent
from argparse import Namespace
import pytest
import logging

from task_Hubbatulin_Mark_inverted_index import (
        InvertedIndex, load_documents, EncodedFileType,
        build_inverted_index, query_callback,
        build_callback,
)
from storage_policy import JSONPolicy, StructPolicy

DATASET_BIG_FPATH = "../data/wikipedia_sample"
DATASET_SMALL_FPATH = "../data/small_wikipedia_sample"
DATASET_TINY_FPATH = "../data/tiny_wikipedia_sample"

DATASET_TINY_STR = dedent("""\
    123\tsame words A_word and nothing\n
    2\tsame words B_word in this dataset\n
    5\tfamous_phrases to be or not to be\n
    37\tall words such as A_word and B_word are here\n
""")

@pytest.fixture()
def tiny_dataset_fio(tmpdir):
    dataset_fio = tmpdir.join('tiny_dataset.txt')
    dataset_fio.write(DATASET_TINY_STR)
    return dataset_fio

def test_can_load_documents(tiny_dataset_fio):
    documents = load_documents(tiny_dataset_fio)
    expected_documents = {
        123: "same words A_word and nothing",
        2: "same words B_word in this dataset",
        5: "famous_phrases to be or not to be",
        37: "all words such as A_word and B_word are here",
    }
    assert expected_documents == documents, (
        "load_documents work incorrectly"
    )

@pytest.mark.parametrize(
    "filepath, document_len",
    [
        pytest.param(DATASET_TINY_FPATH, 4, id="tiny_wikipedia_documents"),
        pytest.param(DATASET_SMALL_FPATH, 34, id="small_wikipedia_documents"),
        pytest.param(DATASET_BIG_FPATH, 4100, id="big_wikipedia_documents", marks=[pytest.mark.slow]),
    ],
)

def test_can_load_right_len_document(filepath, document_len):
    documents = load_documents(filepath)
    assert len(documents) == document_len, (
        "load_documents work load incorrect len"
    )

@pytest.fixture()
def tiny_dataset_documents():
    documents = load_documents(DATASET_TINY_FPATH)
    return documents

@pytest.fixture()
def small_dataset_documents():
    documents = load_documents(DATASET_SMALL_FPATH)
    return documents

def test_encoded_file_type_repr():
    type_r = EncodedFileType('r')
    type_w = EncodedFileType('w')
    assert  "FileType('w')" != repr(type_r)
    assert  "FileType('r')" != repr(type_w)

def test_build_inverted_index_working_right(tiny_dataset_documents):
    test_inverted_index = build_inverted_index(tiny_dataset_documents)
    expected_documents = {
        'same': [123, 2],
        'and': [123, 37],
        'nothing': [123],
        'words': [123, 2, 37],
        'in': [2],
        'this': [2],
        'to': [5],
        'be': [5],
        'or': [5],
        'not': [5],
        'all': [37],
        'such': [37],
        'as': [37],
        'are': [37],
        'here': [37],
        'A_word': [123, 37],
        'B_word': [2, 37],
        'dataset': [2],
        'famous_phrases': [5],
    }
    assert test_inverted_index.term2doc == expected_documents, (
        "build_inverted_index build incorrect"
    )

@pytest.fixture()
def tiny_dataset_index(tiny_dataset_documents):
    index = build_inverted_index(tiny_dataset_documents)
    return index

@pytest.fixture()
def small_dataset_index(small_dataset_documents):
    index = build_inverted_index(small_dataset_documents)
    return index

@pytest.mark.parametrize(
    "query, expected_answer",
    [
        pytest.param(['A_word'], [123, 37], id="A_word"),
        pytest.param(['B_word'], [2, 37], id="B_word"),
        pytest.param(['A_word', 'B_word'], [37], id="A_word and B_word"),
        pytest.param(["word_does_not_exist"], [], id="word does not exist"),
    ],
)

def test_quety_inverted_index_intersect_result(tiny_dataset_index, query, expected_answer):
    answer = tiny_dataset_index.query(query)
    assert sorted(answer) == sorted(expected_answer), (
        f"Expected answer is {expected_answer}, but you get {answer}"
    )

def test_can_dump_and_load_inverted_index(tmpdir, small_dataset_index):
    index_fio = tmpdir.join('inverted.index')
    small_dataset_index.dump(index_fio)
    load_inverted_index = InvertedIndex.load(index_fio)
    assert small_dataset_index == load_inverted_index, (
        "load should return the same inverted index"
    )
    assert {} != load_inverted_index, (
        "load should return the same inverted index"
    )

QUERY_STR = dedent("""
    words
    such
    A_word B_word
    hard_rock
""")

@pytest.fixture()
def tiny_dataset_uft8_fio(tmpdir):
    dataset_fio = tmpdir.join('tiny_dataset.txt')
    dataset_fio.write(QUERY_STR.encode('utf-8'))
    return dataset_fio

@pytest.fixture()
def tiny_dataset_cp1251_fio(tmpdir):
    dataset_fio = tmpdir.join('tiny_dataset.txt')
    dataset_fio.write(QUERY_STR.encode('cp1251'))
    return dataset_fio

def test_process_build_does_process_build(tmpdir, caplog, capsys):
    with caplog.at_level("DEBUG"):
        index_fio = tmpdir.join('inverted.index')
        process_build_args = Namespace(
            dataset_filepath=DATASET_TINY_FPATH,
            inverted_index_filepath=index_fio,
            query_file=None,
            query=None,
        )
        build_callback(process_build_args)
        captured = capsys.readouterr()
        assert '' == captured.out
        assert '' == captured.err

        assert any("Building inverted index for provided documents" in message for message in caplog.messages), (
            "the is no 'Builind inverted index for provided documents' message in logs"
        )
        assert any("Loading documents from file" in message for message in caplog.messages), (
            "the is no 'Loading documents from file' message in logs"
        )
        assert all(record.levelno <= logging.WARNING for record in caplog.records),(
            "Application is unstable, there are WARNING+ logs message in logs"
        )

@pytest.mark.parametrize(
    "encoded",
    [
        pytest.param('utf8', id="utf8"),
        pytest.param('cp1251', id="cp1251"),
    ],
)

def test_process_query_does_process_query_from_correct_file(tmpdir, tiny_dataset_index, encoded, capsys, caplog):
    with caplog.at_level("DEBUG"):
        index_fio = tmpdir.join('inverted.index')
        tiny_dataset_index.dump(index_fio)

        dataset_fio = tmpdir.join('tiny_dataset.txt')
        dataset_fio.write(QUERY_STR.encode(encoded))

        with open(dataset_fio, encoding=encoded) as fin:
            process_queries_from_files = Namespace(
                inverted_index_filepath=index_fio,
                query_file=fin,
                query=None
            )
            query_callback(process_queries_from_files)
            captured = capsys.readouterr()
            assert '' == captured.err
            assert "123" and '2' and '37' in captured.out

            assert any("Read queries from" in message for message in caplog.messages), (
                "the is no 'Read queries from' message in logs"
            )
            assert any("Query inverted index with request" in message for message in caplog.messages), (
                "the is no 'Query inverted index with request' message in logs"
            )
            assert all(record.levelno <= logging.WARNING for record in caplog.records),(
                "Application is unstable, there are WARNING+ logs message in logs"
            )

def test_process_query_does_process_query_from_cli(tmpdir, tiny_dataset_index, tiny_dataset_uft8_fio, capsys, caplog):
    with caplog.at_level("DEBUG"):
        index_fio = tmpdir.join('inverted.index')
        tiny_dataset_index.dump(index_fio)
        with open(tiny_dataset_uft8_fio, encoding='utf8') as fin:
            process_querie_from_cli = Namespace(
                inverted_index_filepath=index_fio,
                query_file=None,
                query=[["words",]],
            )
            query_callback(process_querie_from_cli)
            captured = capsys.readouterr()
            assert '' == captured.err
            assert "123" and '2' and '37' in captured.out

            assert any("Read queries from CLI" in message for message in caplog.messages), (
                "the is no 'Read queries from CLI' message in logs"
            )
            assert any("Query inverted index with request" in message for message in caplog.messages), (
                "the is no 'Query inverted index with request' message in logs"
            )
            assert all(record.levelno <= logging.WARNING for record in caplog.records), (
                "Application is unstable, there are WARNING+ logs message in logs"
            )