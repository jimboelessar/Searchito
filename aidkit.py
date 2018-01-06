# -*- coding: utf-8 -*-
import nltk.tokenize
import string
import shelve
import re # Regular Expressions
from nltk.stem.porter import *

# Filters text by removing punctiations, allowing only english letters and numbers,
# tokkenizing text to words and apply stemming.
def filter_text(text):
    # Remove every punctuation. e.g.  "That's." -> "Thats"
    for punct in string.punctuation:
        text = text.replace(punct,'')
    # Tokenize text to words
    words = nltk.tokenize.word_tokenize(text)
    # Allow only english characters and numbers to be included in a word and
    # transform words to lowercase
    words = [re.sub('[^a-zA-Z0-9]', '', word).lower() for word in words] 
    # Remove empty strings
    words = list(filter(None, words))
    # Stemming
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]
    return words

# Removes punctuations from the expression except parenthesis.
def filter_boolean_expression(expression):
    allowed_chars = ['(',')']
    punctuations = [item for item in string.punctuation if item not in allowed_chars]
    for punct in punctuations:
        expression = expression.replace(punct, '')
    return expression
