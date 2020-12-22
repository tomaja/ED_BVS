  
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
from pyngrok import ngrok
import re
import sys
import config_with_yaml as config

import time
import logging
import sched
import threading

class ViberWebhook:
    def __init__(self, appConfig, dbUsers = 'vb_users.json') -> None:
        http_tunnel = ngrok.connect()
        self.public_url = http_tunnel.public_url.replace('http', 'https')
        print('Public URL acquired: ' + self.public_url)
        self.usersDb = TinyDB(dbUsers)
        self.app = Flask(__name__)
        self.config = appConfig
        self.viber = Api(BotConfiguration(
            name = self.config.getProperty('Publishers.Viber.Name'),
            avatar = self.config.getProperty('Publishers.Viber.Avatar'),
            auth_token = self.config.getProperty('Publishers.Viber.Token')
        ))
        self.query = Query()
        
        ## Delayed webhook setup
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(5, 1, self.set_webhook, (self.viber,))
        t = threading.Thread(target=scheduler.run)
        t.start()

        self.app.add_url_rule('/', 'incoming', self.incoming, methods=['POST'])
        self.t_webApp = threading.Thread(target=self.flaskThread)
        self.t_webApp.setDaemon(True)
        
        print("Viber worker created.")
    
    def __del__(self):
        self.usersDb.close()
        
    def flaskThread(self):
        self.app.run(host='0.0.0.0', port=80, debug=False)

    def Run(self):
        self.t_webApp.run()

    def incoming(self):
        print(request.path)
        viber_request = self.viber.parse_request(request.get_data().decode('utf8'))

        if isinstance(viber_request, ViberMessageRequest):
            message = viber_request.message
            if isinstance(message, TextMessage):
                print(message)
                UserQ = Query()
                if message.text.strip().lower() == 'stop':
                    self.usersDb.update({'active': '0'}, UserQ.id == viber_request.sender.id)
                else:
                    if len(self.usersDb.search(UserQ.id == viber_request.sender.id)) == 0:
                        self.usersDb.insert({'id': viber_request.sender.id, 'name': viber_request.sender.name, 'active': '1'})
                    else:
                        self.usersDb.update({'active': '1'}, UserQ.id == viber_request.sender.id)
                    self.viber.send_messages(viber_request.sender.id, [ TextMessage(text='Pošalji STOP za odjavu') ])
        elif isinstance(viber_request, ViberConversationStartedRequest):
            UserQ = Query()
            if len(self.usersDb.search(UserQ.id == viber_request.user.id)) == 0:
                self.usersDb.insert({'id': viber_request.user.id, 'name': viber_request.user.name, 'active': '1'})
            else:
                self.usersDb.update({'active': '1'}, UserQ.id == viber_request.user.id)
            self.viber.send_messages(viber_request.user.id, [ TextMessage(text='Uspešna prijava. Pošalji STOP za odjavu') ])
        elif isinstance(viber_request, ViberSubscribedRequest):
            UserQ = Query()
            self.viber.send_messages(viber_request.user.id, [ TextMessage(text='Uspešna prijava. Odjava u meniju ili slanjem poruke STOP') ])
            if len(self.usersDb.search(UserQ.id == viber_request.user.id)) == 0:
                self.usersDb.insert({'id': viber_request.user.id, 'name': viber_request.user.name, 'active': '1'})
            else:
                self.usersDb.update({'active': '1'}, UserQ.id == viber_request.user.id)
        elif isinstance(viber_request, ViberUnsubscribedRequest):
            UserQ = Query()
            self.usersDb.update({'active': '0'}, UserQ.id == viber_request.user_id)
        elif isinstance(viber_request, ViberFailedRequest):
            logger.warn("client failed receiving message. failure: {0}".format(viber_request))

        return Response(status=200)

    def set_webhook(self, viber):
        self.viber.set_webhook(self.public_url)  


def main():
    print("Starting Viber webhook...")
    if len(sys.argv) > 1:
        appConfig = config.load(sys.argv[1])
    else:
        appConfig = config.load('config.yml')

    vw = ViberWebhook(appConfig)
    vw.Run()

if __name__ == '__main__':
    main()