#!/usr/bin/env python3
from textwrap import dedent
from argparse import Namespace
from collections import defaultdict
import pytest

from stackoverflow_analytics import (
    load_dataset, process_build, process_queries, build_analitycs,
    stackoverflow_callback
)

DATASET_SMALL_FPATH = "data/stackoverflow_posts_small.xml"
DATASET_TINY_FPATH = "data/stackoverflow_posts_tiny.xml"

STOPWORDS_FPATH = "data/stop_words_en.txt"
DEFAULT_QUIRIES_1 = "data/query_sample_1.csv"
DEFAULT_QUIRIES_2 = "data/query_sample_2.csv"


def test_can_load_dataset_v1():
    dataset = load_dataset(DATASET_TINY_FPATH)
    expected_documents = [
        {
            'year': 2019,
            'score': 10,
            'title': "Is SEO better better better done with repetition?"
        },
        {
            'year': 2019,
            'score': 5,
            'title': "What is SEO?"
        },
        {
            'year': 2020,
            'score': 20,
            'title': "Is Python better than Javascript?"
        },
    ]
    assert expected_documents == dataset, (
        "load_documents work incorrectly"
    )


def test_can_load_dataset_with_correct_len():
    dataset = load_dataset(DATASET_TINY_FPATH)
    assert len(dataset) == 3, (
        "load_documents work incorrectly"
    )


@pytest.fixture()
def tiny_dataset():
    dataset = load_dataset(DATASET_TINY_FPATH)
    return dataset


@pytest.fixture()
def small_dataset():
    dataset = load_dataset(DATASET_SMALL_FPATH)
    return dataset


def test_process_queries_does_working():
    queries = process_queries(DEFAULT_QUIRIES_1)
    expected_queries = [
        {'start_year': 2019, 'end_year': 2019, 'top_N': 2},
        {'start_year': 2019, 'end_year': 2020, 'top_N': 4},
    ]
    assert queries == expected_queries, (
        "process_queries work incorrectly"
    )


@pytest.mark.parametrize(
    "dataset_filepath",
    [
        pytest.param(DATASET_TINY_FPATH, id="tiny_dataset"),
        pytest.param(DATASET_SMALL_FPATH, id="small_dataset"),
    ],
)


def test_process_build_does_process_build(dataset_filepath, caplog, capsys):
    with caplog.at_level("INFO"):
        process_build(dataset_filepath, STOPWORDS_FPATH)
        captured = capsys.readouterr()
        assert '' == captured.out
        assert '' == captured.err

        assert any("process XML dataset" in message for message in caplog.messages), (
            "The is no 'process XML dataset' message in logs"
        )
        assert any("ready to serve queries" in message for message in caplog.messages), (
            "The is no 'ready to serve queries' message in logs"
        )


def test_build_analitycs(tiny_dataset):
    analitic = build_analitycs(tiny_dataset, STOPWORDS_FPATH)
    expected_analityc = {
        'better': [(2019, 10), (2020, 20)],
        'repetition': [(2019, 10)],
        'seo': [(2019, 10), (2019, 5)],
        'python': [(2020, 20)],
        'javascript': [(2020, 20)]
    }
    assert analitic == expected_analityc, (
        "build_analitycs work incorrectly"
    )


@pytest.fixture()
def tiny_dataset_analytic(tiny_dataset):
    analitic = build_analitycs(tiny_dataset, STOPWORDS_FPATH)
    return analitic


def test_answer_on_queryes_v1(tiny_dataset_analytic, caplog, capsys):
    with caplog.at_level("DEBUG"):
        ans = tiny_dataset_analytic.query(2019, 2019, 2)
        expected_ans = {
            'start': 2019,
            'end': 2019,
            'top': [['seo', 15], ['better', 10]]
        }
        assert ans == expected_ans, (
            "query work incorrectly"
        )
        captured = capsys.readouterr()
        assert '' == captured.out
        assert '' == captured.err

        assert any('got query "2019,2019,2"' in message for message in caplog.messages), (
            "The is no 'got query' message in logs"
        )


def test_answer_on_queryes_v2(tiny_dataset_analytic, caplog, capsys):
    with caplog.at_level("DEBUG"):
        ans = tiny_dataset_analytic.query(2019, 2020, 4)
        expected_ans = {
            "start": 2019,
            "end": 2020,
            "top": [["better", 30], ["javascript", 20],
            ["python", 20], ["seo", 15]]
        }
        assert ans == expected_ans, (
            "query work incorrectly"
        )
        captured = capsys.readouterr()
        assert '' == captured.out
        assert '' == captured.err

        assert any('got query "2019,2020,4"' in message for message in caplog.messages), (
            "The is no 'got query' message in logs"
        )


def test_answer_on_queryes_v3(tiny_dataset_analytic, caplog, capsys):
    with caplog.at_level("DEBUG"):
        ans = tiny_dataset_analytic.query(2021, 2022, 4)
        expected_ans = {
            "start": 2021,
            "end": 2022,
            "top": []
        }
        assert ans == expected_ans, (
            "query work incorrectly"
        )
        captured = capsys.readouterr()
        assert '' == captured.out
        assert '' == captured.err

        assert any('got query "2021,2022,4"' in message for message in caplog.messages), (
            "The is no 'got query' message in logs"
        )
        assert any('not enough data to answer, found 0 words out of 4 for period "2021,2022"' in message for message in caplog.messages), (
                "The is no 'not enough data to answer' message in logs"
        )


def test_stackoverflow_callback(caplog, capsys):
    with caplog.at_level("DEBUG"):
        process_queries = Namespace(
            dataset_filepath=DATASET_TINY_FPATH,
            stopwords_filepath=STOPWORDS_FPATH,
            queries=DEFAULT_QUIRIES_2,
        )
        stackoverflow_callback(process_queries)
        captured = capsys.readouterr()

        assert any('process XML dataset' in message for message in caplog.messages), (
            "The is no 'process XML dataset' message in logs"
        )
        assert any('ready to serve queries' in message for message in caplog.messages), (
            "The is no 'ready to serve queries' message in logs"
        )
        assert any('got query "2008,2009,2"' in message for message in caplog.messages), (
            "The is no 'got query' message in logs"
        )
        assert any('not enough data to answer, found 0 words out of 2 for period "2008,2009"' in message for message in
                   caplog.messages), (
            "The is no 'not enough data to answer' message in logs"
        )
        assert any('finish processing queries' in message for message in
                   caplog.messages), (
            "The is no 'finish processing queries' message in logs"
        )
