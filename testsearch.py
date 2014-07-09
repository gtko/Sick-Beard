from bs4 import BeautifulSoup
import cookielib
import urllib
import urllib2




class SmartorrentProvider:

    def __init__(self):
        self.supportsBacklog = True
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders=[('User-agent', 'Mozilla/5.0')]
        self.url = "http://smartorrent.com"

    def _doSearch(self, searchString):

        print "Demarrage de la recherche"
        results = []

        data = urllib.urlencode({'page':u'search','term':searchString.replace('!','')})
        searchUrl = self.url + '/?%s'%data
        req = urllib2.urlopen(searchUrl,data)

        try:
            soup = BeautifulSoup(req)
        except Exception, e:
            print "C'est la merde" + e.message
            return []

        rows = soup.findAll("td" , attrs={"class":u"nom"})

        for row in rows:
            link = row.findAll("a")[1]
            title = str(link.text).lower().strip()
            pageURL = link['href']

            if "vostfr" in title and ((not show.subtitles) or show.audio_lang == "fr" or french):
                continue

            print title + u" " + pageURL + "\n"

            torrentPage = urllib2.urlopen(pageURL)
            torrentSoup = BeautifulSoup(torrentPage)
            downloadTorrentLink = torrentSoup.find("a", attrs={"class":u'telechargergreen'})["href"]
            print downloadTorrentLink

        print "Resultat des recherche"



provider = SmartorrentProvider()
provider._doSearch(u"Grimm 3x13")
