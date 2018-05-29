# Arguments parsing
import argparse
import os
import sys
import ConfigParser
import socket

DESCRIPTION = "Connect Serial objects to LibreCarrier"
SETTINGS_FILE = "settings/libreusb.ini"

def get_server_info(server_url):
    """
    Get url, port , is ssl from a websocket url and check if it is valid
    """

    ws_url = server_url
    url = False
    port = False
    is_ssl = False
    valid = False
    server_url_array = server_url.split(":")

    if len(server_url_array) >= 2:
        # print(server_url_array)
        if server_url_array[0] == "wss":
            is_ssl = True
            valid = True
        elif server_url_array[0] == "ws":
            valid = True

        if len(server_url_array) == 3:
            # print(server_url_array[2])
            port_array = server_url_array[2].split("/")
            # print(port_array)
            if port_array[0].isdigit():
                port = int(port_array[0])
            else:
                valid = False
        else:
            if is_ssl:
                port = 443
            else:
                port = 80
        if server_url_array[1].startswith("//"):
            url = server_url_array[1].replace("//", "")
        else:
            valid = False
    # print(valid, ws_url, url, port, is_ssl)
    return valid, ws_url, url, port, is_ssl

def get():
    args = get_from_terminal()
    args = get_from_file(args)
    connector_path = "connectors/" + args["connector"] + "/" + "libreUSB_" + args["connector"]
    # print(connector_path)
    if os.path.exists(connector_path + ".py"):
        args["connectorFile"] = "python " + connector_path + ".py"
    else:
        if sys.platform == "win32":
            args["connectorFile"] = connector_path + ".exe"
            args["connectorFile"] = args["connectorFile"].replace("/", "\\")
            # print(args["connectorFile"])
        elif sys.platform == "linux2":
            if os.uname()[4][0] == "a":
                args["connectorFile"] = "./" + connector_path + "_arm"
            else:
                args["connectorFile"] = "./" + connector_path
        else:
            args["connectorFile"] = "./" + connector_path + "_mac"
    return args


def get_from_terminal():
    """ Get arguments list

    Returns:
        [args] -- an array of settings
    """

    parser = argparse.ArgumentParser(
        description=DESCRIPTION)
    parser.add_argument("--port", default="/dev/ttyUSB0",
                        help="Serial port")
    parser.add_argument("--baudrate", default=-1,
                        help="Serial port")
    parser.add_argument("--server", default="ws://127.0.0.1:42000/ws",
                        help="Server url to send data to")
    parser.add_argument("--mysensors", default=True,
                        help="get Mysensors devices")
    parser.add_argument("--nogui", default=False, action="store_true",
                        help="Disable gui")
    #parser.add_argument("--unknown", default=True,
    #                    help="get unknown devices")
    parser.add_argument("--force", default=False,
                        help="Connect serial devices without detection", action="store_true")
    parser.add_argument("--libreobject", default=True,
                        help="get LibreObjects")
    parser.add_argument("--lineending", default="n",
                        help="Character to write at end of line Ex: NewLine(n) NL&CR (nr)")
    parser.add_argument("--id", default=0, help="do not change id is set automatically --> ex:madnerd/leds;madnerd/leds/0 etc...")
    parser.add_argument("--password", default=False,
                        help="Password for the websocket")
    parser.add_argument("--settings_file", default=SETTINGS_FILE,
                        help="Settings location")
    parser.add_argument("--name", default="serial")
    parser.add_argument("--retry", default=3, help="retry")
    parser.add_argument("--interval", default=2, help="Interval between USB scan")
    parser.add_argument("--debug", default=False, action="store_true",
                        help="Debug Mode")
    parser.add_argument("--connector", default="websocket", help="Select a connector (websocket)")
    parser.add_argument("--append", default="", help="Add a identifier at the end of channel, ex:madnerd/leds --> madnerd/leds/foo")

    args = vars(parser.parse_args())
    if args["debug"]:
        print("Arguments -------------")
        print(args)
    return args


def get_from_file(args_cmd):
    """ Get arguments from a INI Configuration File

    Arguments:
        args {[string]} -- An array previously parsed from command line

    Returns:
        args {[string]} -- Returns arguments
    """
    if os.path.isfile(args_cmd["settings_file"]):
        file = ConfigParser.ConfigParser()
        file.read(args_cmd["settings_file"])
        for name, arg in args_cmd.items():
            try:
                args_cmd[name] = file.get("settings", name)
            except ConfigParser.NoOptionError:
                pass
        if args_cmd["debug"]:
            print("Configuration File -------------")
            print(args_cmd)
    return args_cmd
