import numpy as np
import pandas as pd
import sklearn as sk
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.externals import joblib
from sklearn.pipeline import Pipeline

def main():
    data = pd.read_csv('./data/feature_data_jp_ja.csv', sep=',', names=['label', 'feature'])
    
    train = data.drop(['label'], axis=1)
    train_label = data['label']
    
    train_X, val_X, train_Y, val_Y = train_test_split(train, train_label,
                                                  test_size = .2,
                                                  random_state=12)
    
    tf = TfidfVectorizer(analyzer='word', ngram_range=(1,6), max_features=10000,
                    sublinear_tf=True, token_pattern=u'[A-Za-z0-9\-ぁ-ヶ亜-黑ー]{1,}')

    train_X_tf =  tf.fit_transform(train_X['feature'])
    val_X_tf =  tf.transform(val_X['feature'])

    clf_final = Pipeline([('tfidf', TfidfVectorizer(analyzer='word', ngram_range=(1,3), max_features=5000,
                    sublinear_tf=True, token_pattern=u'[A-Za-z0-9\-ぁ-ヶ亜-黑ー]{1,}')),
                           ('clf', GradientBoostingClassifier(
                                random_state = 1337,
                                verbose = 0,
                                n_estimators = 20,
                                learning_rate = 0.079,
                                loss = 'deviance',
                                subsample = 0.86,
                                max_depth = 4
                               ))])
    
    clf_final = clf_final.fit(train_X['feature'], train_Y)
    
    joblib.dump(clf_final, './model/ja_jp_v7.pkl')
    
if __name__ == '__main__':
    main()
