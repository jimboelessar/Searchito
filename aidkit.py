# -*- coding: utf-8 -*-
import nltk.tokenize
import string
import shelve
import re # Regular Expressions
from nltk.stem.porter import *
import os
import shutil
import os
import errno

# Filters text by removing punctiations, allowing only english letters and
# numbers,
# tokkenizing text to words and apply stemming.
def filter_text(text):
    # Remove every punctuation.  e.g.  "That's." -> "Thats"
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

# If the basename of the file already exists in the target folder, returns a
# new name for the file, else returns the basename.
def resolve_conflict(target_folder, basename):
        """
        From Flesk-Uploads package.
        """
        if not os.path.exists(os.path.join(target_folder, basename)):
            return basename

        name, ext = os.path.splitext(basename)
        count = 0
        while True:
            count = count + 1
            newname = '%s(%d)%s' % (name, count, ext)
            if not os.path.exists(os.path.join(target_folder, newname)):
                return newname

# Deletets all the files inside the given directory
def delete_files_of_directory(directory):
    for the_file in os.listdir(directory):
        file_path = os.path.join(directory, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

# Creates the given directory if it does not exist already
def create_dicrectory(directory):
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise