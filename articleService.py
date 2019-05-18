from flask import Flask, jsonify, request, make_response,g,Response
import sqlite3
import re
from passlib.hash import sha256_crypt
from flask_api import status
from flask_httpauth import HTTPBasicAuth
import datetime
from http import HTTPStatus
import datetime
from cassandra.cluster import Cluster

app = Flask(__name__)
auth = HTTPBasicAuth()

#microservice_database = 'article_database.db'

def get_database():
    cluster = Cluster(['172.17.0.2'])
    session = cluster.connect('article_database')
    return session

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.teardown_appcontext
def close_connection(exception):
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

@app.route("/postarticle", methods=['POST'])
#@auth.login_required
def post_article():
    if (request.method == 'POST'):
        if not request.json.get('articletitle'):
            return jsonify("You can not create blog without article title")
        elif not request.json.get('articlecontent'):
            return jsonify("You can not create blog without article content")
        else:
            article_details = request.get_json()
            username = request.authorization.username
            temp = str(article_details['articletitle'].replace(" ","%20"))
            temp = 'http://127.0.0.1:5000/retrieveArticle/'+temp
            try:
                db = get_database()
                #c = db.cursor()
                rows = db.execute("Select max(Id) as id from article_blog")

                for row in rows:
                    id = row.id

                if id is None:
                    id = 1
                else:
                    id = id + 1

                db.execute("""insert into article_blog (Id, content, title, author, url, createdDate, modifiedDate, flag)
                                values (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (id,article_details['articlecontent'],article_details['articletitle'], username,temp, str(datetime.datetime.now()), str(datetime.datetime.now()),'A'))
                #db.commit()
                response_message = Response(status=201, mimetype='application/json')
                response_message.headers['location'] = 'http://127.0.0.1:5000/retrieveArticle/' + article_details['articletitle']

            except sqlite3.Error as er:
                print(er)
                response_message = Response(status=409, mimetype='application/json')
        return response_message

@app.route('/retrieveArticle/<articletitle>', methods=['GET'])
def getarticle(articletitle):
    if (request.method == 'GET'):
        try:
            db = get_database()
            #db.row_factory = dict_factory
            #c = db.cursor()
            max_date_value = db.execute("select max(modifiedDate) as last from article_blog where flag = 'A' and title = %(title)s Allow Filtering", {'title': articletitle})

            max_date  = None
            for row in max_date_value:
                max_date = row.last

            if max_date_value is None:
                response_message = Response(status=404, mimetype='application/json')
                return response_message

            ifModifiedDate = request.headers.get('If-Modified-Since')

            # return ifModifiedSince

            if ifModifiedDate is not None:
                if str(ifModifiedDate) >= str(max_date):
                    response_message = Response(status=304, mimetype='application/json')
                    return response_message

            article = db.execute("select Id,title,content,url from article_blog where title=%(title)s and flag='A' ALLOW FILTERING",{'title':articletitle})
            #article = c.fetchone()
            if article is None:
                response_message = Response(status=404, mimetype='application/json')
            else:
                response_message = jsonify(list(article))
                response_message.headers['Last-Modified'] = max_date
                response_message.headers['Cache-Control'] = 'public, max-age=300'
                return response_message
        except sqlite3.Error as er:
            print(er)
            response_message = Response(status=409, mimetype='application/json')
    return response_message

@app.route("/editarticle", methods=['PATCH'])
#@auth.login_required
def editarticle():
    if (request.method == 'PATCH'):
        try:
            db = get_database()
            #c = db.cursor()
            article_details = request.get_json()
            rows = db.execute("select Id from article_blog where title = %(title)s and flag='A' ALLOW FILTERING",{'title':article_details['articletitle']})
            id = None
            for row in rows:
                id = row.id
            if id is None:
                return Response(status=404, mimetype='application/json')

            c = db.execute("update article_blog set content = %(content)s, modifieddate = %(updatetime)s where Id=%(id)s and flag='A'"
                ,{'content':article_details['articlecontent'],'updatetime':str(datetime.datetime.now()),'id':id,'username':request.authorization.username})
            #db.commit()

            response_message = Response(status=200, mimetype='application/json')

        except sqlite3.Error as er:
            print(er)
            response_message = Response(status=409, mimetype='application/json')
    return response_message

@app.route("/deletearticle", methods=['DELETE'])
#@auth.login_required
def delete_article():
    if (request.method == 'DELETE'):
        try:
            db = get_database()
            #c = db.cursor()
            article_details = request.get_json()

            articles = db.execute("select * from article_blog where title=%(title)s and author=%(username)s and flag='A' ALLOW FILTERING",{'username':request.authorization.username,'title':article_details['articletitle']})

            title = None
            id = None

            for row in articles:
                title = row.title
                id = row.id

            if title is None:
                response_message = Response(status=404, mimetype='application/json')
            else:
                db.execute("""delete from article_blog where flag='A' and Id=%(id)s""",{'id':int(id)})
            #db.commit()

            #if (c.rowcount == 1):
            #    response_message = Response(status=200, mimetype='application/json')
                response_message = Response(status=200, mimetype='application/json')
        except sqlite3.Error as er:
            print(er)
            response_message = Response(status=409, mimetype='application/json')

    return response_message

@app.route("/retrivenrecentarticle/<numberOfArcticles>", methods=['GET'])
def retrive_Recent_Article(numberOfArcticles):
    try:
        db = get_database()
        #db.row_factory = dict_factory
        #c = db.cursor()
        max_date_value = db.execute("select max(modifiedDate) as last from article_blog where flag = 'A' Allow Filtering")

        max_date  = None
        for row in max_date_value:
            max_date = row.last

        if max_date_value is None:
            response_message = Response(status=404, mimetype='application/json')
            return response_message

        ifModifiedDate = request.headers.get('If-Modified-Since')

        # return ifModifiedSince

        if ifModifiedDate is not None:
            if str(ifModifiedDate) >= str(max_date):
                response_message = Response(status=304, mimetype='application/json')
                return response_message
        articles = db.execute("select Id,title,content from article_blog where flag='A' LIMIT %(recentarticle)s", {'recentarticle':int(numberOfArcticles)})
        #recent_articles = c.fetchall()
        response_message = jsonify(list(articles))
        response_message.headers['Last-Modified'] = max_date
        response_message.headers['Cache-Control'] = 'public, max-age=300'

        #recent_articles_length = len(recent_articles)
        #return jsonify(recent_articles)

    except sqlite3.Error as er:
        print(er)
        response_message = Response(status=409, mimetype='application/json')

    return response_message

@app.route("/retrivemetadata/<numberOfArcticles>", methods=['GET'])
def retrive_Recent_meta_Article(numberOfArcticles):
    try:
        db = get_database()
        #db.row_factory = dict_factory
        #c = db.cursor()
        max_date_value = db.execute("select max(modifiedDate) as last from article_blog where flag = 'A' Allow Filtering")

        max_date  = None
        for row in max_date_value:
            max_date = row.last

        if max_date_value is None:
            response_message = Response(status=404, mimetype='application/json')
            return response_message

        ifModifiedDate = request.headers.get('If-Modified-Since')

        # return ifModifiedSince

        if ifModifiedDate is not None:
            if str(ifModifiedDate) >= str(max_date):
                response_message = Response(status=304, mimetype='application/json')
                return response_message
        articles = db.execute("select title, author, createdDate, modifiedDate, url from article_blog where flag = 'A' limit %(recentarticle)s", {"recentarticle":int(numberOfArcticles)})
        #recent_articles = c.fetchall()
        response_message = jsonify(list(articles))
        response_message.headers['Last-Modified'] = max_date
        response_message.headers['Cache-Control'] = 'public, max-age=300'
        return response_message
        #recent_articles_length = len(recent_articles)
        #return jsonify(recent_articles)

    except sqlite3.Error as er:
            print(er)
            response_message = Response(status=409, mimetype='application/json')

    return response_message


if __name__ == '__main__':
    app.run(debug=True)
