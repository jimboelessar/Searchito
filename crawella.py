import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin
import pickle
import pathlib
from bs4 import BeautifulSoup
import math
import aidkit as kit
from collections import Counter
import shelve


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
                   
    
    def handle_data(self,data):
        self.data.append(data)
        
    
                    
    ''' This method collects all outgoing links from the page indicated by 'url' '''
    def getLinks(self, url):
        #Initialize the list of links
        self.links=[]
        self.data = []
        self.baseUrl = url # It will be used for links within the same page
        try:
            # Open the url for parsing
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
                #print(soup.get_text())
                #print(soup.findAll(text=True))
                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()    # rip it out
                
                # get text
                text = soup.get_text()
                
                # break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
            
                return text,self.links 
            else:
                return '',[]
        except Exception as ex:
            # Page not found, Access Forbidden, etc
            print("Exception: ",ex)
            return '',[]
        
def process_doc(doc_id, doc, temp_filename):
        # Open temporary file to append each term's frequency
        terms_file = open(temp_filename, 'a')
        # Open document and read it
        '''with open(doc_name, 'r') as doc_file:
            doc = doc_file.read()'''
        filtered_words = kit.filter_text(doc)
        # Find each term's frequency
        terms_freq = Counter(filtered_words)
        # Write pair (term, document id, frequency) to disk
        for term in terms_freq.keys():
            terms_file.write("{} {} {}\n".format(term, doc_id, terms_freq[term]))
        terms_file.close()
        # Return the length of the document (sqrt of document frequency)
        return math.sqrt(len(filtered_words))
        
''' Link Crawler '''       
class Crawella():
    
    def __init__(self):
        self.fromFile() # Load anything we may have crawled earlier        
    
    # This method gathers links beginning from page startUrl and stops when at least maxLinks links have been collected
    # If maxLinks is not defined or maxLinks <= 0, then it stops when there are no more links (that have not already been crawled)
    # If crawlAgain == true, then we crawl the given url even if it has been crawled before
    def crawl(self,startUrl, tempfile, linkfile ,maxLinks = 0, crawlAgain = False):
        numLinks = len(self.crawled)#+len(self.toBeCrawled) # In case of archived links
        if crawlAgain:
            # We don't care if this url has been crawled in the past
            self.toBeCrawled.add(startUrl)
        else:
            # We only add the given url if it hasn't been crawled before
            if startUrl not in self.crawled and startUrl not in self.toBeCrawled:
                self.toBeCrawled.add(startUrl) 
        numVisited = 0
        # Open document links dictionary if already exists or create a new one
        doc_links = shelve.open(linkfile, writeback=True)
        # Clear any previous data
        doc_links.clear()
        # Visit pages until there are no more pages to visit
        while len(self.toBeCrawled) > 0: 
            try:
                numVisited +=1
                parser = Parser()
                url = self.toBeCrawled.pop() # Get one of the links to be crawled
                print(numVisited, "Visiting:", url )
                # Get the text and the links from the next in line url
                text, newLinks = parser.getLinks(url)
                if (len(text)==0):
                    numVisited-=1
                    continue
                # Process document by writing it's terms frequency to disk and get it's length
                length = process_doc(numVisited,text,tempfile)
                # Save document's necessary information (key must be string)
                doc_links[str(numVisited)] = [url, length]
                self.crawled.add(url)
                # And add them to the set of links to be crawled
                for link in newLinks:
                    if link not in self.toBeCrawled and link not in self.crawled:
                        # We don't want to crawl the same link twice
                        self.toBeCrawled.add(link)            
            except Exception as ex:
                print("Exception: ", ex)
                numVisited -=1
            if (maxLinks > 0 and (len(self.crawled) >= (maxLinks+numLinks))):
                # We have gathered at least maxLinks links
                print("Success! At least ", maxLinks, " links have been crawled\n")
                break
        doc_links.close()
        if (maxLinks <= 0):
            print("No more links to fetch!\n")  
        # We combine all the links we have gathered in a dictionary, so that every link has a unique id
        self.links = {key: value for key,value in enumerate(self.crawled.union(self.toBeCrawled))}
        self.toFile()
        return numVisited
        
    ''' Save crawled and toBeCrawled  links to disk for possible later use '''
    def toFile(self):
        with open('files/crawled.pkl', 'wb') as f:
            pickle.dump(self.crawled,f)
        with open('files/toBeCrawled.pkl', 'wb') as f:
            pickle.dump(self.toBeCrawled,f)
        with open('files/linksWithIDs.pkl', 'wb') as f:
            pickle.dump(self.links,f)
       
    ''' Load previously crawled and fetched links '''
    def fromFile(self):
        pathlib.Path('files').mkdir(parents=True, exist_ok=True) # If the folder 'files' does not exist, we create it
        try:
            with open('files/crawled.pkl', 'rb') as f:
               self.crawled = pickle.load(f) # A set containing all the links that have been crawled
        except (IOError, EOFError): 
            # File does not exist or is empty
                self.crawled = set() 
        try:
            with open('files/toBeCrawled.pkl', 'rb') as f:
                self.toBeCrawled = pickle.load(f) # A set of links to be crawled
        except (IOError, EOFError):
            # File does not exist or is empty
            self.toBeCrawled = set() 
            
# Examples
#crawler = Crawella()
#crawler.crawl('https://www.quora.com/How-can-I-extract-only-text-data-from-HTML-pages','temp_terms','links',12)
# Does not crawl the same page twice, instead it crawls one of the archived links (from toBeCrawled.pkl)
#crawler.crawl("https://en.wikipedia.org/wiki/Cruella_de_Ville")
