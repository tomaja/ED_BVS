
from publishers.FacebookPubMod import FacebookPub
from publishers.TelegramPubMod import TelegramPub
from publishers.ViberPubMod import ViberPub
from sources.ElektrodistribucijaMod import ElektrodistribucijaSrc
from sources.FileInputMod import FileInputSrc
import config_with_yaml as config
import sys

def PublishMessage(entry, publisher):
    publisher.Publish(entry)

if len(sys.argv) > 1:
    appConfig = config.load(sys.argv[1])
else:
    appConfig = config.load('config.yml')

allPublishers = []
if len(appConfig.getPropertyWithDefault('Publishers.Facebook', '')) > 0:
    allPublishers.append(FacebookPub(appConfig, 'fb_db.json'))
    
if len(appConfig.getPropertyWithDefault('Publishers.Telegram', '')) > 0:
    allPublishers.append(TelegramPub(appConfig, 'tg_db.json'))
    
if len(appConfig.getPropertyWithDefault('Publishers.Viber', '')) > 0:
    allPublishers.append(ViberPub(appConfig, 'vb_db.json'))

allSources = []
allSources.append(ElektrodistribucijaSrc(appConfig, 'http://www.elektrovojvodina.rs/sl/mediji/ED-Zrenjanin123'))
allSources.append(FileInputSrc(appConfig))

allMessages = []
for src in allSources:
    allMessages = allMessages + src.AcquireMessages()

for msg in allMessages:
    for pub in allPublishers:
        PublishMessage(msg, pub)
