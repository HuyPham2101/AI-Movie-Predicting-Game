import pickle
from flask import Flask, render_template, request
from algo import predict_title, preprocess
from string import Template
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import numpy as np

sparql = SPARQLWrapper("http://localhost:3030/TMDB/sparql")
model = pickle.load(open('data/model.pkl', 'rb'))
title_query = """
PREFIX : <https://www.themoviedb.org/kaggle-export/>
SELECT  ?title
    WHERE {
    ?m a :Movie;
        :title ?title ;
    }
"""
lang_query = """
PREFIX : <https://www.themoviedb.org/kaggle-export/>
SELECT Distinct ?lang
    WHERE {
    ?m a :Movie;
        :original_language ?lang ;
    }
"""


def query_lang():
    sparql.setQuery(lang_query)
    sparql.setReturnFormat(JSON)
    results_dict = sparql.query().convert()
    results = [t['lang']['value'] for t in results_dict['results']['bindings']]
    return results


def prepare():
    sparql.setQuery(title_query)
    sparql.setReturnFormat(JSON)
    results_dict = sparql.query().convert()
    results = [t['title']['value'] for t in results_dict['results']['bindings']]
    return results


info_query = """
PREFIX : <https://www.themoviedb.org/kaggle-export/>
SELECT ?original_lang ?overview ?release_date ?status ?runtime ?budget ?revenue
    WHERE {
    ?m a :Movie;
        :title "$title" ;
        :original_language ?original_lang ;
        :release_date ?release_date ;
        :status ?status ;
        :runtime ?runtime ;
        :overview ?overview ;
        :budget ?budget ;
        :revenue ?revenue;
    }

"""

app = Flask(__name__)


def query(title):
    query_string = Template(info_query).substitute(title=title)
    sparql.setQuery(query_string)
    sparql.setReturnFormat(JSON)
    results_dict = sparql.query().convert()
    results = [obj for obj in results_dict['results']['bindings']]
    return results


@app.route("/", methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        title = request.form['title']
        suggestion = title
        # if the title not given . return a warning
        if title == '':
            return render_template('index.html', info=[], warning="Enter a title", suggestion='')
        result = query(title)
        # if the result is empty , predict the correct title
        if len(result) == 0:
            print("Predicting ...")
            suggestion = predict_title(prepare, title)
            print('found : ', suggestion)
        # check if there is a suggestion.
        if title != suggestion:
            result = query(suggestion)
        else:
            suggestion = ''
        return render_template('index.html', info=result, warning='', suggestion=suggestion)
    else:
        return render_template('index.html', info=[], warning='', suggestion='')


@app.route("/game", methods=('GET', 'POST'))
def guessing_game():
    langs = query_lang()
    if request.method == 'POST':
        title = request.form['title'] if request.form['title'] else np.nan
        budget = request.form['budget'] if request.form['budget'] else np.nan
        runtime = request.form['runtime'] if request.form['runtime'] else np.nan
        lang = request.form.get('lang_select')
        data = pd.DataFrame({'title': [title], 'budget': [budget], 'runtime': [runtime], 'lang': [lang]})
        data = preprocess(data)
        result = model.predict(data)
        return render_template('game.html', lang=langs, revenue=result[0])
    else:
        return render_template('game.html', lang=langs, revenue='')


if __name__ == '__main__':
    app.run()
