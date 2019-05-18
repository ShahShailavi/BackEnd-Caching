from flask import Flask, jsonify, request, make_response,g,Response
import sqlite3
import re
from passlib.hash import sha256_crypt
from flask_api import status
from flask_httpauth import HTTPBasicAuth
import datetime
from http import HTTPStatus
import datetime
import requests
import cachecontrol

from rfeed import *

app = Flask(__name__)
auth = HTTPBasicAuth()

cache = cachecontrol.CacheControl(requests.Session())

@app.route("/summaryfeed", methods=['GET'])
def summary():
    article_summary = cache.get('http://localhost/retrivemetadata/100')
    articles = []

    if article_summary is not None:
        article_summary = article_summary.json()

    for article in article_summary:
        articles.append(Item(
            title = article['title'],
            author = article['author'],
            link = article['url'],
            date = article['createddate']
        ))

    feed = Feed(
        title = "Article Summary Feed",
        link = "www.article-summary-rss.com",
        description = "This is Article Summary which extract title, author, url, and created date",
        language = "en-US",
        items = articles
    )

    return feed.rss()

@app.route("/commentfeed", methods=['GET'])
def commentsummary():
    article_summary = cache.get('http://localhost/retrivenrecentarticle/100')
    articles = []

    if article_summary is not None:
        article_summary = article_summary.json()

    for article in article_summary:
        comment_array = []
        comments = cache.get('http://localhost/retrievearticle/'+article['title']+'/100')
        if comments is not None and comments.text != '':
            comments = comments.json()

        for comment in comments:
            comment_array.append(comment['comment'])

        articles.append(Item(
            title = article['title'],
            categories = comment_array
        ))

    feed = Feed(
        title = "Article-Comment Summary Feed",
        link = "www.article-comment-feed.com",
        description = "This will return all the comments which come under particular article.",
        language = "en-US",
        items = articles
    )

    return feed.rss()

@app.route('/metafeed', methods=['GET'])
# @basic_auth.required
def feed():
    # return "<h1> ***Article TEST API** </h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"

    r = cache.get('http://localhost/retrivenrecentarticle/100')

    items = []

    if r is not None:
        r = r.json()


    for article in r:

        # return article['title']

        comment_tags = cache.get("http://localhost/tag/gettag/"+ str(article['id']))


        if comment_tags is not None and comment_tags != '':
            comment_tags = comment_tags.json()

        tags = []
        for tag in comment_tags:
            if 'tagName' in tag:
                tags.append(tag['tagName'])

        comment_count = cache.get("http://localhost/comments/count/"+ str(article['title']))

        if comment_count == '':
            comment_count = "Number of comments for given article: 0"
        else:
            comment_count = comment_count.text

        items.append(Item(
            title = article['title'],
            description = comment_count,
            categories = tags
        ))

    feed = Feed(
        title = "RSS Feed",
        link = "http://www.example.com/rss",
        description = "Full RSS FEED containing Article, tags and comment count",
        language = "en-US",
        lastBuildDate = datetime.datetime.now(),
        items = items)

    return feed.rss()

app.run()
