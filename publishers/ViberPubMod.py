  
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

import time
import logging
import sched
import threading

class ViberPub:
    def __init__(self, appConfig, dbName = 'vb_db.json') -> None:
        self.db = TinyDB(dbName)
        self.app = Flask(__name__)
        self.config = appConfig
        self.viber = Api(BotConfiguration(
            name = self.config.getProperty('Publishers.Viber.Name'),
            avatar = self.config.getProperty('Publishers.Viber.Token'),
            auth_token = self.config.getProperty('Publishers.Viber.Token')
        ))
        self.query = Query()
        
        ## Delayed webhook setup
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(5, 1, self.set_webhook, (self.viber,))
        t = threading.Thread(target=scheduler.run)
        t.start()

        self.app.add_url_rule('/', 'incoming', self.incoming, methods=['POST'])
        t_webApp = threading.Thread(target=self.flaskThread)
        t_webApp.setDaemon(True)
        t_webApp.start()
        print("Viber publisher created.")
        
    def flaskThread(self):
        self.app.run(host='0.0.0.0', port=80, debug=False)

    def incoming(self):
        print('------------------------------------------------------------------------')
        print(request.path)

        viber_request = self.viber.parse_request(request.get_data().decode('utf8'))

        ## ID korisnika mora da se upiše u bazu i onda da se šalju obaveštenja
        type = viber_request.event_type
        print('------------------------------------------------------------------------')
        print(repr(type))
        if type == EventType.MESSAGE:
            self.viber.send_messages('/qNmzm5H8vXHIuuJAmJZvw==', [ TextMessage(text='Neko piše...') ])
        
        if isinstance(viber_request, ViberMessageRequest):
            message = viber_request.message
            self.viber.send_messages(viber_request.sender.id, [
                message
            ])
        elif isinstance(viber_request, ViberConversationStartedRequest) \
                or isinstance(viber_request, ViberSubscribedRequest) \
                or isinstance(viber_request, ViberUnsubscribedRequest):
            self.viber.send_messages(viber_request.sender.id, [
                TextMessage(None, None, viber_request.get_event_type())
            ])
        elif isinstance(viber_request, ViberFailedRequest):
            logger.warn("client failed receiving message. failure: {0}".format(viber_request))

        # print(' ---------------------------------------- ID:' + viber_request.sender.id)
        return Response(status=200)

    def set_webhook(self, viber):
        self.viber.set_webhook('https://e6734b2c3d40.ngrok.io')
        
    def Publish(self, message) -> None:
        if len(self.db.search(self.query.hash == message.hash)) > 0:
            print('Already published to Viber')
        else:
            try:
                print('Posting to Viber...' + message.message)
                self.viber.send_messages('/qNmzm5H8vXHIuuJAmJZvw==', [ TextMessage(text=message.message) ])
            except:
                print('Posting to Viber failed')
            self.db.insert(message.ToDict())
        

