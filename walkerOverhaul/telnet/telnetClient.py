import socket
import time

class TelnetClient:
    def __init__(self, ip, port, password):
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

    def __sendCommandRecursive(self, command, again):
        x = self.__sendCommandWithoutChecks(command)
        if "OK" in x:
            return True
        elif ("KO: password required. Use 'password' or 'auth'" in x
            and not again):
            #handle missing auth
            self.authenticate(self.password);
            self.__sendCommandRecursive(command, True);
        else:
            self.authenticated = False
            return False

    #just a function to make the function call look better
    def sendCommand(self, command):
        return self.__sendCommandRecursive(command, False)

    def __auth(self):
        result = self.__sendCommandWithoutChecks("auth %s\r\n" % (self.password))
        authenticated = ("OK" in result)
        self.authenticated = authenticated
        return authenticated
