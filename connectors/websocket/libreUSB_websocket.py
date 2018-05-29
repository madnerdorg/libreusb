'''
 LibreConnector : Connect a serial port to libreNode
 Author : Remi Sarrailh (madnerd.org)
 Email : remi@madnerd.org
 License : MIT
'''
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
import sys
from OpenSSL import SSL
from twisted.internet import ssl, reactor
from modules import Settings
import thread
import json
import serial
import threading
global args, connected, connecting, serial_ok

class LCProtocol(WebSocketClientProtocol):


    def onConnect(self, response):
        # print("Server connected: {0}".format(response.peer))
        self.factory.resetDelay()
        self.createChannelAttempt = 0
        self.passwordAttempt = 0

    def onOpen(self):
        print("[" + args["name"] + "] --> " + args["server"] + " OPEN" )

    def onMessage(self, message, isBinary):
        global connected, device, connecting, serial_ok
        def deviceReader():
            global device, serial_ok
            while True:
                if serial_ok:
                    try:
                        data = b''
                        data = device.readline()
                        # print(data)
                        if data is not b'':
                            data = data.decode(encoding='utf-8', errors="replace")
                            self.sendMessage(format(data.encode('utf-8')))

                    except Exception as e:
                        print("[" + args["name"] + "] --> " + args["server"] + " ERROR " + str(e))
                        serial_ok = False
                        self.sendClose()
                        device.close()

        # print(message)
        if not isBinary:
            if connected:
                # print(message)
                try:
                    message = message.encode(encoding="utf-8", errors="replace") + args["lineending"]
                    # To do Terminal in Settings (No Line Break / NewLine \n NewLine & Carriage Return \r\n)
                    device.write(message.encode(encoding="utf-8", errors="replace") )
                except UnicodeDecodeError:
                    print("Non ascii sent, ignore...")
                except Exception as e:
                    print("[" + args["name"] + "] --> " + args["server"] + " SERIAL WRITE ERROR " + str(e))
                    device.close()
                    self.sendClose()
                    serial_ok = False
                # print(message)
            else:
                is_json = False
                if args["debug"] is not False:
                    print("[" + args["name"] + "] --> " + args["server"] + message)
                try:
                    message = json.loads(message)
                    is_json = True
                except Exception as e:
                    print e
                    print("[" + args["name"] + "] --> " + args["server"] + " NOT LIBRECARRIER" )
                    device.close()
                    self.sendClose()
                    serial_ok = False

                if is_json:
                    if "connected" in message:
                        connected = True
                    if "error" in message:
                        if message["error"] == args["name"]:
                            print("[" + args["name"] + "] --> " + args["server"] + " CHANNELS ALREADY EXIST" )
                            #self.sendMessage('{"remove":"' + args["name"] + '"}')
                    if "ok" in message:
                        if message["ok"] == args["name"]:
                            print("[" + args["name"] + "] --> " + args["server"] + " CONNECTED" )
                            connected = True
                    if "channels" in message:
                        print("[" + args["name"] + "] --> " + args["server"] + " CONNECTING ..." )
                        for channel in message["channels"]:
                            if channel == args["name"]:
                                last_id = 0
                                no_unused_channel = True
                                while no_unused_channel:
                                    new_channel = args["name"] + "/" + str(last_id)
                                    no_unused_channel = False
                                    for channel in message["channels"]:
                                        if channel == new_channel:
                                            no_unused_channel = True
                                            last_id = last_id + 1
                                args["name"] = new_channel
                        self.sendMessage('{"add":"' + args["name"] + '"}')
                        read_thread = threading.Thread(target=deviceReader)
                        read_thread.daemon = True
                        read_thread.start()
                    if "password" in message:
                        if self.passwordAttempt == 0 and args["password"] is not False:
                            print("[" + args["name"] + "] --> " + args["server"] + " PASSWORD ?" )
                            self.sendMessage('{"password":"' + args["password"] + '"}')
                            self.passwordAttempt = self.passwordAttempt + 1
                        else:
                            print("[" + args["name"] + "] --> " + args["server"] + " INVALID PASSWORD !!" )
                            device.close()
                            self.sendClose()
                            serial_ok = False


    def onClose(self, wasClean, code, reason):
        pass
        # print("WebSocket connection closed: {0}".format(reason))


class LCFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = LCProtocol

    def clientConnectionFailed(self, connector, reason):
        global serial_ok,connected
        print("[" + args["name"] + "] --> " + args["server"] + " FAILED" )
        # print serial_ok
        connected = False
        if serial_ok:
            self.retry(connector)
        else:
            reactor.stop()

    def clientConnectionLost(self, connector, reason):
        global serial_ok
        connected = False
        print("[" + args["name"] + "] --> " + args["server"] + " CLOSED" )
        # print serial_ok
        if serial_ok:
            self.retry(connector)
        else:
            reactor.stop()


args = Settings.get()

if args["lineending"] == "nr":
    args["lineending"] = "\n\r"
if args["lineending"] == "r":
    args["lineending"] = "\r"
if args["lineending"] == "n":
    args["lineending"] = "\n"
args["lineending"] = args["lineending"].encode()
connected = False
connecting = False
serial_ok = True

# Serial Connection
try:
    device = serial.Serial(args["port"], args["baudrate"],timeout=1)
except Exception as e:
    print("!! Serial failure : " + str(e))
    serial_ok = False

# WebSocket Connection
# log.startLogging(sys.stdout)
valid , ws_url, url, port, is_ssl = Settings.get_server_info(args["server"])


if valid:
    if serial_ok:
        print("[" + args["name"] + "] --> " + args["server"] + " ..." )
        factory = LCFactory(ws_url)
        if is_ssl:
            # print("SSL")
            reactor.connectSSL(url, port, factory, ssl.ClientContextFactory())
        else:
            # print("Not SSL")
            reactor.connectTCP(url, port, factory)
        reactor.run()
else:
    print("[" + args["name"] + "] --> " + args["server"] + " INVALID SERVER" )


