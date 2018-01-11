import aidkit as kit
import math
from collections import Counter
import shelve

# Calculate the TFt value of the given term.
def tf(term, frequency):
    return 1 + math.log(frequency)

# Calculate the IDFt value of the given term.
def idf(term, no_docs, inverted_index):
    term_doc_freq = len(inverted_index[term])
    if term_doc_freq == 0:
        return 0
    else:
        # Filter negative values to zero
        return max(0, math.log(1 + (no_docs/term_doc_freq)))

# Calculate the weight of the value
def tfidf(term, frequency, no_docs, inverted_index):
    return tf(term, frequency) * idf(term, no_docs, inverted_index)

def cosineSimilarity(wq, wd, lq, ld):
    dot = sum(wq[i]*wd[i] for i in range(len(wq)))
    sim = dot/(lq*ld)
    return sim

# Executes a query based on the vector model and returns the document ids that match.
# max_results:  The maximum number of document ids to return.
def execute_query(query, inverted_index, links_filename, no_docs, max_results = 20, min_similarity = 0.6):
    #Remove punctuation 
    terms = kit.filter_text(query)
    unique_terms = set(terms)
    query_len = math.sqrt(len(unique_terms)) # approximate length of the query
    # Create an inverted index consisting of only query terms
    query_index = {}
    for term in unique_terms:
        query_index[term] = inverted_index.get_term_references(term)
    relatedDocs = set([query_index[term][i][0] for term in unique_terms for i in range(len(query_index[term]))])
    # Find each term's frequency
    terms_freq = Counter(terms)
    # Calculate query weights
    query_weights = [tfidf(term, terms_freq[term], no_docs, query_index) for term in unique_terms]
    #Calculate the weights for every related document
    docs_weights = [] 
    for doc in relatedDocs :
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
    docs_len = {}
    with shelve.open('links') as file:
        for key in file:
            docs_len[int(key)] = file[key][1]
    similarities={}
    for i,doc in enumerate(relatedDocs):
        similarities[doc]=cosineSimilarity(query_weights,docs_weights[i],query_len,docs_len[doc])
    #Sort the documents by descending similarity
    #Turn dictionary into list of tuples (id,similarity)
    similarities = sorted(similarities.items(), key = lambda x : x[1], reverse=True)
    documents = [similarities[i][0] for i in range(len(similarities))]
    #Return at most max_results documents ranked from best to worst
    return documents[:max_results]