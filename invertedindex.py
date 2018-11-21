# -*- coding: utf-8 -*-

import shelve
import sys
import math
import aidkit as kit
from collections import Counter
import big_file_sort as sorter
import os

class InvertedIndex:

    # Sets the filename of the inverted index.
    def __init__(self, filename):
        self.filename = filename
        self.memory_index = {}
        # Set if index is open for reading
        self.is_opened = False

    # Opens index for reading.
    # max_size: The maximum size of memory usage in Mb before writing to disk updated index
    def open(self, max_size=100):
        # Convert size to bytes
        self.max_size = 100 * 1024 * 1024
        if not self.is_opened:
            try:
                self.inverted_index = shelve.open(self.filename, flag='r')
            except Exception:
                # If index does not exist, create a new one and reopen it in read mode
                self.inverted_index = shelve.open(self.filename)
                self.inverted_index.close()
                self.inverted_index = shelve.open(self.filename, flag='r')
            self.is_opened = True
    # Closes inverted index.
    # ignore_updates:   Does not update main index with the temporary memory index
    def close(self, ignore_updates=False):
        # If there is a memory index and should not ignore it, merge memory index with main index
        if self.memory_index and not ignore_updates :
            self.merge_indexes()

        # Close main index
        if(self.is_opened):
            self.inverted_index.close()
            self.is_opened = False

    # Returns the references of the given term at the indexed documents.
    # Returns empty list if there are no references of this term.
    # ignore_availability:  True to ignore that the index may be currently processed
    def get_term_references(self, term):
        # Try to fetch references from memory index
        if term in self.memory_index: memory_refs = self.memory_index[term]
        else: memory_refs = []
        #Try to fetch references from disk index
        if self.is_opened:
            try:
                return self.inverted_index[term] + memory_refs
            except KeyError:
                return memory_refs
        else:
            return []

    # Creates a new inverted index from scratch.
    def create_inverted_index(self, temp_file_name):
        open_again = self.is_opened
        self.close()

        # Sort file externally
        kit.create_dicrectory('tmp') # Create folder for temporary chunks of data
        sorter.sort_file(temp_file_name, 'files/sorted_terms', temp_file_location='tmp') # Sort data
        kit.delete_files_of_directory('tmp') # Delete chunks of data, no more needed (the sort function does not handle it)
        os.remove(temp_file_name) # Remove unsorted file
        os.rename('files/sorted_terms', temp_file_name) # Rename sorted to the name of the unsorted file (used later)

        # Create the inverted index to disk
        # Open index if already exists or create a new one
        inv_index = shelve.open(self.filename)
        terms_file = open(temp_file_name, 'r')

        # Create index while merging references of the same term
        firstRow = True
        for row in terms_file:
            # Convert row to (term, document id, frequency)
            term_record = row.split()
            term_record[1] = int(term_record[1])
            term_record[2] = int(term_record[2])

            # If it is the first row to be read, initialize references of term
            if(firstRow):
                term = term_record[0]
                references = []
                firstRow = False
            # If current term is different from the previous one, then merging for previous term is completed
            elif term_record[0] != term:
                # Write previous term to index
                try:
                    # If term already exists
                    inv_index[term] += references
                except KeyError:
                    # If term is new
                    inv_index[term] = references
                # Initialize references of the new term
                term = term_record[0]
                references = []
            # Add reference of the term to the current document
            references.append(term_record[1:])
        # Write the last merged term to index
        inv_index[term] = references
    
        terms_file.close()
        inv_index.close()

        if open_again:
            self.open()
            

    # Updates the inverted index with new documents. The new index is kept in memory until
    # it reaches max_size and then it is written to disk.
    # id_doc_list:  A list containing information for every document in format 
    # [document id, document name].
    def update_index(self, id_doc_list):
        doc_lengths = []
        # If main index was closed, open it temporarily
        close_again = not self.is_opened
        self.open()

        for doc_info in id_doc_list:
            # Open document and read it
            with open(doc_info[1], 'r') as doc_file:
                doc = doc_file.read()
            filtered_words = kit.filter_text(doc)
            doc_lengths.append(math.sqrt(len(filtered_words)))
            # Find each term's frequency
            terms_freq = Counter(filtered_words)
            # Insert term references in memory index
            for term in terms_freq.keys():
                if(term in self.memory_index):
                    self.memory_index[term].append([doc_info[0], terms_freq[term]])
                else:
                    self.memory_index[term] = [[doc_info[0],terms_freq[term]]]
            # If memory index is exceeding the maximum allowed memory size, merge index to the main index in disk
            if sys.getsizeof(self.memory_index) >= self.max_size:
                merge_indexes()
        
        if close_again:
            self.close()
        return doc_lengths

    # Filters all given docs and for every word inside a document writes to disk the 
    # pair (term, document id, frequency inside document).
    def write_filtered_doc(self, id_doc_map, temp_file_name):
         # Open temporary file to write each term's frequency
        terms_file = open(temp_file_name,'w')
        for id in id_doc_map.keys():
            # Open document and read it
            with open(id_doc_map[id],'r') as doc_file:
                doc = doc_file.read()
            filtered_words = kit.filter_text(doc)
            # Find each term's frequency
            terms_freq = {}
            for word in filtered_words:
                if word in terms_freq:
                    terms_freq[word] += 1
                else: 
                    terms_freq[word] = 1
            # Write pair (term, document id, frequency) to disk
            for term in terms_freq.keys():
                terms_file.write("{} {} {}\n".format(term, id, terms_freq[term]))
        terms_file.close()

    # Merges the memory index with the main index in disk.
    def merge_indexes(self):
        # If main index was already open for reading, close it temporarily
        open_again = self.is_opened
        self.close(ignore_updates=True)

        # Open main index
        inv_index = shelve.open(self.filename)

        # Insert new terms or update the ones that already exists from the memory index
        for term in self.memory_index.keys():
            try:
                # If term already exists
                inv_index[term] += self.memory_index[term]
            except KeyError:
                # If term is new
                inv_index[term] = self.memory_index[term]
        
        # Memory index is no longer needed
        self.memory_index = {}
        inv_index.close()
        if(open_again):
            self.open()
        