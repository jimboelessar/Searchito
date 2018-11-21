import aidkit as kit
import boolean

class ExpressionTree(object):
    def __init__(self):
        self.children = []
        self.operator = None
        self.term = None
        self.is_term = False
    
    # Calculates the expression it holds.
    # inverted_index:   Contains the references of all terms inside the expression.
    def evaluate(self, inverted_index):
        if self.is_term:
            # If expression is a term, return the references of the term from the
            # inverted index.
            return inverted_index[self.term]
        elif self.operator == '~':
            # If the expression is a NOT operator, just  return the documents of the
            # only child. Parent will handle it.
            return self.children[0].evaluate(inverted_index)
        else:
            children_docs = []
            children_NOT_docs = []
            # Find the documents of every child and seperate those that are from the NOT
            # operator.
            for child in self.children:
                docs = child.evaluate(inverted_index)
                if child.operator == '~':
                    children_NOT_docs.append(docs)
                else:
                    children_docs.append(docs)
            # Expressions must have at least one child that is not a NOT operator.
            # Otherwise no operation is executed.
            if len(children_docs) == 0:
                return set()
            result = children_docs[0]
            if self.operator == '|':
                # If the expression is an OR operator, union the docs of children.
                # NOT operator in children is not allowed and will be ignored.
                for docs in children_docs[1:]:
                    result = result.union(docs)
            else:
                # If the expression is an AND operator, intersect the docs of children
                # and substruct documents of children with NOT operator.
                for docs in children_docs[1:]:
                    result = result.intersection(docs)
                for docs in children_NOT_docs:
                    result = result - docs
            return result


    # Recreates the expression it holds in string format (for testing purposes).
    def print(self):
        if self.is_term:
            return self.term
        elif self.operator == '|' or self.operator == '&':
            text = '('
            for child in self.children:
                text += child.print() + self.operator
            text = text[:-1]
            text += ')'
            return text
        else:
            return self.operator  + self.children[0].print()


# Executes a query based on the boolean model and returns the documents' ids that match.
# max_results:  The maximum number of documents' ids to return.
def execute_query(query, max_results, inverted_index):
    # Remove punctuations that are not allowed
    filtered_query = kit.filter_boolean_expression(query)

    # Try to parse the logical expression or return no documents' id
    algebra = boolean.BooleanAlgebra()
    try:
        expression = algebra.parse(filtered_query)
    except Exception:
        return []

    # Filter all terms inside the query
    symbols = expression.symbols
    filtered_terms = [kit.filter_text(item.obj)[0] for item in symbols]

    # Create a small inverted index of the terms with only documents id (not frequency)
    query_index = {}
    for term in filtered_terms:
        ref_docs = set(ref[0] for ref in inverted_index.get_term_references(term))
        query_index[term] = ref_docs

    # Create a tree of the expression and find the documents
    tree = create_expression_tree(expression)
    documents = tree.evaluate(query_index)
    # Reduce documents to the maximum allowed number (if there are more)
    if len(documents) > max_results:
        documents = list(documents)[:max_results]
    return documents

# Creates and returns a tree of the given expression. 
# Executing tree operators in inorder gives the same result as the expression.
def create_expression_tree(expression):
    tree = ExpressionTree()
    initialize_node(expression, tree)
    return tree

# Initializes the given node based on the given expression.
def initialize_node(expression, node):
    # If expression is a literal, save the filtered term
    if isinstance(expression, boolean.boolean.Symbol):
        node.is_term = True
        node.term = kit.filter_text(expression.obj)[0]
    else:
        # If expression is an operator, initialize it's children
        node.operator = expression.operator
        for exp in expression.args:
            child = ExpressionTree()
            initialize_node(exp, child)
            node.children.append(child)