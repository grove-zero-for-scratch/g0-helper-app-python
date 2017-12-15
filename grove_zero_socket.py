#! /usr/bin/python

# Scratch Hue Helper app
# ----------------------
# (c) 2015 Chris Proctor
# Distributed under the MIT license.
# Project homepage: http://mrproctor.net/scratch

from flask import Flask
# import Queue
from serial.tools.list_ports import *
import serial
# It's not generally good practice to disable warnings, but this is one of 
# the first scripts students will run, so I am prioritizing a reduction of
# any unnecessary output
import warnings
import logging
import time

warnings.filterwarnings("ignore")

app = Flask("g0_helper_app")
app.logger.removeHandler(app.logger.handlers[0])

# mission_queue = Queue.Queue()
device_state = {"wasButtonAPressed": "false", "wasButtonBPressed": "false", "lightValue" : 20,}
loggers = [app.logger, logging.getLogger('phue'), logging.getLogger('werkzeug')]
# No logging. Switch out handlers for logging.
# handler = logging.FileHandler('scratch_hue_extension.log')
handler = logging.NullHandler()
formatter = logging.Formatter('%(asctime)s - %(name)14s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
for logger in loggers:
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def findGroveZeroNormal():
    L = comports()

    for i in L:
        if (i.vid == 0x2886 and i.pid == 0x800d):
            device_path = str(i.device)
            # device_name = str(i.description) 
            # device_com = str(i.serial_number)  
            return (device_path)
    return None

def getValue(path):
    L = []
    try:
        with serial.Serial(path, 38400, timeout=1) as ser:
            ser.write('1')
            for i in range(6):
                # str object
                L.append(ord(ser.read()))
            ser.close()
    except Exception as e:
        L = [240, 0, 0, 0, 0, 247]
    print(L)
    if (L[1] == 1):
        device_state["wasButtonAPressed"] = "true"
    else:
        device_state["wasButtonAPressed"] = "false"
    if (L[2] == 1):
        device_state["wasButtonBPressed"] = "true"
    else:
        device_state["wasButtonBPressed"] = "false"
    device_state["lightValue"] = L[3] + L[4]*256

@app.route('/poll')
def poll():
    # return "wasButtonAPressed false\nwasButtonBPressed true\nlightValue 20\n"
    device_path = findGroveZeroNormal()
    if (device_path):
        getValue(device_path)
        return "\n".join(["{} {}".format(i, device_state[i]) for i in device_state])
    else:
        return "_problem Chrome helper app not communicating with grove zero"

@app.route('/displayText/<string:text>')
def display_text(text):
    # first_time = time.time()
    device_path = findGroveZeroNormal()
    if (device_path):
        # print(text)
        with serial.Serial(device_path, timeout=1) as ser:
            s = '\x32\xf0'
            # ser.write('\x32')
            # ser.write('\xf0')
            for byte in text:
                s += '{}'.format(byte)
                # s += '{:#x}'.format(ord(byte))
            # for byte in text:
            #     # ser.write(chr(ord(byte)))
            #     ser.write('\x61')
            #     # print(ord(byte))
            s += '\xf7'
            ser.write(s)
            ser.close()
            # print(s)
            # print(time.time()-first_time)
            return "OK"
    return "ERROR"

@app.route('/displayNumber/<num>')
def display_number(num):
    # print(num),
    device_path = findGroveZeroNormal()
    if (device_path):
        with serial.Serial(device_path, timeout=1) as ser:
            s = '\x32\xf0'
            s += '{}'.format(num)
            s += '\xf7'
            ser.write(s)
            ser.close()            
            return "OK"
    return "ERROR"

@app.route('/reset_all')
def reset_all():
    return "OK"

@app.route('/crossdomain.xml')
def cross_domain_check():
    return """
<cross-domain-policy>
    <allow-access-from domain="*" to-ports="12345"/>
</cross-domain-policy>
"""

print(" * The Scratch helper app for controlling Hue lights is running. Have fun :)")
print(" * See mrproctor.net/scratch for help.")
print(" * Press Control + C to quit.")
app.run('0.0.0.0', port=12345)
