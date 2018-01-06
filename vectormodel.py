import aidkit as kit
import math
from collections import Counter

# Calculate the TFt value of the given term.
def tf(term, frequencies):
    return 1 + math.log(frequencies[term])

# Calculate the IDFt value of the given term.
def idf(term, no_docs, inverted_index):
    term_doc_freq = len(inverted_index[term])
    if term_doc_freq == 0:
        return 0
    else:
        # Filter negative values to zero
        return max(0, math.log(1 + (no_docs/term_doc_freq)))

# Calculate the weight of the value
def tfidf(term, frequencies, no_docs, inverted_index):
    return tf(term, frequencies) * idf(term, no_docs, inverted_index)


# Executes a query based on the vector model and returns the document ids that match.
# max_results:  The maximum number of document ids to return.
def execute_query(query, max_results, inverted_index, links_filename, no_docs):
    terms = kit.filter_text(query)
    unique_terms = set(terms)
    # Create an inverted index consisting of only query terms
    query_index = {}
    for term in terms:
        query_index[term] = inverted_index.get_term_references(term)
    # Find each term's frequency
    terms_freq = Counter(terms)
    # Calculate query weights
    term_weights = [tfidf(term, terms_freq, no_docs, query_index) for term in unique_terms]
