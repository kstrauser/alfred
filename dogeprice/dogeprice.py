#!/usr/bin/env python
# -*- coding: utf-8 -*- for the love of Doge

# Copyright (c) 2014, Kirk Strauser
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import json
import logging
import os
import sys
import time
import urllib2

CACHE_TIME = 60
CACHE_FILE = '/tmp/dogemonitor_ticker.json'
DEFAULT_CURRENCY = 'usd'
TICKER_URL = 'http://dogemonitor.com/ticker.php'

MODULELOG = logging.getLogger(__name__)


def get_cached_file():
    """Open and return a cache file, if one exists and is recent enough."""
    try:
        mtime = os.stat(CACHE_FILE).st_mtime
    except OSError as exc:
        MODULELOG.debug('Unable to stat %s: %s', CACHE_FILE, exc.strerror)
        return None

    age = time.time() - mtime

    if age > CACHE_TIME:
        MODULELOG.debug('%s is too old (%.1f seconds, %.1f max)',
                        CACHE_FILE, age, CACHE_TIME)
        return None

    return open(CACHE_FILE)


def get_recent_rates():
    """Return a rates dict fetched from cache or from a URL."""
    cached_file = get_cached_file()
    if cached_file:
        return json.load(cached_file)

    MODULELOG.debug('Fetching %s', TICKER_URL)
    currency_feed = urllib2.urlopen(TICKER_URL).read()

    with open(CACHE_FILE, 'w') as outfile:
        outfile.write(currency_feed)

    return json.loads(currency_feed)


def format_money(amount, currency):
    """Make monetary amounts look pretty.

    This is sort of in the standard library in `locale`, but yeah.

    """
    try:
        money_format = {
            'eur': '€ %(amount).2f',
            'gbp': '£%(amount).2f',
            'pln': '%(amount).2f zł',
            'usd': '$%(amount).2f',
            'xdg': 'Ɖ%(amount).3f',
        }[currency]
    except KeyError:
        money_format = '%(amount).f %(currency)s'

    return money_format % {
        'amount': amount,
        'currency': currency.upper(),
    }


def rates_to_text(rates, currency, dogecoin_amount):
    """Return a string describing the requested conversion."""
    average_bitcoins_per_dogecoin = (
        sum(float(_['price']) for _ in rates['tickers']) /
        len(rates['tickers'])
    )

    currency_per_dogecoin = (average_bitcoins_per_dogecoin *
                             rates['currencies'][currency])

    if dogecoin_amount is None:
        return '%s per %s' % (
            format_money(1 / currency_per_dogecoin, 'xdg'),
            format_money(1, currency),
        )
    else:
        return '%s is %s' % (
            format_money(dogecoin_amount, 'xdg'),
            format_money(dogecoin_amount * currency_per_dogecoin, currency),
        )


def handle_command_line():
    """Do the right thing with the command line (or Alfred query)."""
    # Running inside Alfred?
    args = '{query}'
    if args != '{' + 'query' + '}':
        args = args.split()
    else:
        args = sys.argv[1:]

    try:
        currency = args[1]
    except IndexError:
        currency = DEFAULT_CURRENCY

    try:
        dogecoin_amount = float(args[0])
    except (IndexError, ValueError):
        dogecoin_amount = None

    rates = get_recent_rates()
    print(rates_to_text(rates, currency, dogecoin_amount))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    handle_command_line()
