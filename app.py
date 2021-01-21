from flask import Flask, render_template, request
# from flaskwebgui import FlaskUI
from string import Template
from SPARQLWrapper import SPARQLWrapper, JSON
import rdflib

g = rdflib.Graph()
g.parse('data/TMDB.ttl', format='turtle')
sparql = SPARQLWrapper("http://localhost:3030/TMDB/sparql")

actor_query = """
PREFIX : <https://www.themoviedb.org/kaggle-export/>
SELECT ?actor
WHERE{?m a :Movie ; :title "$title" ;  :cast/:name?actor.}
"""

app = Flask(__name__)


def query(title):
    query_string = Template(actor_query).substitute(title=title)
    sparql.setQuery(query_string)
    sparql.setReturnFormat(JSON)
    results_dict = sparql.query().convert()
    results = [row['actor']['value'] for row in results_dict['results']['bindings']]
    return results


@app.route("/", methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        title = request.form['title']
        return render_template('index.html', actors=[])
    else:
        return render_template('index.html', actors=[])


if __name__ == '__main__':
    app.run()
