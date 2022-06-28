from bs4 import BeautifulSoup
import re
import urllib.request
from multiprocessing import Queue
import threading

q = None
d = None
threads = None
rate_limit = 10
max_depth = 5
base_domain = None
stop_url = None
searchedFlag = False
patternWiki = '/wiki/[^:?]*$'
patternDomain = 'http(s)?://[^/]*'

class NodePage:
    url = ""
    parent = None
    depth = 0

def parsePage(url, depth):
    bingo = False
    if depth > max_depth:
        return
    page = urllib.request.urlopen(base_domain + url)
    contents = page.read()
    soup = BeautifulSoup(contents, 'lxml')
    main_body = soup.find("div", id="mw-content-text")

    for a_tag in main_body.find_all("a", attrs = {'href' : True, 'class' : False}):
        if re.search(patternWiki, a_tag['href']):
            node = NodePage()
            node.url = a_tag['href']
            node.parent = url
            node.depth = depth + 1

            if a_tag['href'] in d:
                if a_tag['href'] != stop_url:
                    continue
            else:
                q.put(node)
            d[node.url] = node
            #print(node.url, node.depth)

            if a_tag['href'] == stop_url and not bingo:
                searchedFlag = True
                bingo = True
                chain = a_tag['href']
                root = a_tag['href']
                while d[root].parent is not None:
                    root = d[root].parent
                    chain = d[root].url + ' => ' + chain
                print('bingo: ', chain)

def SearchWorker():
    while q.qsize() > 0:
        firstOut = q.get()
        parsePage(firstOut.url, firstOut.depth)

def StartWork(url1, url2):
    global q, d, threads, stop_url
    q = Queue()
    d = {}
    threads = []
    stop_url = url1
    root = NodePage()
    root.url = url2
    d[root.url] = root
    parsePage(root.url, root.depth)

    for i in range(rate_limit):
        t = threading.Thread(target=SearchWorker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if not searchedFlag:
        print('Not found chain: ', url2 , ' => ', url1)

if __name__ == '__main__':
    link1 = input('Input first link: \n')
    domain = re.search(patternDomain, link1)
    if domain:
        base_domain = domain[0]
    link2 = input('Input second link: \n')
    domain = re.search(patternDomain, link2)
    if domain:
        if base_domain != domain[0]:
            print("Different language!!!")

    rate_limit = int(input('Input rate limit: \n'))
    StartWork(re.search(patternWiki, link2)[0], re.search(patternWiki, link1)[0])
    StartWork(re.search(patternWiki, link1)[0], re.search(patternWiki, link2)[0])
