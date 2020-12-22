from message import Message
import urllib.request
from bs4 import BeautifulSoup

class ElektrodistribucijaSrc:
    def __init__(self, appConfig, url = '') -> None:
        self.url = url
        self.cities = appConfig.getProperty('Sources.ED.Cities')
        print("Elektrodistribucija source created for: " , repr(appConfig.getProperty('Sources.ED.Cities')))

    def StartsWithSl(self, href_string):
        return href_string.startswith('/sl')

    def GetDateLinks(self):
        with urllib.request.urlopen(self.url) as fp:
            self.soupMainPage = BeautifulSoup(fp, 'html.parser')
        linkEls = self.soupMainPage.find('div', class_ = 'content_body_left').find_all("a", href=self.StartsWithSl)
        links = []
        for linkEl in linkEls:
            links.append('http://www.elektrovojvodina.rs' + linkEl.attrs['href'])
        return links

    def GetMessage(self, link):        
        with urllib.request.urlopen(link) as fp:
            bs = BeautifulSoup(fp, 'html.parser')
        tbody = bs.find('div', class_ = 'content_body_left').tbody
        trs = tbody.find_all('tr')
        message = {}
        message['desc'] = []
        for tr in trs:
            if len(message) == 1:
                message['common_desc'] = tr.text
            else:
                for city in self.cities:
                    cityLowercase = tr.text.lower()
                    if city.lower() in cityLowercase:
                        message['desc'].append(tr.text)
        if len(message['desc']) > 0:
            message['url'] = link
            return message
        else:
            return {}


    def GetRelevantMessages(self):
        links = self.GetDateLinks()
        rawMessages = []
        for link in links:
            msg = self.GetMessage(link)
            if len(msg) > 1:
                rawMessages.append(msg)
        rawMessages.reverse()
        return rawMessages

    def AcquireMessages(self):
        messages = []
        message = Message()
        message.message = self.GetRelevantMessages()
        message.hash = message.Hash()
        messages.append(message)
        return messages
