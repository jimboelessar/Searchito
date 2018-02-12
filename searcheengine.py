# -*- coding: utf-8 -*-


import shelve
import aidkit as kit
from crawella import Crawella
import os
import nltk.tokenize
from invertedindex import InvertedIndex
#from collections import Counter
import booleanmodel
import vectormodel
#import shelve
import time
from os import listdir
from os.path import isfile, join
import shutil

class SearchEngine:

    def __init__(self):
        self.is_maintaining = False
        self.index_filename = 'files/inverted_index'
        self.info_filename = 'files/documents_info.txt'
        self.links_filename = 'files/links'
        self.temp_filename = 'files/temp_terms'
        self.uploads_folder = 'uploads/'
        self.documents_folder = 'website/static/server_documents/'
        self.rel_documents_folder = 'static/server_documents/'
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

    # Saves to disk the total number of indexed documents and the id of the lated
    # document.
    def save_docs_info(self):
        with open(self.info_filename, 'w') as info:
            info.write(str(self.no_docs) + " " + str(self.last_id))

    # Processes the given document names by creating their inverted index and saving 
    # information to disk.
    def crawl(self,url,maxLinks):
        if self.is_maintaining:
            return False
        self.is_maintaining = True
        
        crawler = Crawella()
        self.last_id = crawler.crawl(url,self.temp_filename,self.links_filename,maxLinks)
        # Create the inverted index of the crawled documents
        starttime = time.time()
        self.inverted_index.create_inverted_index(self.temp_filename)
        os.remove(self.temp_filename)
        print(time.time()-starttime, ' sec')

        # Update documents info
        self.no_docs = self.last_id 
        self.save_docs_info()
        self.is_maintaining = False

    # Updates inverted index with the documents inside the uploads folder.
    def update_from_uploaded(self):
        if self.is_maintaining: return False
        self.is_maintaining = True

        documents = [] # The name of the documents to index
        # Move documents from temporal uploads to permanent documents 
        uploaded_documents = [f for f in listdir(self.uploads_folder) if isfile(join(self.uploads_folder, f))] # Get documents name
        for f in uploaded_documents:
            # If document name already exists in the local documents, change its name
            new_name = kit.resolve_conflict(self.documents_folder, f)
            os.rename(self.uploads_folder + f, self.uploads_folder + new_name)
            # Add document name to the list of documents to index
            documents.append(new_name)
            # Move document to the local documents
            shutil.move(self.uploads_folder + new_name, self.documents_folder[:-1])

        # Create a list of documents path and their ids
        doc_ids = []
        for doc_name in documents:
            self.last_id += 1
            doc_ids.append([self.last_id, self.documents_folder + f])
    
        # Update the inverted index and get documents length
        lengths = self.inverted_index.update_index(doc_ids)

        # Insert the links and ids of the new documents
        doc_links = shelve.open(self.links_filename, writeback=True)
        for index, doc_name in enumerate(documents):
            doc_links[str(doc_ids[index][0])] = [self.rel_documents_folder + doc_name, lengths[index]]
        doc_links.close()

        # Update general information about documents
        self.no_docs += len(documents)
        self.save_docs_info()

        self.is_maintaining = False

    # Executes the given query and returns at most a maximum number of documents.
    def execute_query(self, query, boolean_mode=False, max_results=20):
        if self.is_maintaining:
            return []
        if boolean_mode:
            resultIDs = booleanmodel.execute_query(query, max_results, self.inverted_index)
        else:
            resultIDs = vectormodel.execute_query(query, self.inverted_index, self.links_filename, self.no_docs, max_results)
        resultURLs = []
        print(resultIDs)
        with shelve.open(self.links_filename) as links:
            for key in links:
                if int(key) in resultIDs:
                    resultURLs.append(links[key][0])
        return resultURLs

    ##TO BE REMOVED## For testing purposes only
    def print_references(self, term):
        print(self.inverted_index.get_term_references(term))