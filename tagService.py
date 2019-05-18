from flask import Flask, jsonify, request, make_response,g,Response
import sqlite3
import re
from passlib.hash import sha256_crypt
from flask_api import status
from flask_httpauth import HTTPBasicAuth
import datetime
from http import HTTPStatus
from cassandra.cluster import Cluster

app = Flask(__name__)
auth = HTTPBasicAuth()

#tag_database = 'tag_database.db'
#article_database='article_database.db'

def get_database():
    cluster = Cluster(['172.17.0.2'])
    session = cluster.connect('article_database')
    return session

@app.teardown_appcontext
def close_connection(exception):
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# To add new article with tag or to add new tags for existing article
@app.route("/tag/addtag", methods=['POST'])
def addTags():
    if (request.method == 'POST'):
        db = get_database()
        details = request.get_json()
        existing_tag=[]
        author = request.authorization.username
        #to get id for new entry in table
        rows = db.execute("Select max(id) as id from article_blog")
        for row in rows:
            id = row.id

        try:
            tag_Details=details['tag'].split(',')
            articleId=request.json.get('articleId')
            if (not request.json.get('articleId')):
                if not request.json.get('articletitle'):
                    return jsonify("You can not create blog without article title")
                elif not request.json.get('articlecontent'):
                    return jsonify("You can not create blog without article content")
                temp = str(details['articletitle'].replace(" ", "%20"))
                temp = 'http://127.0.0.1:5000/retrieveArticle/' + temp
                #to get id for new entry in database
                if id is None:
                    id = 1
                else:
                    id = id + 1

                db.execute("""insert into article(id, title, content, author, createdDate, modifiedDate, URL,flag) values (%s,%s,%s,%s,%s,%s,%s)""",{int(id),details['articletitle'], details['articlecontent'], request.authorization.username,str(datetime.datetime.now()), str(datetime.datetime.now()), temp,'A'})
                articleId=id
            else:
            #add condition to check if article exists

                rec=db.execute("""SELECT article_id from article_blog WHERE id=%(articleid)s and flag='A' allow filtering""", {'articleid':int(articleId)})

                if not rec:
                    response = Response(status=404, mimetype='application/json')
                    return response


                rec=db.execute("""SELECT tag from article_blog WHERE article_id=%(articleid)s and flag='T' allow filtering""", {'articleid':int(articleId)})
                for row in rec:
                    existing_tag.append(row)

            for tags in tag_Details:
                tag=tags.strip()

                if tag not in existing_tag:
                    if id is None:
                        id = 1
                    else:
                        id = id + 1
                    db.execute("""insert into article_blog(id,author,createdDate, modifiedDate,flag,article_id,tag) values (%(id)s,%(author)s,%(ct)s,%(ut)s,%(cf)s,%(aid)s,%(tag)s)""",{'id':int(id),'author':request.authorization.username,'ct':str(datetime.datetime.now()), 'ut':str(datetime.datetime.now()),'cf':'T', 'aid':int(articleId), 'tag':tag})

            if (id>= 1):
                response = Response(status=201, mimetype='application/json')


        except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response


#Delete a tag
@app.route("/tag/deletetag", methods=['DELETE'])
def deletetag():
    if (request.method == 'DELETE'):
        try:
            db = get_database()
            details = request.get_json()
            artid= details['articleId']
            tag=details['tag']
            #for tag in tags:
            rec = db.execute("""select id from article_blog where tag=%(tag)s and flag=%(cf)s allow filtering""", {'tag':tag,'cf':'T'})

            for row in rec:

                db.execute("""delete from article_blog where id = %(artid)s  and flag='T' """,{'artid':int(row.id)})

            # check for exception if delete done response 200
            response = Response(status=200, mimetype='application/json')
            #else:
            #    response = Response(status=404, mimetype='application/json')
        except sqlite3.Error as er:
                print(er)
                response = Response(status=409, mimetype='application/json')

    return response


#Retrive Tags for article id
@app.route("/tag/gettag/<artid>", methods=['GET'])
def getarticle(artid):
    if (request.method == 'GET'):
        try:
            tag_list=[]
            db = get_database()

            max_date_value = db.execute("select max(modifiedDate) as last from article_blog where flag = 'T' and article_id = %(title)s Allow Filtering", {'title': int(artid)})

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

            rec=db.execute("""SELECT tag from article_blog WHERE article_id=%(artId)s and flag='T' allow filtering""",{'artId':int(artid)})

            for row in rec:
                tag_list.append(row)
            if not tag_list:
                response = Response(status=404, mimetype='application/json')
            else:
                response_message = jsonify(list(tag_list))
                response_message.headers['Last-Modified'] = max_date
                response_message.headers['Cache-Control'] = 'public, max-age=300'
                return response_message

        except sqlite3.Error as er:
                response = Response(status=409, mimetype='application/json')

    return response

# get all the articles for a specific tag
@app.route('/tag/getarticles/<tag>',methods=['GET'])
def getart(tag):
    try:
        db = get_database()

        max_date_value = db.execute("select max(modifiedDate) as last from article_blog where flag = 'T' and tag = %(title)s Allow Filtering", {'title': tag})

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

        article_list=[]
        rec= db.execute("""select article_Id from article_blog where tag=%(tag)s and flag=%(cf)s allow filtering""", {'tag':tag,'cf':'T'})

        for row in rec:
            recA=db.execute("""SELECT title,url,author from article_blog WHERE id=%(artid)s allow filtering """ , {'artid':int(row.article_id)})

            for subrow in recA:
                 article_list.append(subrow)


        if not article_list:
            response = Response(status=404, mimetype='application/json')
        else:
            response_message = jsonify(list(articlelist))
            response_message.headers['Last-Modified'] = max_date
            response_message.headers['Cache-Control'] = 'public, max-age=300'
            return response_message

    except sqlite3.Error as er:
            response = Response(status=409, mimetype='application/json')

    return response

if __name__ == 'main':
    app.run(debug=True)
