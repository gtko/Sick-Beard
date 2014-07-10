# -*- coding: latin-1 -*-
# Author: Guillaume Serre <guillaume.serre@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from bs4 import BeautifulSoup
from sickbeard import logger, classes, show_name_helpers
from sickbeard.common import Quality
from sickbeard.exceptions import ex
import cookielib
import generic
import sickbeard
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



class TorrenthoundProvider(generic.TorrentProvider):

    def __init__(self):
        
        generic.TorrentProvider.__init__(self, "Torrenthound")

        self.supportsBacklog = True
        
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders=[('User-agent', 'Mozilla/5.0')]
        
        self.url = "http://www.torrenthound.com"
        
        
    def isEnabled(self):
        return sickbeard.Torrenthound

    def _get_season_search_strings(self, show, season):

        showNames = show_name_helpers.allPossibleShowNames(show)
        result = []
        for showName in showNames:
            result.append( showName + " S%02d" % season )
        return result

    def _get_episode_search_strings(self, ep_obj, french=None):

        strings = []

        showNames = show_name_helpers.allPossibleShowNames(ep_obj.show)
        for showName in showNames:
            strings.append("%s S%02dE%02d" % ( showName, ep_obj.scene_season, ep_obj.scene_episode) )
            strings.append("%s %dx%d" % ( showName, ep_obj.scene_season, ep_obj.scene_episode ) )

        return strings
    
    def _get_title_and_url(self, item):
        return (item.title, item.url)
    
    def getQuality(self, item):
        return item.getQuality()
        
    def _doSearch(self, searchString, show=None, season=None, french=None):

        print "Demarrage de la recherche"
        results = []
        searchOri = searchString
        listLang = [""]
        if(show.audio_lang == "fr") :
            listLang = ["french" , "truefrench" , "francais"]

        for lang in listLang :

            searchString = searchOri + " " + lang
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
                    title = str(link.text).lower().strip().encode('utf-8')
                    downloadTorrentLink = self.url + select(row , "div.sfloat a[title^=.torrent]")[0]["href"]
                    if "vostfr" in title and ((not show.subtitles) or show.audio_lang == "fr" or french):
                          continue
                    if(("french" in title or "truefrench" in title or "francais" in title) or show.audio_lang != "fr") :
                        print title + " " + downloadTorrentLink
                        if downloadTorrentLink:
                            downloadURL = downloadTorrentLink
                            if "720p" in title:
                                if "bluray" in title:
                                    quality = Quality.HDBLURAY
                                elif "web-dl" in title.lower() or "web.dl" in title.lower():
                                    quality = Quality.HDWEBDL
                                else:
                                    quality = Quality.HDTV
                            elif "1080p" in title:
                                quality = Quality.FULLHDBLURAY
                            elif "hdtv" in title:
                                if "720p" in title:
                                    quality = Quality.HDTV
                                elif "1080p" in title:
                                    quality = Quality.FULLHDTV
                                else:
                                    quality = Quality.SDTV
                            else:
                                quality = Quality.SDTV

                            if show and french==None:
                                results.append( TorrenthoundSearchResult( self.opener, title, downloadURL, quality, str(show.audio_lang) ) )
                            elif show and french:
                                results.append( TorrenthoundSearchResult( self.opener, title, downloadURL, quality, 'fr' ) )
                            else:
                                results.append( TorrenthoundSearchResult( self.opener, title, downloadURL, quality ) )

        return results
    
    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """
        result = classes.TorrentDataSearchResult(episodes)
        result.provider = self

        return result    
    
class TorrenthoundSearchResult:
    
    def __init__(self, opener, title, url, quality, audio_langs=None):
        self.opener = opener
        self.title = title
        self.url = url
        self.quality = quality
        self.audio_langs=audio_langs
        
    def getNZB(self):
        return self.opener.open( self.url , 'wb').read()

    def getQuality(self):
        return self.quality

provider = TorrenthoundProvider()
