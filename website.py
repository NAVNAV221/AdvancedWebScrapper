from concurrent.futures.thread import ThreadPoolExecutor
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, SoupStrainer
import requests
import colorama
import cfscrape


CLEAR = 0
VISITED = 0

colorama.init()
YELLOW = colorama.Fore.YELLOW
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
RED = colorama.Fore.RED


class Website:
    def __init__(self, url, pattern):
        self.url = url
        self.pattern = pattern
        self.location = 0
        self.matches = 0
        self.headers = {"scheme": "https",
                        "accept": "text/html,application/xhtml+xml",
                        "accept-encoding": "gzip, deflate, br",
                        "accept-language": "en-US,en;q=0.9",
                        "cache-control": "no-cache",
                        "dnt": "1",
                        "pragma": "no-cache",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-site": "same-origin",
                        "sec-fetch-user": "?1",
                        "upgrade-insecure-requests": "1",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64)"}
        self.internal_objects = self.__grab_object_links()
        self.tree = None

    def __fix_to_absolute(self, attr):
        '''
        1. Whether we have an href (or src) attribute without an absolute path such: /we-content/foo
           we need to fix it by adding the website's url.
        2. Also, we need to consider the fact that sometimes urls comes with params: https://foo.com/foo?boo=com.
           So we need to fix it to: https://foo.com/foo.
        All this done to not cause redundancy in the url set.
        '''
        attr = urljoin(self.url, attr)

        parsed_attr = urlparse(attr)
        attr = parsed_attr.scheme + '://' + parsed_attr.netloc + parsed_attr.path
        return attr

    def __is_valid_url(self, link):  # TODO: Check if url is the base url
        return bool(urlparse(link).netloc) and bool(urlparse(link).scheme) and (
            not link.endswith(('ico', 'gif', 'svg')))

    def __grab_object_links(self):
        print(f"{GREEN}-------- START PROCESS ON URL: {self.url} --------{RESET}")
        object_domain = urlparse(self.url).netloc
        internal_links = set()
        external_links = set()

        response = requests.get(self.url, headers=self.headers)
        unfiltered_links = []

        for link in BeautifulSoup(response.content, parse_only=SoupStrainer('a'), features='html.parser'):
            if link.has_attr('href'):
                unfiltered_links.append(link['href'])

        for link in unfiltered_links:
            link = self.__fix_to_absolute(link)

            if not self.__is_valid_url(link):
                print(f"{RED}[DELETED] {RESET}{link} {RED}URL isn't valid")
                continue
            # the object already in the internal objects
            if link in internal_links:
                print(f"{RED}[DELETED] {RESET}{link} {RED}already in internal")
                continue
            # external objects
            if object_domain not in link:
                if link not in internal_links:
                    print(f"{GRAY}[!] External link: {link}")
                    external_links.add(link)
                continue
            internal_links.add(link)

        if self.url in internal_links:
            internal_links.remove(self.url)

        print(f"{YELLOW}[+] CLEARED URLS: {len(unfiltered_links) - (len(internal_links) + len(external_links))}")
        print(f"{YELLOW}[+] TOTAL URLS: {len(internal_links) + len(external_links)}")
        print(f"{YELLOW}[+] INTERNAL URLS: {len(internal_links)}")
        print(f"{YELLOW}[+] EXTERNAL URLS: {len(external_links)}{RESET}")
        print(f"{GREEN}-------- PROCESS ON URL: {self.url} FINISHED --------{RESET}")
        return internal_links

    def _scrape(self, website=None):
        scraper = cfscrape.create_scraper()
        response = scraper.get(website.url, headers=self.headers).text
        matches = len(re.findall(self.pattern, response))
        website.matches = matches

    # BFS Algorithm
    def crawl_url_by_depth(self, depth):
        if depth == 0:
            self._scrape(self)
            return
        else:
            print(f"---------------------ROOT URL: {self.url} ---------------------")

            location = self.location
            self.tree = [self]
            queue = [self]

            for j in range(depth):
                for count in range(len(queue)):
                    url = queue.pop(0)
                    # print(f"URL: {url}")
                    urls = url.internal_objects
                    # print(f"URLs: {urls}")
                    for i in urls:
                        location += 1
                        child = Website(i, self.pattern)
                        child.location = location
                        self.tree.append(child)
                        queue.append(child)

            # for i in childrens:
            #     print(i.url)

            # all_urls = [self.url]
            # queue = [self.url]
            # for j in range(depth):
            #     for count in range(len(queue)):
            #         url = queue.pop(0)
            #         urls = self.__grab_object_links(url)
            #         for i in urls:
            #             all_urls.append(i)
            #             queue.append(i)

                    # url = queue.pop(0)
                    # urls = url.__grab_object_links()
                    # for i in urls:
                    #     child = Website(i, self.pattern)
                    #     self.childrens.append(child)
                    #     queue.append(i)

        threads = min(30, len(self.tree))
        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self._scrape, self.tree)
        return self.tree, self._show_tree()

    def _show_tree(self):
        for obj in self.tree:
            print(obj)

    def __str__(self):
        return f"[+] WEBSITE OBJECT\n{YELLOW}NAME: {self.url}\nCHILDRENS: {self.internal_objects}\nMATCHES OF PATTERN {self.matches}\nLOCATION ON TREE:{self.location}{RESET}"