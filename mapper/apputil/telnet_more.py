###
#
# Further telnet commands that can be executed to e.g. stop an app
#
###

import socket

class TelnetMore:
    def __init__(self, ip, port, password):
        self.ip = ip
        self.port = port
        self.password = password

        self.__s = socket.socket()
        self.alive = False
        self.authenticated = True
        try:
            self.__s.connect((self.ip, self.port))
            self.alive = True
        except socket.error as ex:
            print("Error connecting to %s:%s (%s)" % (ip, port, ex))
            #thread.interrupt_main()
        print(self.authenticate(password))

    def __del__(self):
        self.__s.close()

    def authenticate(self, password):
        if (self.alive and password and len(password) > 0):
            self.__s.send("auth %s\r\n" % (password))
            x = self.__s.recv(1024)
            if "OK" in x:
                #auth successful...
                self.password = password
                return True
            else:
                self.authenticated = False
                return False

    def startApp(self, packageName):
        if (self.alive and self.authenticated):
            self.__s.send("more start %s\r\n" % (packageName))

            x = self.__s.recv(1024)
            if "OK" in x:
                return True
            else:
                return False
        else:
            raise ValueError('Socket not alive or not authenticated')

    def stopApp(self, packageName):
        if (self.alive or self.authenticated):
            self.__s.send("more stop %s\r\n" % (packageName))

            x = self.__s.recv(1024)
            if "OK" in x:
                return True
            else:
                return False
        else:
            raise ValueError('Socket not alive or not authenticated')

    def restartApp(self, packageName):
        if (self.alive or self.authenticated):
            self.__s.send("more restart %s\r\n" % (packageName))

            x = self.__s.recv(1024)
            if "OK" in x:
                return True
            else:
                return False
        else:
            raise ValueError('Socket not alive or not authenticated')

    def resetAppdata(self, packageName):
        if (self.alive or self.authenticated):
            self.__s.send("more reset %s\r\n" % (packageName))

            x = self.__s.recv(1024)
            if "OK" in x:
                return True
            else:
                return False
        else:
            raise ValueError('Socket not alive or not authenticated')
