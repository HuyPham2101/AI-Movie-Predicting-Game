from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import spacy
import string
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
import pickle

sparql = SPARQLWrapper("http://localhost:3030/TMDB/sparql")


def predict_title(query: any, input_title: str) -> str:
    """Predicts an answer to a given question
    :param query:
    :param input_title:
    :return: answer string or None if insufficient confidence"""
    res = query()
    # remove punctuation
    titles = np.array([r.translate(str.maketrans('', '', string.punctuation)) for r in res])
    data = pd.DataFrame({'Title': titles}, index=None)

    answer = None
    nlp = spacy.load('en_core_web_md')
    input_title = nlp(input_title)
    listt = []
    maxx = 0
    # create a list of list pair of similarity and answer
    for line in data["Title"]:
        doc_title = nlp(line)
        listt.append([doc_title.similarity(input_title), doc_title.text])
    # find out the most correct answer
    for pair in listt:
        for ele in pair:
            if (not isinstance(ele, str)) and (ele > maxx):
                maxx = ele
                answer = pair[-1]
    # print(question.text,answer)
    return answer


def fetch_data():
    info_query = """
    PREFIX : <https://www.themoviedb.org/kaggle-export/>
    SELECT ?original_lang ?runtime ?budget ?revenue ?title
        WHERE {
        ?m a :Movie;
            :title ?title ;
            :original_language ?original_lang ;
            :runtime ?runtime ;
            :budget ?budget ;
            :revenue ?revenue;
        }
    """
    sparql.setQuery(info_query)
    sparql.setReturnFormat(JSON)
    results_dict = sparql.query().convert()
    results = [t for t in results_dict['results']['bindings']]
    infos = []
    for res in results:
        film = {'lang': res['original_lang']['value'], 'title': res['title']['value'], 'budget': res['budget']['value'],
                'revenue': res['revenue']['value'], 'runtime': res['runtime']['value']}
        infos.append(film)
    return pd.DataFrame(infos)


def create_model():
    data = fetch_data()
    train_data = preprocess(data.drop(['revenue'], axis=1))
    target = data['revenue']
    regess = LogisticRegression(solver='liblinear')
    regess.fit(train_data, target)
    return regess


def preprocess(data):
    data['lang'] = data['lang'].fillna('en')
    data['title'] = data['title'].fillna('No title')
    data['budget'] = data['budget'].fillna(data['budget'].mean())
    data['runtime'] = data['runtime'].fillna(data['runtime'].mean())
    if data.size == 4:
        data['budget'] = data['budget'].fillna(0)
        data['runtime'] = data['runtime'].fillna(0)
    label_list = ['title', 'lang']
    for column in label_list:
        # encode the label to int
        le = LabelEncoder()
        data[column] = le.fit_transform(data[column].astype(str))
        # transform data distribution to a mean value 0 and standard deviation of 1
        ss = StandardScaler()
        data[column] = ss.fit_transform(data[column].values.reshape(-1, 1))
    return data


if __name__ == '__main__':
    model = create_model()
    pickle.dump(model, open('data/model.pkl', 'wb'))
