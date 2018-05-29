from tkinter import *
import threading
import sys
import os
import socket
from tkinter import ttk
import Settings
global keep_scanning
args = Settings.get()

def goToSettings():
    print "settings"
    os.system("explorer settings")

def gui():
    global args
    # Create interface
    bg_grey = "#f3f3f3"
    root = Tk()
    try:
        root.iconbitmap('libreUSB.ico')
    except:
        print("No icon")
    root.title("Libre USB") #Title
    root.configure(background=bg_grey) #Background color
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    ent = ttk.Entry(root, state='readonly')
    var = StringVar()
    var.set(args["server"])
    ent.config(textvariable=var, width = 50,justify='center')
    ent.pack()

    ttk.Button(text="Exit", command=root.destroy ,width = 50).pack()
    ttk.Button(text="Settings", command=goToSettings ,width = 50).pack()
    root.mainloop()

gui_thread = threading.Thread(name="gui", target = gui)
gui_thread.daemon = True #If thread is not a daemon application could crashed
gui_thread.start()
