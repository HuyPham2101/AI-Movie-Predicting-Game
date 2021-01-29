from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import spacy
import string
import numpy as np

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

