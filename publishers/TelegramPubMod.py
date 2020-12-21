
from telegram import Update, Chat, Bot, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from tinydb import TinyDB, Query
import config_with_yaml as config
import re

class TelegramPub:
    def __init__(self, appConfig, dbName = 'tg_db.json') -> None:
        self.config = appConfig
        self.bot = Bot(token=self.config.getProperty('Publishers.Telegram.Token'))
        self.chat_id = self.config.getProperty('Publishers.Telegram.ChatId')
        self.db = TinyDB(dbName)
        self.query = Query()
        print("Telegram publisher created.")
    
    def __del__(self):
        self.db.close()

    def FormatMessage(self, rawMessages):
        res = '*Automatsko obaveštenje o najavljenim prekidima snabdevanja električnom energijom u Banatskom Velikom Selu i okolini*\n\n'
        for rawMessage in rawMessages:
            common_desc = rawMessage['common_desc']
            common_desc = ' '.join(common_desc.split('\\t'))
            common_desc = ' '.join(common_desc.split('\n'))
            common_desc = ' '.join(common_desc.split('\t'))
            common_desc = ' '.join(common_desc.split())
            common_desc = common_desc.replace('\xa0', ' ').replace('.', r'\.')
            res = res + common_desc + '\n'
            for rawMessageDesc in rawMessage['desc']:
                pretty = ' '.join(rawMessageDesc.split('\\n')).replace('\xa0', ' ').replace('.', '\.')
                pretty = ' '.join(pretty.split('\\t'))
                pretty = ' '.join(pretty.split('\n'))
                pretty = ' '.join(pretty.split('\t'))
                pretty = ' '.join(pretty.split())
                pretty = re.sub(r'\b[0-9]\\\.', '', pretty)
                pretty = re.sub(r'[0-9]\\\.', '', pretty)
                res = res + '_' + pretty + '_ \n'
            res = res + '[Elektrodistribucija](' + rawMessage['url'] + ')'
            res = res + '\n\n'
        return res

    def Publish(self, message) -> None:
        if len(self.db.search(self.query.hash == message.hash)) > 0:
            print('Already published to Telegram')
        else:
            try:
                print('Posting to Telegram...' + self.FormatMessage(message.message))
                self.bot.sendMessage(self.chat_id, self.FormatMessage(message.message), parse_mode=ParseMode.MARKDOWN_V2)
                self.db.insert(message.ToDict())
            except:
                print('Posting to Telegram failed')
