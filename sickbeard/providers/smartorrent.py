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


class SmartorrentProvider(generic.TorrentProvider):

    def __init__(self):
        
        generic.TorrentProvider.__init__(self, "Smartorrent")

        self.supportsBacklog = True
        
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders=[('User-agent', 'Mozilla/5.0')]
        
        self.url = "http://smartorrent.com"
        
        
    def isEnabled(self):
        return sickbeard.Smartorrent

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

        results = []
        data = urllib.urlencode({'page':u'search','term':searchString.replace('!','')})
        searchUrl = self.url + '/?%s'%data
        req = urllib2.urlopen(searchUrl,data)

        try:
            soup = BeautifulSoup(req)
        except Exception, e:
            logger.log(u"C'est la merde , ça ne response pas ! : "+str(e), logger.ERROR)
            return []

        rows = soup.findAll("td" , attrs={"class":u"nom"})
        for row in rows:
            link = row.findAll("a")[1]
            title = str(link.text).lower().strip()
            pageURL = link['href']

            if "vostfr" in title and ((not show.subtitles) or show.audio_lang == "fr" or french):
                continue

            torrentPage = urllib2.urlopen(pageURL)
            torrentSoup = BeautifulSoup(torrentPage)
            downloadTorrentLink = torrentSoup.find("a", attrs={"class":u'telechargergreen'})["href"]
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
                    results.append( SmartorrentSearchResult( self.opener, title, downloadURL, quality, str(show.audio_lang) ) )
                elif show and french:
                    results.append( SmartorrentSearchResult( self.opener, title, downloadURL, quality, 'fr' ) )
                else:
                    results.append( SmartorrentSearchResult( self.opener, title, downloadURL, quality ) )

        return results
    
    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """
        result = classes.TorrentDataSearchResult(episodes)
        result.provider = self

        return result    
    
class SmartorrentSearchResult:
    
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

provider = SmartorrentProvider()
