import time
import logging
import math
import sys
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from threading import Thread, Event, Lock

TEXT = 0x1
BINARY = 0x2

log = logging.getLogger()

idMutex = Lock()
requestMutex = Lock()
responseMutex = Lock()
requests = {} # map with IDs as keys and events as messages
responses = {} # Map with IDs as keys, values are the messages

def setRequest(id, event):
    global requests, requestMutex
    requestMutex.acquire()
    requests[id] = event
    requestMutex.release()

def setEvent(id):
    global requests
    requestMutex.acquire()
    result = False
    if id in requests:
        requests[id].set()
        result = True
    else:
        # the request has already been deleted due to a timeout...
        result = False
    requestMutex.release()
    return result

def removeRequest(id):
    global requests, requestMutex
    requestMutex.acquire()
    requests.pop(id)
    requestMutex.release()

def setResponse(id, message):
    global responses, responseMutex
    responseMutex.acquire()
    responses[id] = message
    responseMutex.release()

def popResponse(id):
    global responses, responseMutex
    responseMutex.acquire()
    message = responses.pop(id)
    responseMutex.release()
    return message

clients = []
class SimpleEcho(WebSocket):

    def handleMessage(self):
        if self.opcode == TEXT:
            log.debug("Receiving message: %s" % str(self.data))
            splitup = self.data.split(";")
            id = int(splitup[0])
            response = splitup[1]
            setResponse(id, response)
            if not setEvent(id):
                # remove the response again - though that is kinda stupid
                popResponse(id)

    def handleConnected(self):
        clients.append(self)
        log.warning('%s connected' % str(self.address))

    def handleClose(self):
        clients.remove(self)
        log.warning('%s closed' % str(self.address))

server = None
def setupWebsocket(websocketInterface, websocketPort):
    global server
    server = SimpleWebSocketServer(websocketInterface, websocketPort, SimpleEcho)
    server.serveforever()


class WebsocketServer:
    def __init__(self, websocketInterface, websocketPort):
        global server
        global clients
        self.__initialId = 0
        self.__clients = clients
        self.__server = server
        t = Thread(target=setupWebsocket, name='ws', args=(websocketInterface, websocketPort,))
        t.daemon = True
        print("Starting thread")
        t.start()

    def __del__(self):
        self.__server.close()

    def __getNewMessageId(self):
        global idMutex
        idMutex.acquire()
        self.__initialId += 1
        self.__initialId = int(math.fmod(self.__initialId, 10000))
        if self.__initialId == 10000:
            self.__initialId = 1
        toBeReturned = self.__initialId
        idMutex.release()
        return toBeReturned

    def send(self, command, timeout):
        log.debug("Sending command: %s" % command)
        global requests
        messageId = self.__getNewMessageId()
        messageEvent = Event()
        messageEvent.clear()
        setRequest(messageId, messageEvent)
        log.debug("Waiting for at least one client")
        while len(clients) == 0:
            time.sleep(0.5)
        log.debug("Client connected, sending command")
        for client in clients:
            client.sendMessage(u"%s;%s" % (str(messageId), str(command)))

        result = None
        log.debug("Timeout: " + str(timeout))
        if messageEvent.wait(timeout):
            log.debug("Received an answer")
            # okay, we can get the response..
            result = popResponse(messageId)
            log.debug("Answer: %s" % result)
        else:
            # timeout reached
            log.warning("Timeout reached while waiting for a response...")

        log.debug("Received response: %s" % str(result))
        removeRequest(messageId)
        return result

    def sendCommand(self, command, timeout):
        received = self.send(command, timeout)
        if received is None:
            log.warning("Reached a timeout waiting for response, returning None")
            return None
        elif "KO: password required." in received:
            log.fatal("Missing auth... TODO! report")
            sys.exit(1)
        else:
            return received
