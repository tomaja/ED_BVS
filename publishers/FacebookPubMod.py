import facebook
from tinydb import TinyDB, Query
import config_with_yaml as config

class FacebookPub:
    def __init__(self, appConfig, dbName = 'fb_db.json') -> None:
        self.db = TinyDB(dbName)
        self.config = appConfig
        self.query = Query()
        print("Facebook publisher created.")
        self.parent_object = self.config.getProperty('Publishers.Facebook.ParentObject')
        self.access_token = self.config.getProperty('Publishers.Facebook.AccessToken')

    def FormatMessage(self, rawMessages):
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

    def Publish(self, message) -> None:
        if len(self.db.search(self.query.hash == message.hash)) > 0:
            print('Already published')
        else:
            try:
                print('Posting to FB...' + self.FormatMessage(message.message))
                post = { 'message': self.FormatMessage(message.message), 'link': message.link }
                graph = facebook.GraphAPI(access_token=self.access_token, version='3.1')
                api_request = graph.put_object(
                    parent_object=self.parent_object,
                    connection_name='feed',
                    message=post['message'],
                    #link=post['link']
                )
            except:
                print('Posting to FB failed')
            self.db.insert(message.ToDict())
