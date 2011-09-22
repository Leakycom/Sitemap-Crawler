"""
    AUTHOR: Darren Nix
    Version: 0.1
    Date:    2011-9-7
    Site: www.darrennix.com
    License: Apache 2.0

    Crawls a site to find unique page URLs and returns them as a list.
    Ignores query strings, badly formed URLs, and links to domains
    outside of the starting domain.
    
    Inspired by sitemap_gen from Valdimir Toncar


    DEPENDENCIES:
    BeautifulSoup HTML parsing library
    Eventlet

"""
import urlparse
from BeautifulSoup import BeautifulSoup
import eventlet
from eventlet.green import urllib2

class Sitemapper():

    def main(self, start_url, block_extensions=['.pdf'], max_urls = 100):

		# Set user agent string
		opener = urllib2.build_opener()
		opener.addheaders = [
			('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'),
			('Accept-Encoding', 'gzip,deflate,sdch'),
			('Accept-Language', 'en-US,en;q=0.8'),
			('Cache-Control', 'max-age=0'),
			('Connection', 'keep-alive')
		]
		urllib2.install_opener(opener)

		# Get base info
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(start_url)
		fragments = (scheme, netloc, '', '', '', '')
		base_url = urlparse.urlunparse(fragments)

		urls_queue = set([base_url])
		urls_crawled = set()

		pool = eventlet.GreenPool(20)

		counter = 0
		while True:
			#Infinite loop sanity check
			counter +=1
			if counter > max_urls:
				break

			for url, body in pool.imap(self.fetch, urls_queue):
				# Remove this url from the queue set
				urls_queue = urls_queue - set([url])

				# Add url to crawled set
				urls_crawled = urls_crawled.union(set([url]))

				# Extract links
				links = self.extract_links(url, body, block_extensions)
				for link in links:
					if link not in urls_queue and link not in urls_crawled:
						# Add link to queue
						urls_queue = urls_queue.union(set([link]))

		return urls_crawled

	def fetch(self, url):
		print "opening", url

		try:
			body = urllib2.urlopen(url).read()
			return url, body
		except (urllib2.URLError, urllib2.HTTPError), detail:
			# Skip this node
			print "ERROR %s" % detail
			return url, False

	def extract_links(self, url, body, block_extensions):
		# Soup it and find links
		soup = BeautifulSoup(''.join(body))
		links = soup.findAll('a')

		good_links = []
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
			elif blocked:
				# bad extension
				pass
			else:
				# Add this link to the list
				good_links.append(link_url)

		return good_links