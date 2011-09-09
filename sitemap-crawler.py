"""
    AUTHOR: Darren Nix
    Version: 0.1
    Date:    2011-9-7
    Site: www.darrennix.com

    Crawls a site to find unique page URLs and returns them as a list.
    Ignores query strings, badly formed URLs, and links to domains
    outside of the starting domain.

    DEPENDENCIES:
    BeautifulSoup HTML parsing library

"""
import urllib2
import urlparse
from BeautifulSoup import BeautifulSoup

class Sitemapper():
        
    def main(self, start_url, block_extensions=['.pdf'], max_urls = 100):

        # Set user agent string
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib2.install_opener(opener)

        # Get base info
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(start_url)
        fragments = (scheme, netloc, '', '', '', '')
        base_url = urlparse.urlunparse(fragments)

        # Start processing
        print "Crawling the site... %s" % base_url
        urls_crawled = self.parse_pages(base_url, max_urls, block_extensions)

        return urls_crawled


    def parse_pages(self, base_url, max_urls, block_extensions):

        urls_queue = []
        urls_crawled = []
        urls_queue.append(base_url)


        # Keep looping over each page as long as there's one to parse
        counter=0
        while len(urls_queue):
            # Safety check to prevent infinite loop
            counter += 1
            if counter > max_urls:
                break

            # Get the page contents
            url = urls_queue.pop()
            try:
                print "READ: %s" % url
                f = urllib2.urlopen(url)
                page = f.read()
                f.close()
                urls_crawled.append(url)
            except (urllib2.URLError, urllib2.HTTPError), detail:
                # Skip this node
                print "ERROR %s" % detail
                continue

            # Soup it and find links
            soup = BeautifulSoup(''.join(page))
            links = soup.findAll('a')

            # Loop through all the links on the page
            for link in links:

                # Ignore A tags without HREFs
                try:
                    partial_link_url = str(link['href'])
                except KeyError:
                    continue

                # Concatenate relative urls like "../joing.html" with currently being processed url
                link_url = urlparse.urljoin(url, partial_link_url)

                # Strip off any trailing jibberish like ?test=1
                (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(link_url)
                fragments = (scheme, netloc, path, '', '', '')
                link_url = urlparse.urlunparse(fragments)

                # Make sure we're still on the same domain
                (base_scheme, base_netloc, base_path, base_params, base_query, base_fragment) = urlparse.urlparse(url)

                # Skip some file types
                blocked = False
                for blocked_extension in block_extensions:
                    extension_length = len(blocked_extension)
                    url_extension = path[-extension_length:]
                    if url_extension == blocked_extension:
                        blocked = True
                    

                if netloc != base_netloc:
                    # Different domain
                    pass
                elif link_url in urls_queue or link_url in urls_crawled:
                    # already in list
                    pass
                elif blocked:
                    # bad extension
                    pass
                else:
                    urls_queue.append(link_url)

        return urls_crawled