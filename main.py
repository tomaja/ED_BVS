
from publishers.FacebookPubMod import FacebookPub
from sources.ElektrodistribucijaMod import ElektrodistribucijaSrc
import config_with_yaml as config

def PublishMessage(entry, publisher):
    publisher.Publish(entry)

appConfig = config.load('config.yml')
allPublishers = []
allPublishers.append(FacebookPub(appConfig, 'fb_db.json'))

allSources = []
allSources.append(ElektrodistribucijaSrc(appConfig, 'http://www.elektrovojvodina.rs/sl/mediji/ED-Zrenjanin123'))

allMessages = []
for src in allSources:
    allMessages = allMessages + src.AcquireMessages()

for msg in allMessages:
    for pub in allPublishers:
        PublishMessage(msg, pub)
