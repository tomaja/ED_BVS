  
from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from viberbot.api.event_type import EventType
from tinydb import TinyDB, Query
import re

import time
import logging
import sched
import threading

class ViberPub:
    def __init__(self, appConfig, dbName = 'vb_db.json') -> None:
        self.db = TinyDB(dbName)
        self.usersDb = TinyDB('vb_users.json')
        self.app = Flask(__name__)
        self.config = appConfig
        self.viber = Api(BotConfiguration(
            name = self.config.getProperty('Publishers.Viber.Name'),
            avatar = '',
            auth_token = self.config.getProperty('Publishers.Viber.Token')
        ))
        self.query = Query()
        print("Viber publisher created.")
    
    def __del__(self):
        self.db.close()
        self.usersDb.close()
            
    def FormatMessage(self, rawMessages):
        res = 'Automatsko obaveštenje o najavljenim prekidima snabdevanja električnom energijom u Banatskom Velikom Selu i okolini\n\n'

        for rawMessage in rawMessages:
            common_desc = rawMessage['common_desc']
            common_desc = ' '.join(common_desc.split('\\t'))
            common_desc = ' '.join(common_desc.split('\n'))
            common_desc = ' '.join(common_desc.split('\t'))
            common_desc = ' '.join(common_desc.split())
            common_desc = common_desc.replace('\xa0', ' ')
            res = res + common_desc + '\n'
            for rawMessageDesc in rawMessage['desc']:
                pretty = ' '.join(rawMessageDesc.split('\\n')).replace('\xa0', ' ')
                pretty = ' '.join(pretty.split('\\t'))
                pretty = ' '.join(pretty.split('\n'))
                pretty = ' '.join(pretty.split('\t'))
                pretty = ' '.join(pretty.split('\\'))
                pretty = ' '.join(pretty.split())
                pretty = re.sub(r'\b[0-9]\\\.', '', pretty)
                pretty = re.sub(r'[0-9]\\\.', '', pretty)
                res = res + ' ' + pretty + '\n'
            res = res + '\n'
        return res

    def Publish(self, message) -> None:
        try:
            print('Posting to Viber...' + self.FormatMessage(message.message))
            UserQ = Query()
            for user in self.usersDb.search(UserQ.active == '1'):
                messageCopy = message
                messageCopy.userId = user['id']
                if len(self.db.search((self.query.hash == messageCopy.hash) & (self.query.userId == user['id']))) == 0:
                    self.viber.send_messages(user['id'], [ TextMessage(text=self.FormatMessage(messageCopy.message)) ])
                    self.db.insert(messageCopy.ToDict())
                    print('Message sent to Viber user: ' + user['name'])
                else:
                    print('User ' + user['name'] + ' already notified through Viber')
        except:
            print('Posting to Viber failed')
        

