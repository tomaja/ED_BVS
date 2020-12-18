
import hashlib

class Message:
    def __init__(self) -> None:
        self.message = ''
        self.image = None
        self.link = ''
        self.hash = ''
        self.md5 = hashlib.md5()
        
    def Hash(self):
        self.md5.update(repr(repr(self.message) + self.link).encode('utf-8'))
        return self.md5.hexdigest()

    def ToDict(self):
        d = {}
        d['message'] = self.message
        d['image'] = self.image
        d['link'] = self.link
        d['hash'] = self.hash
        return d