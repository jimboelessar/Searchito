import shelve
import aidkit as kit
import math
import os
import nltk.tokenize
from invertedindex import InvertedIndex
from collections import Counter
import booleanmodel
import vectormodel
import shelve

class SearchEngine:

    def __init__(self):
        self.is_maintaining = False
        self.index_filename = 'inverted_index'
        self.info_filename = 'documents_info.txt'
        self.links_filename = 'links'
        self.temp_filename = 'temp_terms'
        self.inverted_index = InvertedIndex(self.index_filename)
        self.inverted_index.open()

        # Get information about the total documents number and the id of the last
        # document that was added.
        try:
            with open(self.info_filename, 'r') as info_file:
                info = nltk.tokenize.word_tokenize(info_file.read())
                self.no_docs = int(info[0])
                self.last_id = int(info[1])
        except IOError:
            self.no_docs = 0
            self.last_id = 0

    def stop(self):
        self.inverted_index.close()

    # Filters the fiven document and for every word inside it writes to disk the 
    # pair (term, document id, frequency inside document). Returns it's length.
    def process_doc(self, doc_id, doc_name):
        # Open temporary file to append each term's frequency
        terms_file = open(self.temp_filename, 'a')
        # Open document and read it
        with open(doc_name, 'r') as doc_file:
            doc = doc_file.read()
        filtered_words = kit.filter_text(doc)
        # Find each term's frequency
        terms_freq = Counter(filtered_words)
        # Write pair (term, document id, frequency) to disk
        for term in terms_freq.keys():
            terms_file.write("{} {} {}\n".format(term, doc_id, terms_freq[term]))
        terms_file.close()
        # Return the length of the document (sqrt of document frequency)
        return math.sqrt(len(filtered_words))

    # Saves to disk the total number of indexed documents and the id of the lated
    # document.
    def save_docs_info(self):
        with open(self.info_filename, 'w') as info:
            info.write(str(self.no_docs) + " " + str(self.last_id))

    # Processes the given document names by creating their inverted index and saving 
    # information to disk.
    def crawl(self, documents):
        if self.is_maintaining:
            return False
        self.is_maintaining = True

        # Open document links dictionary if already exists or create a new one
        doc_links = shelve.open(self.links_filename, writeback=True)
        # Clear any previous data
        doc_links.clear()
        # Reset last document id
        self.last_id = 0
        # Crawl documents and process them one by one
        for doc_name in documents:
            self.last_id += 1
            # Process document by writing it's terms frequency to disk and get it's length
            length = self.process_doc(self.last_id, doc_name)
            # Save document's necessary information (key must be string)
            doc_links[str(self.last_id)] = [doc_name, length]
        doc_links.close()

        # Create the inverted index of the crawled documents
        self.inverted_index.create_inverted_index(self.temp_filename)
        os.remove(self.temp_filename)

        # Update documents info
        self.no_docs = len(documents) 
        self.save_docs_info()
        self.is_maintaining = False

    # Updates inverted index with the given documents
    def update_index(self, documents):
        if self.is_maintaining:
            return False
        self.is_maintaining = True

        # Create a list of documents and their ids
        doc_ids = []
        for doc_name in documents:
            self.last_id += 1
            doc_ids.append([self.last_id, doc_name])
    
        # Update the inverted index and get documents' length
        lengths = self.inverted_index.update_index(doc_ids)

        # Update links to documents
        doc_links = shelve.open(self.links_filename, writeback=True)
        for index, doc_name in enumerate(documents):
            doc_links[str(doc_ids[index][0])] = [doc_name, lengths[index]]
        doc_links.close()

        self.no_docs += len(documents)
        self.save_docs_info()
        self.is_maintaining = False

    # Executes the given query and returns at most a mixmum number of documents.
    def execute_query(self, query, max_results, boolean_mode=False):
        if self.is_maintaining:
            return []

        if boolean_mode:
            result = booleanmodel.execute_query(query, max_results, self.inverted_index)
        else:
            result = vectormodel.execute_query(query, max_results, self.inverted_index, self.links_filename, self.no_docs)

        return result

    ##TO BE REMOVED## For testing purposes only
    def print_references(self, term):
        print(self.inverted_index.get_term_references(term))