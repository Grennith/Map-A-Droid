import socket
import time
import logging
log = logging.getLogger()

class TelnetClient:
    def __init__(self, ip, port, password):
        if (password != None):
            log.debug('Trying to build up a telnet connection to %s:%s with a password'
                % (str(ip), str(port)))
        else:
            log.debug('Trying to build up a telnet connection to %s:%s without a password'
                % (str(ip), str(port)))

        self.ip = ip
        self.port = port
        self.password = password
        self.connected = False

        self.__sock = socket.socket()
        attempts = 0
        while (not self.__connectSocket() and attempts < 10):
            time.sleep(1)
        if (self.__sock is None):
            raise ValueError('Socket not connected')
        else:
            self.connected = True
        #Retrieve the help instructions to have auth only receive "OK"
        #log.error(self.__sock.recv(1024))
        result = ""
        while not "OK" in result:
            result = self.__sock.recv(1024)
        self.authenticated = self.__auth()

        #print(authenticated)


    def __del__(self):
        self.__sock.close()

    def __connectSocket(self):
        try:
            self.__sock.connect((self.ip, self.port))
            return True
        except socket.error as ex:
            return False

    def __sendCommandWithoutChecks(self, command):
        self.__sock.send(command)
        #TODO: handle socketError
        return self.__sock.recv(1024)

    def getScreenshot(self):
        self.__sock.send("screen capture\r\n")
        start = time.time()
        chars = self.__sock.recv(4096)
        countOfChars = int(chars)
        #print(countOfChars)
        img_data = ""
        while len(img_data) < countOfChars:
            img_data += self.__sock.recv(4096)

        fh = open("screenshot.jpg", "wb")
        fh.write(img_data.decode('base64'))
        fh.close()
        #print time.time() - start

    def __sendCommandRecursive(self, command, again):
        log.debug("__sendCommandRecursive: Waiting for result of %s" % str(command))
        x = self.__sendCommandWithoutChecks(command)
        log.debug("__sendCommandRecursive: Sending '%s' resulted in '%s'" % (str(command), x))
        if ("KO: password required. Use 'password' or 'auth'" in x
            and not again):
            #handle missing auth
            log.debug('__sendCommandRecursive: Auth required')
            self.__auth();
            self.__sendCommandRecursive(command, True);
        else:
            log.debug('__sendCommandRecursive: Sent command successfully')
            self.authenticated = False
            return (True, x)

    #just a function to make the function call look better
    def sendCommand(self, command):
        return self.__sendCommandRecursive(command, False)

    def __auth(self):
        if (self.password == None):
            log.debug("__auth: No password configured, not authenticating")
            return False
        log.debug("__auth: Trying to authenticate")
        toSend = "auth %s\r\n" % str(self.password)
        result = self.__sendCommandWithoutChecks(toSend)
        log.debug("__auth: got: %s" % str(result))
        authenticated = ("OK" in result)
        self.authenticated = authenticated
        log.debug("__auth: Authenticated: %s" % str(authenticated))
        return authenticated
