import sys
try:
    import feedparser
except ImportError:
    print "Error: the FeedParser module could not be found"
    print "Download it fromhttp://code.google.com/p/feedparser/downloads/list and restart the application"
    sys.exit(raw_input()) # Quit when enter is pressed
import os
import shelve
import time

__version__='0.3'

def _open_file(filename,mode='r'):
    # Catch exceptions
    if not os.path.isfile(filename):
        raise IOError('File %s does not exist'%filename)
    try:
        return open(filename,mode)
    except Exception,e:
        print 'Error: %s'%e

class DigestReader:
    def __init__(self,filename='digests.txt'):
        self._file = _open_file(filename)

    def parse(self):
        # Parse through the file, ignoring //'s
        returner = {}
        _f = self._file
        for line in _f.readlines():
            if line.startswith('//'): continue
            if not line.strip(): continue
            name,url = line.split(':',1)
            returner[name] = url
        return returner

class DatReader:
    def __init__(self,filename='data.dat'):
        self._file = filename
        self._urls = None
    def parse_rss(self,urls):
        # Return a dict of URLS and their last update time
        # If its a new feed, update time = None
        d = shelve.open(self._file)
        returner = {}
        for i in urls:
            # If the URL of the feed is in the db:
            if urls[i] in d:
                # Read the timestamp from the last updated URl
                returner[i] = (urls[i],d[urls[i]])
            else:
                # Else write None as the timestamp
                returner[i] = (urls[i],None)
                d[urls[i]] = None
        d.close()
        self._urls = returner
        return returner
    def write_timestamp(self,url,timestamp):
        d = shelve.open(self._file)
        d[url] = timestamp
        d.close()

class Feed:
    # Individual class for each feed
    def __init__(self,url,old_time,name):
        self.url = url
        self.name = name
        self.timestamp = 0
        self.entries = 0
        self.old_time = old_time
        self.last_post = None
        self.last_author = None
        self._open()
        
    def _open(self):
        # Use feedparser to open the feed
        url = self.url
        _feed = feedparser.parse(url)
        if 'bozo_exception' in _feed:
            print 'Error in reading feed %s'%url
            self.timestamp = None
            self.entries = None
            return
        if len(_feed.entries)==0:
            print 'Error: No entries in feed %s'%url
            self.timestamp = None
            self.entries = 0
            return None
        _time = _feed.entries[0].updated_parsed
        self.timestamp = time.mktime(_time)
        self.entries = len(_feed.entries)
        self.last_post = _feed.entries[0]['title']
        if 'author_detail' in _feed.entries[0]:
            self.last_author = _feed.entries[0].author_detail.name
        else:
            self.last_authour = False

class FeedValidater:
    def __init__(self,urls):
        # Take all the urls and save them
        self._urls = urls
        
    def validate(self):
        returner = {}
        for i in self._urls:
            _t1 = time.time()
            print 'Opening %s'%i
            returner[i] = Feed(self._urls[i][0],self._urls[i][1],i)
            print '%s opened in %s seconds'%(i,str(round(time.time()-_t1,3)))
        return returner

    def check(self,feeds):
        returner = {}
        for name in feeds:
            # Take our Feed object and inspect its shit
            # We return a dict of the name, plus a tuple
            # containing either True or False, with some
            # extra info for the UI
            feed = feeds[name]
            if not feed.old_time == None:
                if feed.timestamp > feed.old_time:
                    new_post = True
                else:
                    new_post = False
            else:
                new_post = True
            # (New post?, entries, old_time, last_post,last_author,url)
            returner[name] = (new_post,feed.entries,feed.timestamp,feed.last_post,feed.last_author,feed.url)
        return returner     
            
def main():
    print 'Digest '+__version__
    print ': Parsing feeds :'
    # Load our feeds
    reader = DigestReader()
    urls = reader.parse()
    # Read our feed timestamps
    dreader = DatReader()
    timestamps = dreader.parse_rss(urls)
    # Create and validate our feeds
    validator = FeedValidater(timestamps)
    feeders = validator.validate()
    # Loop through our feeds and check them against our timestamp
    returned_urls = validator.check(feeders)
    #print returned_urls
    # Print the results
    os.system('cls')
    print 'Digest '+__version__+'\n'
    count=False
    for i in returned_urls:
        if returned_urls[i][0]:
            count=True
            # New post!
            print '------------------------------------------'
            print 'New post in feed %s'%i
            #print 'Details:'
            title = ' -Title : '+returned_urls[i][3]
            print title.encode('utf-8')
            #if returned_urls[i][4]:
            #    print ' -Poster: %s'%returned_urls[i][4]
            #print ' -Date  : %s'%time.ctime(returned_urls[i][2])
            dreader.write_timestamp(returned_urls[i][5],int(returned_urls[i][2]))
            print '------------------------------------------\n'
    if not count:
        print 'No feed updates today!'
    raw_input()

if __name__=='__main__':
    # Wait until we have a connection to the internet
    while True:
        if not os.system('ping www.google.com -n 1'):
            os.system(["clear","cls"][os.name == "nt"])
            break
        else:
            os.system(["clear","cls"][os.name == "nt"])
            time.sleep(2)
    main()
