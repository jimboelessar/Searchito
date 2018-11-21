# -*- coding: utf-8 -*-


import shelve
import aidkit as kit
from crawella import Crawella
import os
import nltk.tokenize
from invertedindex import InvertedIndex
import booleanmodel
import vectormodel
import time
from os import listdir
from os.path import isfile, join
import shutil
import pathlib

class SearchEngine:

    def __init__(self):
        self.is_maintaining = False
        foldername = 'files'
        # If the folder does not exist, we create it
        pathlib.Path(foldername).mkdir(parents=True, exist_ok=True)
        self.index_filename = foldername + '/inverted_index'
        self.info_filename = foldername + '/documents_info.txt'
        self.links_filename = foldername + '/links'
        self.temp_filename = foldername + '/temp_terms'
        self.uploads_folder = 'uploads/'
        self.documents_folder = 'static/server_documents/'
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

    def restart(self):
        self.inverted_index.close()
        self.inverted_index.open()

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
        num_crawled_docs = crawler.crawl(url,self.temp_filename,self.links_filename,maxLinks, self.last_id)
        if (num_crawled_docs != 0):      
            # Create or update the inverted index 
            self.inverted_index.create_inverted_index(self.temp_filename)
            # Update documents' info
            self.last_id += num_crawled_docs
            self.no_docs += num_crawled_docs
            self.save_docs_info()
        os.remove(self.temp_filename)
        self.is_maintaining = False
        print("Success")

    # Updates inverted index with the documents inside the uploads folder.
    def update_from_uploaded(self):
        if self.is_maintaining: return False
        self.is_maintaining = True

        documents = [] # The name of the documents to index
        # Move documents from temporal uploads to permanent documents 
        kit.create_dicrectory(self.documents_folder)
        uploaded_documents = [f for f in listdir(self.uploads_folder) if isfile(join(self.uploads_folder, f))] # Get documents name
        for f in uploaded_documents:
            # Try to decode the file or else ignore it
            try:
                # Try to read the file
                with open(self.uploads_folder + f, 'r') as doc_file:
                    doc_file.read()
                # If document name already exists in the local documents, change its name
                new_name = kit.resolve_conflict(self.documents_folder, f)
                os.rename(self.uploads_folder + f, self.uploads_folder + new_name)
                # Add document name to the list of documents to index
                documents.append(new_name)
                # Move document to the local documents
                shutil.move(self.uploads_folder + new_name, self.documents_folder[:-1])
            except UnicodeDecodeError:
                # Delete file, can not decode it
                os.remove(self.uploads_folder + f)
        # Create a list of documents path and their ids
        doc_ids = []
        for doc_name in documents:
            self.last_id += 1
            doc_ids.append([self.last_id, self.documents_folder + doc_name])
    
        # Update the inverted index and get documents length
        lengths = self.inverted_index.update_index(doc_ids)

        # Insert the links and ids of the new documents
        doc_links = shelve.open(self.links_filename, writeback=True)
        for index, doc_name in enumerate(documents):
            doc_links[str(doc_ids[index][0])] = [self.documents_folder + doc_name, lengths[index]]
        doc_links.close()

        # Update general information about documents
        self.no_docs += len(documents)
        self.save_docs_info()

        self.is_maintaining = False

    # Executes the given query and returns at most max_results documents.
    def execute_query(self, query, boolean_mode=False, max_results=20):
        if self.is_maintaining:
            return []
        if boolean_mode:
            resultIDs = booleanmodel.execute_query(query, max_results, self.inverted_index)
        else:
            resultIDs = vectormodel.execute_query(query, self.inverted_index, self.links_filename, self.no_docs, max_results)
        resultURLs = []
        with shelve.open(self.links_filename) as links:
            for id in resultIDs:
                resultURLs.append(links[str(id)][0])
        return resultURLs
