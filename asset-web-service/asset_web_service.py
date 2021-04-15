#!/usr/bin/env python3
"""Asset web service

This web service is designed for parsing and calculating the profitability of assets
for this website of the central bank.
In the module, implement a class describing an Asset, a group of assets - CompositeAssets.
Methods for calculating profitability are implemented in these classes


This file can also be imported as a module and contains the following
functions:
* parse_cbr_currency_base_daily - Parsing currency indicators
* parse_cbr_key_indicators - Parsing key indicators

You can find out a more detailed api for the service in the terms of reference:)
"""
import logging.config
from typing import List
from bisect import bisect_left, insort_left

import yaml
import requests
from lxml import html
from flask import Flask, abort, request, jsonify

DEFAULT_ENCODING = "utf-8"
URL_CBR_DAILY = "https://www.cbr.ru/eng/currency_base/daily/"
URL_CBR_INDICATORS = "https://www.cbr.ru/eng/key-indicators/"
DEFAULT_LOGGING_CONF_FILEPATH = 'logging.conf.yml'


class Asset:
    """This class describes an Asset
    ----------
    Attributes

    char_code : str
        Asset product code
    name : str
        Asset name
    capital : float
        Cost of capital invested
    interest : float
        Percentage of profitability for the year

    Methods

    calculate_revenue(period: int, currency_rate: float)
        Calculate revenue of asset
    to_list()
        Return list of attributes
    """

    def __init__(self, char_code: str, name: str, capital: float, interest: float):
        self.char_code = char_code
        self.name = name
        self.capital = capital
        self.interest = interest

    def __lt__(self, other):
        return self.name < other.name

    def calculate_revenue(self, period: int, currency_rate: float) -> float:
        """Calculate revenue of asset
        This method calculates the investment profit of an asset
        for a specified period and a current rate
        :param
        ---------
        period : int
            The period for which you need to calculate the income
        currency_rate : float
            Current asset rating
        :return
        ---------
        float
            Revenue for the period
        """
        revenue_in_currency = self.capital * ((1.0 + self.interest) ** period - 1.0)
        revenue = revenue_in_currency * currency_rate
        return revenue

    def to_list(self) -> List:
        """Return list of asset attributes"""
        return [self.char_code, self.name, self.capital, self.interest]


class CompositeAssets:
    """This class describes an CompositeAssets
    The class contains several assets and manipulation with them
    ----------

    Methods

    add(Asset)
        Adding new asset in collection
    contain(Asset)
        Checks if an asset is in the collection
    get(name str)
        Return list of asset attributes by name
    clear()
        Clear assets collections
    calculate_revenue(period int, currency_rates dict)
        Calculate total revenue form all assets in collection
    """

    def __init__(self, _asset_collection=None):
        self._asset_collection = []
        if _asset_collection:
            for asset in _asset_collection:
                insort_left(self._asset_collection, asset)

    def __len__(self):
        return len(self._asset_collection)

    def add(self, asset: Asset):
        """Add an asset to the collection"""
        insort_left(self._asset_collection, asset)

    def contains(self, asset: Asset) -> bool:
        """Checks if an asset is in the collection"""
        index = bisect_left(self._asset_collection, asset)
        if (index != len(self)) and (self._asset_collection[index].name == asset.name):
            return True
        return False

    def get(self, name: str) -> List:
        """Get asset from collection by name"""
        asset = Asset("", name, 0, 0)
        index = bisect_left(self._asset_collection, asset)
        if (index != len(self)) and (self._asset_collection[index].name == asset.name):
            return self._asset_collection[index].to_list()
        return []

    def clear(self):
        """Clear all assets"""
        self._asset_collection = []

    def calculate_revenue(self, period: int, currency_rates: dict) -> float:
        """Calculate total revenue for all assets in the collection
        This method calculates the investment profit of all assets in collection
        for a specified period and a current rate.

        :param
        ---------
        period : int
            The period for which you need to calculate the income
        currency_rate : float
            Current asset rating
        :return
        ---------
        float
            Revenue for the period from all assets
        """
        total_revenue = 0
        for asset in self._asset_collection:
            revenue = asset.calculate_revenue(period, currency_rates[asset.char_code])
            total_revenue += revenue
        return total_revenue

    def to_list(self) -> list:
        """Convert the all assets in collection to list"""
        result = []
        for asset in self._asset_collection:
            insort_left(result, asset.to_list())
        return result


def parse_cbr_currency_base_daily(content: str):
    """This function for parsing daily currency rates from CBR site"""
    root = html.fromstring(content)
    table = root.xpath('//tr')[1:]

    result = {}
    for row in table:
        result[row[1].text] = float(row[4].text) / float(row[2].text)
    return result


def parse_cbr_key_indicators(content: str):
    """This function for parsing USD, EUR and precious metals rates from CBR site"""
    root = html.fromstring(content)
    tables = root.xpath('//table')[:2]

    result = {}
    for table in tables:
        for row in table[0][1:]:
            key = row.xpath('./td/div/div/text()')[1]
            value = float(row[-1].text.replace(',', ''))
            result[key] = value
    return result


def setup_logging(filepath=DEFAULT_LOGGING_CONF_FILEPATH):
    """Setup logging configurations from file"""
    with open(filepath) as config_fin:
        logging.config.dictConfig(yaml.safe_load(config_fin))


setup_logging()
app = Flask(__name__)
app.bank = CompositeAssets()


@app.errorhandler(404)
def route_not_found(error):
    """404 handler"""
    return "This route is not found", 404


@app.errorhandler(500)
def route_not_available(error):
    """503 handler"""
    return "CBR service is unavailable", 503


@app.route("/cbr/daily")
def get_daily():
    """Get daily currency rates in format {"char_code": rate}"""
    cbr_response = requests.get(URL_CBR_DAILY)
    if not cbr_response.ok:
        abort(503)

    result = parse_cbr_currency_base_daily(cbr_response.text)
    return result, 200


@app.route("/cbr/key_indicators")
def get_key_indicators():
    """Get USD, EUR and precious metals rates in format {"char_code": rate}"""
    cbr_response = requests.get(URL_CBR_INDICATORS)
    if not cbr_response.ok:
        abort(503)

    result = parse_cbr_key_indicators(cbr_response.text)
    return result, 200


@app.route("/api/asset/add/<string:char_code>/<string:name>/<string:capital>/<string:interest>")
def api_asset_add(char_code: str, name: str, capital: str, interest: str):
    """Add new asset to the bank"""
    capital, interest = float(capital), float(interest)
    asset = Asset(char_code=char_code, name=name, capital=capital, interest=interest)

    if app.bank.contains(asset):
        return f"Asset '{name}' already exists", 403

    app.bank.add(asset)
    return f"Asset '{name}' was successfully added", 200


@app.route("/api/asset/list")
def api_asset_list():
    """Get the list of assets in JSON format"""
    return jsonify(app.bank.to_list()), 200


@app.route("/api/asset/cleanup")
def api_asset_cleanup():
    """Clear all assets in the bank"""
    app.bank.clear()
    return "", 200


@app.route("/api/asset/get")
def api_asset_get():
    """Get assets with specified names from the bank in JSON format"""
    names = request.args.getlist("name")

    result = []
    for name in names:
        asset = app.bank.get(name)
        if asset:
            result.append(asset)

    return jsonify(sorted(result)), 200


@app.route("/api/asset/calculate_revenue")
def api_asset_calculate_revenue():
    """
    swagger_from_file: tmp.yml

    Calculate the estimated investment yield for the specified
    periods of time
    """
    periods = request.args.getlist("period")

    daily_response = requests.get(URL_CBR_DAILY)
    key_indicators_response = requests.get(URL_CBR_INDICATORS)
    currency_rates = parse_cbr_currency_base_daily(daily_response.text)
    currency_rates.update(parse_cbr_key_indicators(key_indicators_response.text))

    result = {}
    for period in periods:
        result[period] = app.bank.calculate_revenue(int(period), currency_rates)
    return result, 200


if __name__ == '__main__':
    app.run(debug=True)
