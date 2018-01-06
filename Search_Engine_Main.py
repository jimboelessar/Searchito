from invertedindex import InvertedIndex
import shelve
import aidkit as kit
import booleanmodel
import vectormodel
from searcheengine import SearchEngine

""" Example of creating an inverted index, updating it and getting references of a term.

database = ["doc1.txt", "doc2.txt", "doc3.txt", "doc4.txt"]
database2 = ["doc5.txt", "doc6.txt"]
engine = SearchEngine()
engine.crawl(database)
engine.print_references("englund")
engine.print_references("work")
engine.update_index(database2)
engine.print_references("work")
engine.stop()

"""

""" Print the whole inverted index

with shelve.open('inverted_index') as file:
    for key in file:
        print(key, " -> ", len(file[key]), ": ", file[key])


# Print the links list

with shelve.open('links') as file:
    for key in file:
        print(key, " -> ", file[key])

"""

""" Example of making queries in boolean model

engine = SearchEngine()
queries = []
queries.append("work")
queries.append("a")
queries.append("the")
queries.append("hello")
queries.append("work or a")
queries.append("work or (a and hello)")
# Query is filtered from punctuations first
queries.append("work or ( (not a and not the) or zak.@is) or (wo$$^rk and zakis)..-,")
# Bad queries are handled, empty list of documents is returned
queries.append("work or hello")
queries.append("work or hello bad")
# This is a bad query, but still executed with the missing expression valued as empty
queries.append("work or hello or")

for query in queries:
    print(query, "->", engine.execute_query(query, 10, boolean_mode=True))

engine.stop()

"""

# Example of making queries in  vector model
engine = SearchEngine()
queries = []
queries.append("Zakis zakis is great great great")

for query in queries:
    print(query, "->", engine.execute_query(query, 10))

engine.stop()