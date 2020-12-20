import unittest
import config_with_yaml as config
from publishers.FacebookPubMod import FacebookPub
from sources.ElektrodistribucijaMod import ElektrodistribucijaSrc

class TestStringMethods(unittest.TestCase):

    def testFacebookPub(self): 
        try:       
            appConfig = config.load('config.test.yml')
            pub = FacebookPub(appConfig, 'fb_db.json')
            src = ElektrodistribucijaSrc(appConfig, 'http://www.elektrovojvodina.rs/sl/mediji/ED-Zrenjanin123')
            msgs = src.AcquireMessages()
            for msg in msgs:
                txt = pub.FormatMessage(msg.message)
                self.assertTrue(type(txt).__name__ == 'str' or type(txt).__name__ == 'unicode')
        except:
            self.assertTrue(False)
if __name__ == '__main__':
    unittest.main()