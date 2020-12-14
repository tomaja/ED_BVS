from message import Message
import urllib.request
from bs4 import BeautifulSoup

class ElektrodistribucijaSrc:
    def __init__(self, appConfig, url = '') -> None:
        self.url = url
        self.city = appConfig.getProperty('Sources.ED.City').lower()
        self.cities = appConfig.getProperty('Sources.ED.Cities')
        print("Elektrodistribucija source created for: " , repr(appConfig.getProperty('Sources.ED.Cities')))

    def StartsWithSl(self, href_string):
        return href_string.startswith('/sl')

    def GetDateLinks(self):
        with urllib.request.urlopen(self.url) as fp:
            self.soupMainPage = BeautifulSoup(fp, 'lxml')
        linkEls = self.soupMainPage.find('div', class_ = 'content_body_left').find_all("a", href=self.StartsWithSl)
        links = []
        for linkEl in linkEls:
            links.append('http://www.elektrovojvodina.rs' + linkEl.attrs['href'])
        return links

    def GetMessage(self, link):        
        with urllib.request.urlopen(link) as fp:
            bs = BeautifulSoup(fp, 'lxml')
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
            return message
        else:
            return {}


    def Prettify(self, rawMessages):
        res = 'Automatsko obaveštenje o nestanku struje u selu i okolini:\n\n'
        for rawMessage in rawMessages:
            res = res + rawMessage['common_desc'] + '\n'
            for rawMessageDesc in rawMessage['desc']:
                pretty = ' '.join(rawMessageDesc.split('\\n'))
                pretty = ' '.join(pretty.split('\\t'))
                pretty = ' '.join(pretty.split('\n'))
                pretty = ' '.join(pretty.split('\t'))
                pretty = ' '.join(pretty.split(' '))
                res = res + pretty + '\n'
            res = res + '\n'
        return res

    def GetRelevantMessages(self):
        links = self.GetDateLinks()
        rawMessages = []
        for link in links:
            msg = self.GetMessage(link)
            if len(msg) > 1:
                rawMessages.append(msg)
        return self.Prettify(rawMessages)

    def AcquireMessages(self):

        messages = []
        message = Message()
        message.message = self.GetRelevantMessages()
        message.hash = message.Hash()
        messages.append(message)
        return messages
