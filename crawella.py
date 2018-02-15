import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import math
import aidkit as kit
from collections import Counter
import shelve
import pickle


''' HTML Parser '''
class Parser(HTMLParser):
            
    def __init__(self):
        HTMLParser.__init__(self)
        
    ''' Overloading method that is called when an opening tag is encountered (<) '''
    def handle_starttag(self, tag, attrs):
        # We look for links
        if tag == 'a':
            for (key, value) in attrs:
                if key == 'href': # We found a link
                    if (not value.startswith("#") and not value == 'javascript:;'):
                        # We avoid links to the current page (#) and links that are not links (javascript)
                        url = urljoin(self.baseUrl, value)
                        # We add it to our list of links:
                        self.links = self.links + [url]
                   
    ''' This method collects all outgoing links from the page indicated by 'url' '''
    def getTextAndLinks(self, url):
        #Initialize the list of links
        self.links=[]
        self.baseUrl = url # It will be used to construct absolute URLs from relative URLs 
        try:
            # Open the URL for parsing
            response = urllib.request.urlopen(url)
            # We are only interested in HTML
            if 'text/html' in response.getheader('Content-Type'):
                # Read the content
                htmlBytes = response.read()
                # Convert to necessary type
                htmlString = htmlBytes.decode("utf-8","ignore") # We ignore characters in other encodings such as cp1252
                #Feed the text to the parser.
                self.feed(htmlString)
                soup = BeautifulSoup(htmlString, 'html.parser')
                # Remove all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()          
                # Get text
                text = soup.get_text()                
                # Break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # Drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)            
                return text,self.links 
            else:
                return '',[]
        except Exception as ex:
            # Page not found, Access Forbidden, etc
            print("Exception: ",ex)
            return '',[]
    
# Process document by writing it's terms' frequency to disk and get its length    
def process_doc(doc_id, doc, terms_file):
        filtered_words = kit.filter_text(doc)
        # Find each term's frequency
        terms_freq = Counter(filtered_words)
        # Write pair (term, document id, frequency) to disk
        for term in terms_freq.keys():
            terms_file.write("{} {} {}\n".format(term, doc_id, terms_freq[term]))
        # Return the length of the document (sqrt of document frequency)
        return math.sqrt(len(filtered_words))
    
        
''' Link Crawler '''       
class Crawella():     
    
    # This method gathers links beginning from page startUrl and stops when at least maxLinks links have been collected
    # If maxLinks is not defined or maxLinks <= 0, then it stops when there are no more links (that have not already been crawled)
    def crawl(self,startUrl, tempfile, linkfile ,maxLinks = 0, lastID = 0):
        indexedURLs = 'files/indexedURLs.pkl'
        # Load the URLs that are already indexed in order to avoid re-indexing them
        try:
            with open(indexedURLs, 'rb') as f:
               links = pickle.load(f) 
        except (IOError, EOFError): 
            # File does not exist or is empty
            links = []
        toBeCrawled = set()
        toBeCrawled.add(startUrl)
        crawled = set()
        numVisited = 0
        numIndexed = 0
        # Open document links dictionary if it already exists or create a new one
        doc_links = shelve.open(linkfile, writeback=True)
        terms_file = open(tempfile, 'a')
        # Visit pages until there are no more pages to visit
        while len(toBeCrawled) > 0: 
            if (maxLinks > 0 and (numVisited >= maxLinks)):
                # We have processed maxLinks links
                print(maxLinks, " pages have been crawled.\n")
                break
            try:
                numVisited +=1
                parser = Parser()
                url = toBeCrawled.pop() # Get one of the links to be crawled
                print(numVisited)
                # Get the text and the links from the next in line url
                text, newLinks = parser.getTextAndLinks(url)
                if (len(text)==0): #An error occured (e.g. forbidden access), we continue with the next url
                    numVisited-=1
                    continue
                # Add the retrieved links to the set of links to be crawled
                for link in newLinks:
                    if link not in toBeCrawled and link not in crawled:
                        # We don't want to crawl the same page twice
                        toBeCrawled.add(link) 
                if url in links:
                    # The url has already been indexed so we continue with the next one
                    continue        
                numIndexed += 1
                # Process document for future use
                length = process_doc(lastID + numIndexed,text,terms_file)
                # Save document's necessary information (key must be string)
                doc_links[str(lastID + numIndexed)] = [url, length]
                crawled.add(url)
                links.append(url)
            except Exception as ex:
                print("Exception: ", ex)
                numVisited -=1
                continue
        doc_links.close()
        terms_file.close()
        with open(indexedURLs, 'wb') as f:
            # Save the URLs that were preprocessed in a file
            pickle.dump(links,f)
        return numIndexed