#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by bdsaglam on 14/10/2016, 23:29

import sys
import argparse
import re
import dateutil.parser
import cookielib
import urllib
import urllib2

from bs4 import BeautifulSoup


def make_soup(url):
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html, 'lxml')
    return soup


def parse_entry_date(s):
    regex = re.compile(r'\d*\.\d*\.\d*[ ]\d*:\d*')
    eslesme = regex.search(s)

    if eslesme:
        date_string = eslesme.group()
        date = dateutil.parser.parse(date_string)
    else:
        date = None

    return date


def get_page_count(page_url):
    try:
        soup = make_soup(page_url)
        pager = soup.find('div', 'pager')
        total_page = int(pager['data-pagecount'])
    except TypeError:
        total_page = 1
    return total_page


def scrape_topic(topic_url, page_limit=None):
    topic_root_url = topic_url.split('?')[0]

    page_count = get_page_count(topic_root_url)
    if page_limit is not None:
        page_count = min(page_count, page_limit)

    for i in range(1, page_count + 1):
        page_url = '{}{}{}'.format(topic_root_url, '?p=', i)
        soup = make_soup(page_url)
        entries = soup.find("ul", id="entry-list")

        for li in entries.findAll('li'):
            div_info = li.find('div', 'info')
            date_info = div_info.find('a', attrs={'class': 'entry-date'}).string
            date = parse_entry_date(date_info)

            author = li['data-author']
            entry = li.find('div', 'content').text
            yield {'date': date, 'author': author, 'entry': entry}


def get_token(page_url):
    soup = make_soup(page_url)
    entry = soup.find("input", {'name': '__RequestVerificationToken'})
    token = entry['value']
    return token


def login(username, password):
    # Store the cookies and create an opener that will hold them
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    # Add our headers
    opener.addheaders = [('User-agent', 'EksiTesting')]

    # Install our opener (note that this changes the global opener to the one
    # we just made, but you can also just call opener.open() if you want)
    urllib2.install_opener(opener)

    # The action/ target from the form
    authentication_url = 'https://eksisozluk.com/giris'

    # Input parameters we are going to send
    loginData = {
        '__RequestVerificationToken': get_token(authentication_url),
        'ReturnUrl': 'https://eksisozluk.com/',
        'UserName': username,
        'Password': password,
        'RememberMe': 'false'}

    # Use urllib to encode the payload
    data = urllib.urlencode(loginData)

    # Build our Request object (supplying 'data' makes it a POST)
    req = urllib2.Request(authentication_url, data)

    # Make the request and read the response
    resp = urllib2.urlopen(req)
    contents = resp.read()
    return resp, contents


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('thread_url', help='the url of page', type=str)
    parser.add_argument('-o', '--output2csv', help='output csv file', type=str)
    parser.add_argument('-p', '--page', help='max number of pages', type=int)

    args = parser.parse_args(sys.argv[1:])

    result = list(scrape_topic(args.thread_url, args.page))

    if args.output2csv:
        import pandas as pd

        df = pd.DataFrame(result)
        df.to_csv(args.output2csv, encoding='utf-8', index=False)
    else:
        print result
