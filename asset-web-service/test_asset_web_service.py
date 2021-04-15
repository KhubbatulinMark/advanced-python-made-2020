import json
from json import JSONDecodeError
from contextlib import nullcontext as do_not_raise_exception
from collections import namedtuple
from unittest.mock import patch, MagicMock

import pytest
import requests
from requests import exceptions

from asset_web_service import (
    app,
    parse_cbr_currency_base_daily,
    parse_cbr_key_indicators,
    Asset,
    CompositeAssets,
    URL_CBR_DAILY,
    URL_CBR_INDICATORS,
    DEFAULT_ENCODING,
)

DEFAULT_STATUS_CODE = 200
DEFAULT_ENCODING = "utf-8"

CBR_DAILY_RESPONSE_FILEPATH = "cbr_currency_base_daily_sample.html"
CBR_INDICATORS_RESPONSE_FILEPATH = "cbr_key_indicators_sample.html"
URL_UNKNOWN = "https://it-should-not-exist.com"

# -------------------------------------------------   TESTS FOR ASSET   -----------------------------------------


def test_asset_create():
    asset = Asset("USD", "dollar", 1, 0.04)

    assert asset.name == "dollar", "Asset create wrong!"
    assert asset.capital == 1, "Asset create wrong!"
    assert asset.interest == 0.04, "Asset create wrong!"


@pytest.mark.parametrize(
    "period, rate, expected_result",
    [
        pytest.param(1, 74.5, 298),
        pytest.param(3, 75.0, 936.48),
        pytest.param(7, 73.12, 2310.09316977),
    ]
)
def test_can_calculate_asset_revenue_correctly(period, rate, expected_result):
    asset = Asset("USD", "dollar", 100, 0.04)
    result = asset.calculate_revenue(period, rate)
    assert f"{expected_result:.8f}" == f"{result:.8f}", (
        f"Wrong revenue value: expected {expected_result:.8f}, got {result:.8f}"
    )


@pytest.mark.parametrize(
    "left_asset, right_asset, expected_result",
    [
        pytest.param(Asset("USD", "dollar", 73.4, 0.045), Asset("EUR", "euro", 73.73, 0.04), True),
        pytest.param(Asset("EUR", "euro", 83, 0.045), Asset("USD", "euro", 82, 0.04), False),
    ]
)
def test_can_compare_assets_correctly(left_asset, right_asset, expected_result):
    result = left_asset < right_asset
    assert result is expected_result, (
        f"Wrong comparison: expected {expected_result} for assets with names \
        {left_asset.name} and {right_asset.name}, got {result}"
    )

# -------------------------------------------------   TESTS FOR COMPOSITE   -----------------------------------------


@pytest.mark.parametrize(
    "assets, expected_result",
    [
        pytest.param([Asset("EUR", "euro", 82, 0.03), Asset("USD", "dollar", 73, 0.04)], 2, id='List of Assets'),
        pytest.param(None, 0, id='None'),
    ]
)
def test_composite_create(assets, expected_result):
    composite = CompositeAssets(assets)
    result = len(composite.to_list())
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


@pytest.fixture()
def small_composite():
    asset_1 = Asset("EUR", "euro", 82, 0.03)
    asset_2 = Asset("USD", "dollar", 73, 0.04)
    composite = CompositeAssets([asset_1, asset_2])
    return composite


def test_bank_to_list_is_sorted_and_works_correctly(small_composite):
    expected_result = [
        ["EUR", "euro", 82, 0.03],
        ["USD", "dollar", 73, 0.04]
    ]
    result = small_composite.to_list()
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


def test_can_add_assets_to_composite(small_composite):
    asset = Asset("GBP", "pound", 102, 0.02)
    small_composite.add(asset)
    result = [x.name for x in small_composite._asset_collection]
    expected_result = sorted(["euro", "dollar", "pound"])
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


@pytest.mark.parametrize(
    "asset, expected_result",
    [
        pytest.param(Asset("EUR", "euro", 82, 0.03), True, id='Fully contained'),
        pytest.param(Asset("USD", "dollar", 72, 0.04), True, id='Contained with changes'),
        pytest.param(Asset("GBP", "pound", 102, 0.02), False, id='Not contained'),
    ]
)
def test_composite_contains_works_correctly(asset, expected_result, small_composite):
    result = small_composite.contains(asset)
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


def test_composite_clear_works_correctly(small_composite):
    small_composite.clear()
    assert len(small_composite.to_list()) == 0, (
        f"Wrong result: expected 0, got {len(small_composite.to_list())}"
    )


def test_composite_get_works_correctly(small_composite):
    result = small_composite.get("dollar")
    expected_result = ["USD", "dollar", 73, 0.04]
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )


def test_bank_calculate_revenue_works_correctly():
    assets = [
        Asset("EUR", "euro", 82, 0.03),
        Asset("USD", "dollar", 72, 0.04),
        Asset("GBP", "pound", 102, 0.02),
    ]
    key_indicators = {
        "EUR": 83.6,
        "USD": 74.3,
    }
    currency_rates = {
        "GBP": 0.342,
    }
    currency_rates.update(key_indicators)
    assert 3 == len(currency_rates)
    period = 4
    expected_result = sum(
        asset.calculate_revenue(period, currency_rates[asset.char_code])
        for asset in assets
    )
    composite = CompositeAssets(assets)
    result = composite.calculate_revenue(period, currency_rates)
    assert expected_result == result, (
        f"Wrong result: expected {expected_result}, got {result}"
    )

# -------------------------------------------------   TESTS FOR PARSING   -----------------------------------------


def test_parse_cbr_currency_base_daily_works_correctly():
    expected_result = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "TRY": 9.87607
    }
    with open(CBR_DAILY_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        content = fin.read()
    result = parse_cbr_currency_base_daily(content)
    for key in expected_result:
        assert key in result, (
            f"Wrong result: key {key} is absent from result {result}"
        )
        assert result[key] == expected_result[key], (
            f"Wrong result: expected {expected_result[key]}, got {result[key]}"
        )
    assert len(result) == 34, (
        f"Wrong result len: expected {34}, got {len(result)}"
    )


def test_parse_cbr_key_indicators_works_correctly():
    expected_result = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14,
    }
    with open(CBR_INDICATORS_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        content = fin.read()
    result = parse_cbr_key_indicators(content)
    for key in expected_result:
        assert key in result, (
            f"Wrong result: key {key} is absent from result {result}"
        )
        assert result[key] == expected_result[key], (
            f"Wrong result: expected {expected_result[key]}, got {result[key]}"
        )

# -------------------------------------------------   TESTS WITH MOCKs   -----------------------------------------


@pytest.mark.parametrize(
    "target_url, expected_outcome",
    [
        pytest.param(URL_CBR_DAILY, True, id=f"Request from {URL_CBR_DAILY}"),
        pytest.param(URL_CBR_INDICATORS, True, id=f"Request from {URL_CBR_INDICATORS}"),
    ]
)
def test_http_request_is_successful(target_url, expected_outcome):
    response = requests.get(target_url)
    assert expected_outcome == bool(response)


def build_response_mock_from_content(content, encoding=DEFAULT_ENCODING, status_code=DEFAULT_STATUS_CODE):
    text = content.decode(encoding)
    response = MagicMock(
        content=content,
        encoding=encoding,
        text=text,
        status_code=status_code,
    )
    response.json.side_effect = lambda: json.loads(text)
    return response


def callback_requests_get(url):
    url_mapping = {
        URL_CBR_DAILY: CBR_DAILY_RESPONSE_FILEPATH,
        URL_CBR_INDICATORS: CBR_INDICATORS_RESPONSE_FILEPATH,
    }
    if url in url_mapping:
        mock_content_filepath = url_mapping[url]
        with open(mock_content_filepath, "rb") as content_fin:
            content = content_fin.read()
        mock_response = build_response_mock_from_content(content=content)
        return mock_response

    raise exceptions.ConnectionError(f"Exceeded max trial connection to {url}")


@patch("requests.get")
@pytest.mark.parametrize(
    "target_url, expectation",
    [
        pytest.param(URL_CBR_DAILY, pytest.raises(JSONDecodeError), id=f"raise-JSONDecodeError from {URL_CBR_DAILY}"),
        pytest.param(URL_CBR_INDICATORS, pytest.raises(JSONDecodeError), id=f"raise-JSONDecodeError from "
                                                                            f"{URL_CBR_INDICATORS}"),
        pytest.param(URL_UNKNOWN, pytest.raises(exceptions.ConnectionError), id="raise-ConnectionError"),
    ]
)
def test_can_mock_web(mock_requests_get, target_url, expectation):
    mock_requests_get.side_effect = callback_requests_get
    with expectation:
        response = requests.get(target_url)
        assert response.status_code == 200
        assert "Bank" in response.text
        assert isinstance(response.json(), dict)


# --------------------------------------------------- TESTS FOR WEB PART  -------------------------------------------


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_service_does_not_reply_to_nonexistent_path(client):
    expected_message = "This route is not found"
    response = client.get("/")
    status_code = response.status_code
    message = response.data.decode(encoding=DEFAULT_ENCODING)

    assert expected_message == message, (
        f"Wrong message: expected {expected_message}, got {message}"
    )
    assert 404 == status_code, (
        f"Wrong status code: expected 404, got {status_code}"
    )


@patch("requests.get")
def test_cbr_daily_page_unavailable(mock, client):
    mock.return_value.status_code = 503
    result = client.get("/cbr/daily", follow_redirects=True)

    expected_message = "CBR service is unavailable"
    message = result.data.decode(encoding=DEFAULT_ENCODING)

    assert mock.called_once(URL_CBR_DAILY)
    assert 503 == result.status_code, (
        f"Wrong status code: expected 503, got {result.status_code}"
    )
    assert expected_message == message, (
        f"Wrong message: expected {expected_message}, got {message}"
    )


@pytest.mark.parametrize(
    "route, name, length",
    [
        pytest.param("/api/asset/add/USD/dollar/12/0.04", 'dollar', 1),
        pytest.param("/api/asset/add/EUR/euro/10/0.035", 'euro', 2),
    ]
)
def test_api_add_asset_works_correctly(route, name, length, client):
    response = client.get(route, follow_redirects=True)

    expected_message = f"Asset '{name}' was successfully added"
    message = response.data.decode(encoding=DEFAULT_ENCODING)

    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert expected_message == message, (
        f"Wrong message: expected {expected_message}, got {message}"
    )
    assert len(client.application.bank.to_list()) == length, (
        f"Wrong length of collection: expected {length}, got {len(client.application.bank.to_list())}"
    )


def test_api_asset_cleanup_works_correctly(client):
    client.get("/api/asset/add/USD/dollar/12/0.04", follow_redirects=True)
    client.get("/api/asset/add/EUR/euro/10/0.035", follow_redirects=True)
    response = client.get("/api/asset/cleanup", follow_redirects=True)

    message = response.data.decode(encoding=DEFAULT_ENCODING)
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert "" == message, (
        f"Wrong message: expected empty message, got {message}"
    )
    length = len(client.application.bank.to_list())
    assert 0 == length, (
        f"Cleanup failed: expected size of 0, got {length}"
    )


@pytest.fixture()
def medium_composite():
    asset_1 = Asset("EUR", "euro", 82, 0.03)
    asset_2 = Asset("USD", "dollar", 73, 0.04)
    asset_3 = Asset("GBP", "pound", 102, 0.02)
    composite = CompositeAssets([asset_1, asset_2, asset_3])
    return composite


def test_api_asset_list_works_correctly(client, medium_composite):
    client.application.bank = medium_composite
    expected_result = medium_composite.to_list()

    response = client.get("/api/asset/list", follow_redirects=True)
    assert response.status_code == 200, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert response.json == expected_result, (
        f"Wrong result: expected {expected_result}, got {response.json}"
    )


@pytest.mark.parametrize(
    "route, expected_result",
    [

        pytest.param(
            "/api/asset/get?name=euro",
            [
                ["EUR", "euro", 82, 0.03],
            ], id="One asset"
        ),
        pytest.param(
            "/api/asset/get?name=euro&name=dollar",
            [
                ["EUR", "euro", 82, 0.03],
                ["USD", "dollar", 73, 0.04],
            ], id="Two assets"
        ),
        pytest.param(
            "/api/asset/get?name=euro&name=dollar&name=pound",
            [
                ["EUR", "euro", 82, 0.03],
                ["GBP", "pound", 102, 0.02],
                ["USD", "dollar", 73, 0.04],
            ], id="Three assets with withdrawal order"
        ),
    ]
)
def test_api_asset_get_works_correctly(medium_composite, route, expected_result, client):
    client.application.bank = medium_composite
    response = client.get(route)
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
    assert expected_result == response.json, (
        f"Wrong result: expected {expected_result}, got {response.json}"
    )


@patch("requests.get")
@pytest.mark.parametrize(
    "route, periods",
    [
        pytest.param("/api/asset/calculate_revenue?period=2", ["2"]),
        pytest.param("/api/asset/calculate_revenue?period=3&period=7", ["3", "7"]),
    ]
)
def test_api_calculate_revenue_works_correctly(mock, medium_composite, route, periods, client):

    side_effect = []
    namespace = namedtuple("return_value", ["text", "status_code"])
    with open(CBR_DAILY_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        side_effect.append(namespace(fin.read(), 200))
    with open(CBR_INDICATORS_RESPONSE_FILEPATH, "r", encoding=DEFAULT_ENCODING) as fin:
        side_effect.append(namespace(fin.read(), 200))
    mock.side_effect = side_effect
    currency_rates = {
        "CHF": 84.8882,
        "JPY": 72.9265,
        "UAH": 26.5297,
        "GBP": 101.1955,
    }
    key_indicators = {
        "USD": 75.4571,
        "EUR": 91.9822,
        "Au": 4529.59,
        "Ag": 62.52,
        "Pt": 2459.96,
        "Pd": 5667.14,
    }
    currency_rates.update(key_indicators)
    client.application.bank = medium_composite
    expected_result = {}
    for period in periods:
        expected_result[period] = \
            client.application.bank.calculate_revenue(int(period), currency_rates)
    response = client.get(route)
    assert mock.called_once(URL_CBR_DAILY)
    assert mock.called_once(URL_CBR_INDICATORS)
    assert expected_result == response.json, (
        f"Wrong result: expected {expected_result}, got {response.json}"
    )
    assert 200 == response.status_code, (
        f"Wrong status code: expected 200, got {response.status_code}"
    )
