# each feature function takes an N-long document (list of strings) and returns an N-long list
#   of lists/tuples of features (i.e., strings) to add to the total data for that sentence.
#   often the list will contain lists that are 1-long
import lexicon_list
import spotlight
from tweedr.ml.wordnet import hypernyms
from itertools import izip, chain


def spacer(xs):
    return [' '.join(xs)]


def unigrams(document):
    return [[token] for token in document]


def rbigrams(document):
    grams = zip(document, document[1:] + ['$$$'])
    return map(spacer, grams)


def lbigrams(document):
    grams = zip(['^^^'] + document[:-1], document)
    return map(spacer, grams)


def ctrigrams(document):
    grams = zip(['^^^'] + document[:-1], document, document[1:] + ['$$$'])
    return map(spacer, grams)


def plural(document):
    return [['PLURAL'] if token.endswith('s') else [] for token in document]


def is_transportation(document):
    return [['TRANSPORTATION'] if token in lexicon_list.transportation else [] for token in document]


def is_building(document):
    return [['BUILDING'] if token in lexicon_list.buildings else [] for token in document]


def capitalized(document):
    return [['CAPITALIZED'] if token[0].isupper() else [] for token in document]


def numeric(document):
    return [['NUMERIC'] if token.isdigit() else [] for token in document]


def includes_numeric(document):
    return[['INCLUDES_NUMERIC'] if contains_digits(token) else [] for token in document]


def unique(document):
    seen = {}
    features = []
    for token in document:
        features.append(['UNIQUE'] if token not in seen else [])
        seen[token] = 1
    return features


def get_pos(offset, document):
    doc_joined = " ".join(document)
    beginning = doc_joined[:offset]
    length = len(beginning.split(" ")) - 1
    return length


def contains_digits(string):
    for char in list(string):
        if char.isdigit():
            return True
            break
    return False


def dbpedia_features(document):
    doc_length = len(document)
    doc_joined = " ".join(document)
    positions = [[] for x in xrange(doc_length)]
    try:
        annotations = spotlight.annotate('http://tweedr.dssg.io:2222/rest/annotate', doc_joined, confidence=0.4, support=20)
        for a in annotations:
            offset = a["offset"]
            type = a["types"]
            all_types = type.split(",")
            dbpedia_type = all_types[0]
            pos = get_pos(offset, document)
            db = str(dbpedia_type)
            positions[pos] = [db.upper()]
    except Exception:
        return positions
    return positions


crf_feature_functions = [
    unigrams,
    plural,
    is_transportation,
    is_building,
    capitalized,
    numeric,
    unique,
    hypernyms,
    dbpedia_features,
]

all_feature_functions = crf_feature_functions + [
    rbigrams,
    lbigrams,
    ctrigrams,
]

classifier_feature_functions = [
    unigrams,
]


def featurize_and_then_some(tokens, feature_functions):
    feature_functions_results = [feature_function(tokens) for feature_function in feature_functions]
    list_of_token_features = []
    #add token features
    for token_featuress in izip(*feature_functions_results):
        list_of_token_features.append(list(chain.from_iterable(token_featuress)))
    #add features to the left and to the right
    i = 0
    while i < len(list_of_token_features):
        j = list_of_token_features[i]
        it = [k for k in j]
        if i > 0:
            a = list_of_token_features[i - 1]
            c = ['^^^' + k for k in a]
            c.pop(0)
            it += c

        if i < len(list_of_token_features) - 1:
            b = list_of_token_features[i + 1]
            d = ['$$$' + k for k in b]
            d.pop(0)
            it += d
        i = i + 1
        yield chain.from_iterable([it])


def featurize(tokens, feature_functions):
    '''Take a N-long list of strings (natural text), apply each feature function,
    and then unzip (transpose) and flatten so that we get a N-long list of
    arbitrarily-long lists of strings.
    '''
    feature_functions_results = [feature_function(tokens) for feature_function in feature_functions]
    for token_featuress in izip(*feature_functions_results):
        yield chain.from_iterable(token_featuress)


def main():
    # example usage:
    # echo "The Fulton County Grand Jury said Friday an investigation of Atlanta's recent primary election produced no evidence that any irregularities took place." | python features.py
    import sys
    from tweedr.lib.text import token_re
    for line in sys.stdin:
        # tokenize the document on whitespace
        tokens = token_re.findall(line)
        # apply all feature functions
        tokens_features = featurize(tokens, all_feature_functions)
        for i, token_features in enumerate(tokens_features):
            print i, list(token_features)

if __name__ == '__main__':
    main()
