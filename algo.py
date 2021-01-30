from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import spacy
import string
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
import pickle
from sklearn.model_selection import cross_val_score

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


def create_model():
    data = pd.read_csv('data/train.csv')
    data = data[['title', 'budget', 'revenue', 'runtime', 'original_language']]
    data['lang'] = data['original_language']
    data = data.drop(['original_language'], axis=1)
    train_data = preprocess(data.drop(['revenue'], axis=1))
    target = data['revenue']
    regess = LogisticRegression(solver='liblinear')
    regess.fit(train_data, target)
    # evaluate model
    # X_train = train_data
    # y_train = target
    # scores = cross_val_score(regess, X_train, y_train)
    # print(f'Accuracy: {scores.mean()}')
    # test model
    # test = pd.read_csv('data/test.csv')
    # test = test[['title', 'budget', 'runtime', 'original_language']]
    # test['lang'] = test['original_language']
    # test = test.drop(['original_language'], axis=1)
    # test_data = preprocess(test)
    # predictions = regess.predict(test_data)
    #
    # output = pd.DataFrame({'id': test.title, 'revenue': predictions})
    # output.to_csv('data/submission.csv', index=False)
    return regess


def preprocess(data):
    data['lang'] = data['lang'].fillna('en')
    data['title'] = data['title'].fillna('No title')
    imp = SimpleImputer(missing_values=np.nan, strategy='mean')
    if data.size == 4:
        data['budget'] = data['budget'].fillna(0)
        data['runtime'] = data['runtime'].fillna(0)
    else:
        data['budget'] = imp.fit_transform(data[['budget']])
        data['runtime'] = imp.fit_transform(data[['runtime']])
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
