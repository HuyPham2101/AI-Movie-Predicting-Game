from flask import Flask, render_template, request
from nlp import predict_title
from string import Template
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://localhost:3030/TMDB/sparql")

title_query = """
PREFIX : <https://www.themoviedb.org/kaggle-export/>
SELECT  ?title
    WHERE {
    ?m a :Movie;
        :title ?title ;
    }
"""


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
        result = query(title)
        if len(result) == 0:
            print("Predicting ...")
            title = predict_title(prepare, title)
            print('found : ', title)
        result = query(title)
        print(result)
        return render_template('index.html', info=result)
    else:
        return render_template('index.html', info=[])


if __name__ == '__main__':
    app.run()
