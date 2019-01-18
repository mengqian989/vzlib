#coding: utf-8

from __future__ import print_function
import pysolr

import os
import re
import json
import math
from datetime import datetime 
from flask import Flask, render_template, request, redirect, \
     url_for, send_from_directory, g, flash, session, jsonify
from contextlib import closing
from werkzeug import secure_filename
import os.path
from flask import Response

# change this URL
SOLR = 'http://localhost:8080/solr/pmc'

# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr(SOLR, timeout=10)

app = Flask(__name__)
app.config.from_object(__name__)

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

regex = re.compile('\s+')

@app.route('/')
def home():
    query_his = ['']*11
    field_facet = 'Choose Faceting'
    field_plos = 'Choose Dataset'
    field_batch = 'Choose Output'
    field_his = ['All']*11
    conj_his = ['AND']*11
    counter_return = 2
    field1 = 'All'
    return render_template('index.html',batch_string = '', field1 = field1, field_facet = field_facet,field_batch = field_batch,
                           field_plos = field_plos, conj_his = conj_his,
                           query_his_1 = query_his, field_his = field_his, counter_return = counter_return,
                           query_his = json.dumps(query_his))


@app.route('/search',methods = ['POST'])
def search():
    error = None
    docs = None
    total = None
    cursor_mark_num = '*'
    cursor_mark_list = ['*']
    counter_return = 0
    query_all = []
    field_all = []
    query_his = ['']*11
    query_his_1 = []
    field_his = []
    conj_his = []
    prev_1 = '*'
    next_1 = '*'
    counter_1 = 0
    query_final = ''
    q = ''
    q_f_s = ''
    q_f_e = ''
    #query_facet = ''
    #query_final = ''
    field = None
    field_plos = None
    page = 1
    page_prev = 0
    #field_facet = 'Choose Faceting'
    field_plos = 'Choose Dataset'

    #get all of the query
    counter = 1
    query_name = "query1"
    field_name = "field1"
    check = request.form.get(query_name,None)
    
    while check != None:
        if request.form[query_name] != '':
            query_all.append(query_name)
            field_all.append(field_name)
        counter = counter + 1
        query_name = "query" + str(counter)
        field_name = "field" + str(counter)
        check = request.form.get(query_name,None)
        
    
    # if no query...        
    if query_all == []:
        error = u'No query provided'
    
    #loop through all query
    else:
        cursor_mark = request.form['cursor_mark']
        page = int(request.form['page'])
        if cursor_mark == 'prev':
            if page == 1:
                error = u'No previous page'
                page_prev = 1
            else:
                page = page - 1
                cursor_mark_num = request.form['prev']
                page_prev = page - 1
                
        elif cursor_mark == 'next':
            page =  page + 1
            cursor_mark_num = request.form['next']
            page_prev = page - 1

        """        
        page = int(request.form['page'])+1
        next_1 = request.form['next']
        prev_1 = request.form['prev']
        """
        
        counter_1 = 0 #add one at the end
        for query_name in query_all:
            q = request.form[query_name]
            field_name = field_all[counter_1]
            field = request.form[field_name]
            query_his[counter_1] = q
            field_his.append(field)
            q_1 = q
            q = '"'+q+'"'
            conj_name = "conj"+str(counter_1+1)
            
            if field == 'Title':
                query = 'title:' + q
            elif field == 'Abstract':
                query = 'abstract:' + q
            elif field == 'Author':
                query = 'author:' + '"*' + q_1 + '*"'
            elif field == 'Journal Name':
                query = 'journal_name:' + q
            elif field == 'Body':
                query = 'body:' + q
            elif field == 'Subject':
                query = 'subject:' + q
            elif field == 'Affiliation':
                query = 'author_affiliate:' + q
            
            elif field == 'Publication Date (YYYY-MM-DD)':
                if re.findall("^[0-9]{4}-[0-9]{2}-[0-9]{2}$",q)==[]:
                    error = u'Not a correct date format'
                    query = 'publication_date:0000-00-00'
                else:
                    query = 'publication_date:' + q
            #facet?
            #date searching?
                
            else:
                query = 'title:' + q + ' abstract:' + q \
                    + ' subject:' + q + ' author:' + q \
                    + ' body:' + q + ' journal_name:' + q \
                    + ' author_affiliate:' + q
            
            if query_final == '':
                query_final += query
            else:
                conj_ = request.form[conj_name]
                conj_his.append(conj_)
                conj = " " + conj_ + " " 
                query_final += conj
                query_final += query

            
            counter_1 += 1

        
        
        #print(q)
        #print(field)
        #print(next)
        
        #querying through date deviation
        
        if request.form['query_facet_s'] != '' :
            if request.form['query_facet_e'] !='':
                q_f_s = request.form['query_facet_s']
                q_f_e = request.form['query_facet_e']
                query_facet = ' AND publication_date:[' + q_f_s + 'T00:00:00Z TO ' + q_f_e + 'T00:00:00Z]'
                query_final += query_facet 
            else:
                query_facet = ''
        else:
            query_facet = ''
        
        field_plos = request.form['field_plos']
        
        if field_plos == 'PLoS':
            SOLR = 'http://localhost:8080/solr/plos'
            
        else:
            SOLR = 'http://localhost:8080/solr/pmc'
            
        
        solr = pysolr.Solr(SOLR, timeout=10)
        
        params= {
                 'cursorMark': cursor_mark_num,
                 'sort': 'id asc'
                }
        
        
        docs = solr.search(query_final, **params)
            
        query_his_1 = query_his    
        total = docs.hits

        cursor_mark_list = request.form['cursor_mark_list']
        cursor_mark_list = cursor_mark_list.split(';')
        next_1 = docs.nextCursorMark
        if next_1 not in cursor_mark_list:
            cursor_mark_list.append(next_1)
        prev_1 = cursor_mark_list[page_prev-1]
        
        cursor_mark_list = ';'.join(cursor_mark_list)
        
        counter_1 += 1 
            #print(next)
    
            #for d in docs:
            #    print("The title is '{0}'.".format(d['title']))
            
    
    return render_template("index.html", docs=docs,
                           prev_1 = prev_1, next_1 = next_1,
                           cursor_mark_list = cursor_mark_list,
                           total=total,
                           query_facet_s=q_f_s,query_facet_e=q_f_e,
                           query_final = query_final,
                           field_plos = field_plos,
                           query_his = json.dumps(query_his),
                           field_his = field_his,
                           query_his_1 = query_his_1,
                           conj_his = conj_his, counter_return = counter_1,
                           page=page, error=error)

@app.route('/download_all', methods=['POST'])
def download():
    query_final = request.form['query_final']
    if request.form['params'] == 'all':
        params = {'rows':2000000000}
        docs_all = solr.search(query_final,**params)
        batch_string = ''
        for doc in docs_all:
            batch_string += json.dumps(doc)
        content = batch_string
        return Response(content, 
                mimetype='application/json',
                headers={'Content-Disposition':'attachment;filename=results.json'})
    elif request.form['params'] == 'facet':
        params = {
                'facet': 'on',
                 'facet.field': 'publication_date_facet',
                }
        docs = solr.search(query_final, **params)
        facet_string = ''
        facet_month = docs.facets['facet_fields']['publication_date_facet']
        facet_size = range(len(facet_month))
        counter_facet = 0
        for counter_facet in facet_size:
            date = facet_month[counter_facet]
            if type(date) == str:
                number = facet_month[counter_facet + 1]
                if type(number) == int and number != 0:
                    facet_string += date + "," + str(number) + "\n"
            counter_facet += 1
        content = facet_string
        return Response(content, 
                mimetype='application/octet-stream',
                headers={'Content-Disposition':'attachment;filename=facet.txt'}) 
    

if __name__ == '__main__':

    app.run('127.0.0.1', 5000, debug=True)
