'''
 LibreUSB : Scan USB Serial port and connect it
 using connector
 Author : Remi Sarrailh (madnerd.org)
 Email : remi@madnerd.org
 License : MIT
'''

import os
import time
from threading import Thread
import threading
import serial
from serial.tools import list_ports
import re
import sys


from modules import Settings

VERSION = "0.8"

global keep_scanning, subprocesses
devices_ports = []
devices_name = []
devices = {}
libreUSB_processes = []
config_file = False
keep_scanning = True

args = Settings.get()
if args["nogui"] is False:
    from modules import Gui

print("LibreUSB - version " + VERSION)
print("By madnerd.org (https://github.com/madnerdorg/libreusb)")
print("----------------------------------------------------------")

# Get connector for windows or linux, if a python version exists use it instead
connector_software = args["connectorFile"]


def print_status():
    global devices
    print("-------------- Devices ---------------------------")
    for name, settings in devices.iteritems():
        if settings[2] == "n":
            settings[2] = "NewLine"
        elif settings[2] == "nr":
            settings[2] = "Both NL & CR"
        elif settings[2] == "r":
            settings[2] = "Carriage return"
        elif settings[2] == "":
            settings[2] = "No line ending"
        if args["append"] != "":
            print(name + "/" + args["append"] + "  -  " + settings[0] + "  -  " + settings[1] + "  -  " + settings[2])
        else:
            print(name + "  -  " + settings[0] + "  -  " + settings[1] + "  -  " + settings[2])
    print("--------------------------------------------------")

# Check if the device returns data on serial port.
def get_all(serialDevice):
    return serialDevice.port
"""
# Check if the device returns data on serial port.
def get_unknown(serialDevice):
    print(serialDevice.port + " --> Unknown ?")
    name = ""
    try:
        serialDevice.flushInput()
        data = serialDevice.readline().strip()
    except:
        print(serialDevice.port + " used by another application (or invalid)")
    #print(data)
    try:
        data.decode()
    except UnicodeDecodeError:
        name = "nonascii"
    else:
        if data != "" and len(data) > 3:
            name = serialDevice.port
            print(data)
            print "New Serial Device!"
    return name
"""
# Check if the device answer when "/info" is sent.
def get_libreobject(serialDevice):
    print(serialDevice.port + " --> LibreObject ?")
    name = ""
    try:
        serialDevice.write("/info".encode())
        serialDevice.flushInput()
        data = serialDevice.readline().strip()
    except:
        print(serialDevice.port + " used by another application (or invalid)")
    try:
        data = data.decode()
        if data != "" and len(data) > 3:
            name = data
            #print "New " + name + " Device!"
    except:
        pass
    #print(data)
    return name

# Check if device answer when 0;0;3;0;2;0;0\n is sent (Mysensors command : INTERNAL/I_VERSION)
# Source : https://www.mysensors.org/build/parser
# Todo : Refactor get_mysensors/get_libreobject in one function.
def get_mysensors(serialDevice):
    print(serialDevice.port + " --> MySensors ?")
    name = ""
    try:
        serialDevice.write("0;0;3;0;2;0;0\n".encode())
        serialDevice.flushInput()
        data = serialDevice.readline().strip()
    except:
        print("Device used by another application (or invalid)")
    try:
        data = data.decode()
        #0;255;3;0;2;2.2.0
        if data != "":
            mysensors_array = data.split(";")
            # print(len(mysensors_array))
            if len(mysensors_array) == 6:
                name="mysensors/gateway/v" + mysensors_array[5]
            #print("New MySensors Gateway")
    except Exception as e:
        pass
    #print(data)
    return name

## Add ESP8266 identification (Command AT --> OK)

def get_devices(usb_port):
    """ Check what device this is, using a string as a question
        If the device send back a message with answer in it, return his name and port
    """
    name = ""
    goodport = False
    if args["baudrate"] == -1:
        baudrates = ["9600", "115200", "57600", "38400"]
    else:
        baudrates = []
        baudrates.append(args["baudrate"])
    for baudrate in baudrates:

        if name != "":
            break

        try:
            print(usb_port + " ------- " + baudrate)
            serialDevice = serial.Serial(usb_port, baudrate,
                                        writeTimeout=0.5, timeout=1)
            goodport = True
        except Exception as serial_error:
            print(usb_port + " used by another application (or invalid)")
            # print("[ERROR]: " + str(serial_error))
        if goodport:
            retry = int(args["retry"])

            #time.sleep(args["interval"])
            while retry > 0:
                lineending = args["lineending"]
                if bool(args["force"]) is True:
                    name = get_all(serialDevice)
                    return lineending, baudrate, name
                else:
                    # print(str(retry) + "------")
                    """
                    if args["unknown"] is True:
                        time.sleep(0.25)
                        name = get_unknown(serialDevice)

                        # If string is nonascii we assume the baudrate is incorrect.
                        if name == "nonascii":
                            name = ""
                            serialDevice.close()
                            break
                        #print(name)
                    """
                    if args["libreobject"] is True and name == "":
                        time.sleep(0.25)
                        name = get_libreobject(serialDevice)
                        if name != "":
                            lineending = ""
                        #print(name)

                    if args["mysensors"] is True and name == "":
                        time.sleep(0.25)
                        name = get_mysensors(serialDevice)
                        #print(name)
                        if name != "":
                            lineending = "n"

                    if name != "":
                        serialDevice.close()
                        return lineending, baudrate, name
                retry = retry - 1
            serialDevice.close()
        else:
            return "","", ""
    name = serialDevice.port
    if args["baudrate"] == -1:
        baudrate = "9600"
    else:
        baudrate = args["baudrate"]
    return lineending, baudrate, name

def get_ports():
    """
        # Get serials port list and put it in an array

        return: devices list
    """
    raw_devices = list_ports.comports()
    devices = []
    for raw_device in raw_devices:
        devices.append(raw_device[0])
    return devices


def connector_thread(append, name, usb_port, baudrate, lineending, url):
    """
        Start connector
    """
    global libreUSB_processes
    command = connector_software + ' --port "' + str(usb_port) + '"'
    if append == "":
        command = command + ' --name "' + name + '"'
        
    else:
        print(append)
        command = command + ' --name "' + name + '/' + append + '"'
    command = command + ' --baudrate "' + baudrate + '"'  # Add Baudrate
    command = command + ' --lineending "' + lineending + '"'  # Add Baudrate
    command = command + ' --settings "' + args["settings_file"] + '"'
    if args["debug"]:
        print("[INFO]: " + command)
    #DETACHED_PROCESS = 0x00000008
    #subprocess.call(command, creationflags=DETACHED_PROCESS)
    # print(libreUSB_process)
    # libreUSB_processes.append(libreUSB_process)
    os.system(command)


def connect(name, usb_port, baudrate, lineending):
    """
        Start a thread for connector
    """
    new_connector = Thread(target=connector_thread,
                           args=(args["append"], name, usb_port, baudrate, lineending, args["server"]))
    # new_connector.daemon = True
    new_connector.start()
    # connectors.append(new_connector)


def scan_devices():
    global devices
    """
        Search for serial devices (arduino)
    """
    scanned_devices = get_ports()
    for usb_port in scanned_devices:
        if usb_port not in devices_ports:
            # print("[NEW]: " + usb_port)
            devices_ports.append(usb_port)
            lineending, baudrate, name = get_devices(usb_port)

            if name != "":
                # Check name for invalid characters
                regex = r'^([\w-]|\.|;|/|:|,)+$'
                # https://stackoverflow.com/questions/10944438/how-do-i-check-if-a-string-only-contains-alphanumeric-characters-and-dashes
                found_s = re.findall(regex, name)
                valid = bool(found_s)
                if valid is False:
                    name = usb_port
                connect(name, usb_port, baudrate, lineending)
                devices_name.append(name)
                devices[name] = [usb_port, baudrate, lineending]
                print_status()
            else:
                pass
                # print("[WARN]: " + usb_port + " not connected")
    for device_port in devices_ports:
        if device_port not in scanned_devices:
            #print("[INFO]: " + device_port + " was removed")
            devices_ports.remove(device_port)
            device_name = ""
            for device in devices:
                #print(devices[device][0])
                #print(device_port)
                if devices[device][0] == device_port:
                    device_name = device
            devices.pop(device_name, None)
            print_status()

while keep_scanning:
    if args["nogui"] is False:
        keep_scanning = False
        for thread in threading.enumerate():
            if thread.name == "gui":
                keep_scanning = True
    scan_devices()
    # print(libreUSB_processes)
    if keep_scanning is False:
        # raise Exception('Gui Stopped')
        sys.exit(0)
    time.sleep(float(args["interval"]))
