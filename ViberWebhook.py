  
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
import socket

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
        self.app.add_url_rule('/ctrl', '', self.control, methods=['POST', 'GET'])
        self.t_webApp = threading.Thread(target=self.flaskThread)
        self.t_webApp.setDaemon(True)
        
        print("Viber worker created.")
    
    def __del__(self):
        self.usersDb.close()
        
    def flaskThread(self):
        self.app.run(host='0.0.0.0', port=80, debug=False)

    def Run(self):
        self.t_webApp.run()

    def GetAdmins(self):
        admins = self.usersDb.search(self.query.admin == '1')
        return admins

    def NotifyAdmins(self, admins, message):
        for admin in admins:
            self.viber.send_messages(admin['id'], [ TextMessage(text = message) ])   

    def IsAdmin(self, user_id, admins):
        return next((admin for admin in admins if admin['id'] == user_id), None) != None

    def Reboot():
        command = "/usr/bin/sudo /sbin/shutdown -r now"
        import subprocess
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output)

    def RestartViber():
        command = "service Viber restart"
        import subprocess
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output)

    def incoming(self):

        admins = self.GetAdmins()
        print(request.path)
        viber_request = self.viber.parse_request(request.get_data().decode('utf8'))

        if isinstance(viber_request, ViberMessageRequest):
            message = viber_request.message
            if isinstance(message, TextMessage):

                is_admin = self.IsAdmin(viber_request.sender.id, admins)
                if is_admin:
                    print("IsAdmin: True")
                
                ## HANDLE ADMIN REQUESTS
                usersListStr = ''
                if(message.text.strip() == "/ListUsers" and is_admin):
                    for user in self.usersDb.all():
                        usersListStr += user['name'] + '\n'
                    self.NotifyAdmins(admins, 'Korisnici: \n' + usersListStr)
                    return Response(status=200)                
                if(message.text.strip() == "/ListAdmins" and is_admin):
                    for user in self.usersDb.search(self.query.admin == '1'):
                        usersListStr += user['name'] + '\n'
                    self.NotifyAdmins(admins, 'Administratori: \n' + usersListStr)
                    return Response(status=200)
                if(message.text.strip() == "/GetPublicURL" and is_admin):
                    self.NotifyAdmins(admins, 'Javna adresa: \n' + self.public_url)
                    return Response(status=200)
                if(message.text.strip() == "/GetLocalIP" and is_admin):
                    self.NotifyAdmins(admins, 'Lokalna adresa: \n' + socket.gethostbyname(socket.gethostname()))
                    return Response(status=200)
                if(message.text.strip() == "/XRebootMe" and is_admin):
                    self.NotifyAdmins(admins, 'Rebooting...')
                    self.Reboot()
                    return Response(status=200)
                if(message.text.strip() == "/XRestartViberService" and is_admin):
                    self.NotifyAdmins(admins, 'Restarting Viber service...')
                    self.RestartViber()
                    return Response(status=200)

                UserQ = Query()

                # Handle standard requests
                if message.text.strip().lower() == 'stop':
                    self.usersDb.update({'active': '0'}, UserQ.id == viber_request.sender.id)
                else:
                    if len(self.usersDb.search(UserQ.id == viber_request.sender.id)) == 0:
                        self.usersDb.insert({'id': viber_request.sender.id, 'name': viber_request.sender.name, 'active': '1', 'admin': '0'})
                    else:
                        self.usersDb.update({'active': '1'}, UserQ.id == viber_request.sender.id)
                    self.viber.send_messages(viber_request.sender.id, [ TextMessage(text = 'Uspešna prijava! Pošalji STOP za odjavu.') ])
                    #self.viber.send_messages("/qNmzm5H8vXHIuuJAmJZvw==", [ TextMessage(text = 'Novi korisnik: ' + viber_request.sender.name) ])
                    self.NotifyAdmins(admins, 'Novi korisnik: ' + viber_request.sender.name)
        elif isinstance(viber_request, ViberConversationStartedRequest):
            UserQ = Query()
            #self.viber.send_messages(viber_request.user.id, [ TextMessage(text='Za prijavu pošaljite bilo kakvu poruku.') ])
            if len(self.usersDb.search(UserQ.id == viber_request.user.id)) == 0:
                self.usersDb.insert({'id': viber_request.user.id, 'name': viber_request.user.name, 'active': '1', 'admin': '0'})
            else:
                self.usersDb.update({'active': '0'}, UserQ.id == viber_request.user.id)
        elif isinstance(viber_request, ViberSubscribedRequest):
            UserQ = Query()
            self.viber.send_messages(viber_request.user.id, [ TextMessage(text='Za prijavu pošaljite bilo kakvu poruku.') ])
            if len(self.usersDb.search(UserQ.id == viber_request.user.id)) == 0:
                self.usersDb.insert({'id': viber_request.user.id, 'name': viber_request.user.name, 'active': '1', 'admin': '0'})
            else:
                self.usersDb.update({'active': '1'}, UserQ.id == viber_request.user.id)
        elif isinstance(viber_request, ViberUnsubscribedRequest):
            UserQ = Query()
            self.usersDb.update({'active': '0'}, UserQ.id == viber_request.user_id)
        elif isinstance(viber_request, ViberFailedRequest):
            logger.warn("client failed receiving message. failure: {0}".format(viber_request))

        return Response(status=200)


    def control(self):
        admins = self.GetAdmins()
        #data = request.get_data().decode('utf8')
        if(request.args.get('command') == 'users'):
            if(request.args.get('a') == '0'):
                usersListStr = ""
                for user in self.usersDb.all():
                    usersListStr += user['name'] + ';'
                return Response(status=200, response=usersListStr)
            else:
                usersListStr = ""
                for user in self.usersDb.search(self.query.admin == '1'):
                    usersListStr += user['name'] + ';'
                return Response(status=200, response=usersListStr)

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
