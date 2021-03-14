from message import Message

class FileInputSrc:
    def __init__(self, appConfig) -> None:
        self.fileInput = appConfig.getProperty('Sources.File.Input')
        print("FileInput source created for: " , repr(appConfig.getProperty('Sources.File.Input')))

    def GetRelevantMessages(self):
        file = open(self.fileInput, "r")
        rawInput = file.readlines()
        rawMessages = []
        for msg in rawInput:
            if len(msg) > 1:
                rawMessages.append(msg)
        rawMessages.reverse()
        return rawMessages

    def AcquireMessages(self):
        messages = []
        message = Message()
        message.message = self.GetRelevantMessages()
        message.hash = message.Hash()
        messages.append(message)
        return messages
