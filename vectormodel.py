import aidkit as kit
import math
from collections import Counter
import shelve

# Calculate the TF value of the given term.
def tf(term, frequency):
    if (frequency!=0):
        return 1 + math.log(frequency)
    else:
        return 0

# Calculate the IDF value of the given term.
def idf(term, no_docs, inverted_index):
    term_doc_freq = len(inverted_index[term])
    if term_doc_freq == 0:
        return 0
    else:
        # Filter negative values to zero
        return max(0, math.log(1 + (no_docs/term_doc_freq)))

# Calculate the weight of the value
def tfidf(term, frequency, no_docs, inverted_index):
    tf_ =  tf(term, frequency)
    if (tf_!=0):
        return  tf_* idf(term, no_docs, inverted_index)
    else:
        return 0

def cosineSimilarity(wq, wd, ld):
    dot = sum(wq[i]*wd[i] for i in range(len(wq)))
    sim = dot/ld
    return sim

def compute_docs_weights(query_index, relevant_docs, no_docs):
    #Calculate the weights for every relevant document
    docs_weights = []
    for doc in relevant_docs :
        doc_weights=[]
        for term in query_index:
            found = False
            for i in range (len(query_index [term])):
                if query_index [term] [i] [0]== doc:
                    doc_weights.append(tfidf(term, query_index[term][i][1],no_docs,query_index ) )
                    found = True
                    break
            if (found==False):
                doc_weights.append(0)
        docs_weights.append(doc_weights)
    return docs_weights
    
    
'''Executes a query based on the vector model and returns the document IDs that match.
   max_results:  The maximum number of documents to return.'''
def execute_query(query, inverted_index, links_filename, no_docs, max_results = 20):
    #Remove punctuation 
    terms = kit.filter_text(query)
    # Find each term's frequency
    terms_freq = Counter(terms)
    unique_terms = set(terms)
    # Create an inverted index consisting of only query terms
    query_index = {}
    for term in unique_terms:
        query_index[term] = inverted_index.get_term_references(term)
    relevant_docs = set([query_index[term][i][0] for term in unique_terms for i in range(len(query_index[term]))])
    # Calculate query weights
    query_weights = {term : tfidf(term, terms_freq[term], no_docs, query_index) for term in unique_terms}
    docs_weights = compute_docs_weights(query_index, relevant_docs, no_docs)
    docs_len = {}
    with shelve.open(links_filename) as file:
        for key in file:
            docs_len[int(key)] = file[key][1]
    similarities={}
    for i,doc in enumerate(relevant_docs):
        similarities[doc]=cosineSimilarity(list(query_weights.values()),docs_weights[i],docs_len[doc])
    #Sort the documents by descending similarity
    #Turn dictionary into list of tuples (id,similarity)
    similarities = sorted(similarities.items(), key = lambda x : x[1], reverse=True)
    documents = [similarities[i][0] for i in range(len(similarities))]
    #Return at most max_results documents (IDs) ranked from best to worst
    return documents[:max_results]


    