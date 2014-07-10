from bs4 import BeautifulSoup
import cookielib
import urllib
import urllib2

"""
soupselect.py
CSS selector support for BeautifulSoup.
soup = BeautifulSoup('<html>...')
select(soup, 'div')
- returns a list of div elements
select(soup, 'div#main ul a')
- returns a list of links inside a ul inside div#main
"""

import re

tag_re = re.compile('^[a-z0-9]+$')

attribselect_re = re.compile(
    r'^(?P<tag>\w+)?\[(?P<attribute>\w+)(?P<operator>[=~\|\^\$\*]?)' +
    r'=?"?(?P<value>[^\]"]*)"?\]$'
)

# /^(\w+)\[(\w+)([=~\|\^\$\*]?)=?"?([^\]"]*)"?\]$/
#   \---/  \---/\-------------/    \-------/
#     |      |         |               |
#     |      |         |           The value
#     |      |    ~,|,^,$,* or =
#     |   Attribute
#    Tag

def attribute_checker(operator, attribute, value=''):
    """
    Takes an operator, attribute and optional value; returns a function that
    will return True for elements that match that combination.
    """
    return {
        '=': lambda el: el.get(attribute) == value,
        # attribute includes value as one of a set of space separated tokens
        '~': lambda el: value in el.get(attribute, '').split(),
        # attribute starts with value
        '^': lambda el: el.get(attribute, '').startswith(value),
        # attribute ends with value
        '$': lambda el: el.get(attribute, '').endswith(value),
        # attribute contains value
        '*': lambda el: value in el.get(attribute, ''),
        # attribute is either exactly value or starts with value-
        '|': lambda el: el.get(attribute, '') == value \
            or el.get(attribute, '').startswith('%s-' % value),
    }.get(operator, lambda el: el.has_key(attribute))


def select(soup, selector):
    """
    soup should be a BeautifulSoup instance; selector is a CSS selector
    specifying the elements you want to retrieve.
    """
    tokens = selector.split()
    current_context = [soup]
    for token in tokens:
        m = attribselect_re.match(token)
        if m:
            # Attribute selector
            tag, attribute, operator, value = m.groups()
            if not tag:
                tag = True
            checker = attribute_checker(operator, attribute, value)
            found = []
            for context in current_context:
                found.extend([el for el in context.findAll(tag) if checker(el)])
            current_context = found
            continue
        if '#' in token:
            # ID selector
            tag, id = token.split('#', 1)
            if not tag:
                tag = True
            el = current_context[0].find(tag, {'id': id})
            if not el:
                return [] # No match
            current_context = [el]
            continue
        if '.' in token:
            # Class selector
            tag, klass = token.split('.', 1)
            if not tag:
                tag = True
            found = []
            for context in current_context:
                found.extend(
                    context.findAll(tag,
                        {'class': lambda attr: attr and klass in attr.split()}
                    )
                )
            current_context = found
            continue
        if token == '*':
            # Star selector
            found = []
            for context in current_context:
                found.extend(context.findAll(True))
            current_context = found
            continue
        # Here we should just have a regular tag
        if not tag_re.match(token):
            return []
        found = []
        for context in current_context:
            found.extend(context.findAll(token))
        current_context = found
    return current_context

def monkeypatch(BeautifulSoupClass=None):
    """
    If you don't explicitly state the class to patch, defaults to the most
    common import location for BeautifulSoup.
    """
    if not BeautifulSoupClass:
        from BeautifulSoup import BeautifulSoup as BeautifulSoupClass
    BeautifulSoupClass.findSelect = select

def unmonkeypatch(BeautifulSoupClass=None):
    if not BeautifulSoupClass:
        from BeautifulSoup import BeautifulSoup as BeautifulSoupClass
    delattr(BeautifulSoupClass, 'findSelect')



class SmartorrentProvider:

    def __init__(self):
        self.supportsBacklog = True
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders=[('User-agent', 'Mozilla/5.0')]
        self.url = "http://www.torrenthound.com"

    def _doSearch(self, searchString):

        print "Demarrage de la recherche"
        results = []

        listLang = [""]
        if(True) :
            listLang = ["french" , "truefrench" , "franais" , "francais"]

        for lang in listLang :

            searchString += " " + lang
            data = urllib.urlencode({"search" : searchString.replace('!','')})
            searchUrl = self.url + '/%s' %data.replace("=" , "/")
            print searchUrl

            try:
                req = self.opener.open(searchUrl)
                soup = BeautifulSoup(req)
            except Exception, e:
                print "c est la merde"+str(e)
                return []
            rows = select(soup , "table.searchtable td")
            for row in rows:
                link = select(row , "a[href^=/hash]")
                if (len(link) > 0) :
                    link = link[0]
                    extract = [s.extract() for s in select(link , ".cat")]
                    title = str(link.text.encode("utf-8" , "ignore")).lower().strip().encode("utf-8" , "ignore")
                    if("french" in title or "truefrench" in title or "francais" in title) :
                        downloadTorrentLink = self.url + select(row , "div.sfloat a[title^=.torrent]")[0]["href"]
                        print title + " " +downloadTorrentLink
                # if "vostfr" in title and ((not show.subtitles) or show.audio_lang == "fr" or french):
                  #      continue

            print "Resultat des recherche"

provider = SmartorrentProvider()
provider._doSearch("Grimm S02E15")
