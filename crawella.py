import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin
import pickle
import pathlib


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
    def getLinks(self, url):
        #Initialize the list of links
        self.links=[]
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
                return self.links #mporoume na epistrefoume kai to htmlString an to xreiazomaste meta
            else:
                return []
        except Exception as ex:
            # Page not found, Access Forbidden, etc
            print("Exception: ",ex)
            return []
        
''' Link Crawler '''       
class Crawella():
    
    def __init__(self):
        self.fromFile() # Load anything we may have crawled earlier        
    
    # This method gathers links beginning from page startUrl and stops when at least maxLinks links have been collected
    # If maxLinks is not defined or maxLinks <= 0, then it stops when there are no more links (that have not already been crawled)
    # If crawlAgain == true, then we crawl the given url even if it has been crawled before
    def crawl(self,startUrl, maxLinks = 0, crawlAgain = False):
        numLinks = len(self.crawled)+len(self.toBeCrawled) # In case of archived links
        if crawlAgain:
            # We don't care if this url has been crawled in the past
            self.toBeCrawled.add(startUrl)
        else:
            # We only add the given url if it hasn't been crawled before
            if startUrl not in self.crawled and startUrl not in self.toBeCrawled:
                self.toBeCrawled.add(startUrl) 
        numVisited = 0
        # Visit pages until there are no more pages to visit
        while len(self.toBeCrawled) > 0: 
            try:
                parser = Parser()
                url = self.toBeCrawled.pop() # Get one of the links to be crawled
                numVisited +=1
                print(numVisited, "Visiting:", url )
                # Get the links from the next in line url
                newLinks = parser.getLinks(url)
                self.crawled.add(url)
                # And add them to the set of links to be crawled
                for link in newLinks:
                    if link not in self.toBeCrawled and link not in self.crawled:
                        # We don't want to crawl the same link twice
                        self.toBeCrawled.add(link)            
            except Exception as ex:
                print("Exception: ", ex)
            if (maxLinks > 0 and (len(self.crawled)+len(self.toBeCrawled)) >= (maxLinks+numLinks)):
                # We have gathered at least maxLinks links
                print("Success! At least ", maxLinks, " links have been fetched\n")
                break
        if (maxLinks <= 0):
            print("No more links to fetch!\n")  
        # We combine all the links we have gathered in a dictionary, so that every link has a unique id
        self.links = {key: value for key,value in enumerate(self.crawled.union(self.toBeCrawled))}
        self.toFile()
        
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
crawler = Crawella()
crawler.crawl('https://en.wikipedia.org/wiki/Cruella_de_Ville',1000)
# Does not crawl the same page twice, instead it crawls one of the archived links (from toBeCrawled.pkl)
crawler.crawl("https://en.wikipedia.org/wiki/Cruella_de_Ville")
