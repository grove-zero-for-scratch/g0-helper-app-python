
from flask import Flask, request
import logging
import serial
import numpy as np
import threading
import time
try:
    import Queue
except ImportError:
    import queue as Queue

app = Flask("GroveZeroServer")
app.logger.removeHandler(app.logger.handlers[0])
handler = logging.NullHandler()
formatter = logging.Formatter('%(asctime)s - %(name)14s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
logging.getLogger('werkzeug').addHandler(handler)
logging.getLogger('werkzeug').setLevel(logging.INFO)

device_state ={"wasButtonPressed/A"    : "false", 
                "wasButtonPressed/B"    : "false", 
                "wasTilted/Up"          : "false",
                "wasTilted/Down"        : "false",
                "wasTilted/Left"        : "false",
                "wasTilted/Right"       : "false",
                "lightValue"            : 0,
                "soundValue"            : 0,
                "temperatureValue"      : 0,
                "accelerationValue/X"   : 0,
                "accelerationValue/Y"   : 0,
                "accelerationValue/Z"   : 0,}

device_port = ""
is_scratch_connected_count = np.int32(0)
task_q = Queue.Queue(maxsize = 30)
# result_q = Queue.Queue(maxsize = 100)
result_q = Queue.Queue(maxsize = 3)

class serialThread(threading.Thread):
    def __init__(self, task_queue, result_queue):
        threading.Thread.__init__(self)
        self.exit = False
        self.port = ''
        self.result_queue = result_queue
        self.task_queue = task_queue

    def work(self):
        try:
            # write command
            task = self.task_queue.get_nowait()
        except Queue.Empty:
            # read value
            task = 0
        # read sensors
        # 1. handle 4.4% timeout 
        # 2. TypeError(check firmware) --- discard data and report error
        # 3. check length of data --- discard data and report error
        if task == 0:
            L = []
            try:
                self.port = device_port
                with serial.Serial(self.port, 115200, timeout=0.2) as ser:
                    # ser.write('\x80')
                    ser.write(bytes([128]))
                    for i in range(14):
                        # str object
                        L.append(ord(ser.read()))
                    ser.close()
            except TypeError:
                L = [250] * 14
            except Exception:
                L = [251] * 14                
            
            if (len(L) != 14):
                L = [252] * 14

            try:
                self.result_queue.put_nowait(L)
                print("queue size: {}".format(self.result_queue.qsize()))
            except Queue.Full:
                pop = self.result_queue.get()
                self.result_queue.put(L)
                # pass
        # display or play music
        else:
            try:
                self.port = device_port
                with serial.Serial(self.port, 115200, timeout=0.2) as ser:
                    ser.write(task)
                    ser.close()
            except Exception as e:
                print(e)
                print("can't handle a task")

    def run(self):
        while not self.exit:
            self.work()

@app.route('/poll')
def poll():
    # scratch status various
    global is_scratch_connected_count
    is_scratch_connected_count += 1

    try:
        L = result_q.get_nowait()
    except Queue.Empty:
        device_state["wasButtonPressed/A"] = "false"
        device_state["wasButtonPressed/B"] = "false"
        device_state["wasTilted/Left"] = "false"
        device_state["wasTilted/Right"] = "false"
        device_state["wasTilted/Up"] = "false"
        device_state["wasTilted/Down"] = "false"
        return "\n".join(["{} {}".format(i, device_state[i]) for i in device_state])

    if (L[0] == 1):
        device_state["wasButtonPressed/A"] = "true"
        device_state["wasButtonPressed/B"] = "false"
    elif (L[0] == 2):
        device_state["wasButtonPressed/A"] = "false"
        device_state["wasButtonPressed/B"] = "true" 
    elif (L[0] == 250):
        print("_problem Helper app can not communicate with Grove Zero Error 250: port slow")
        return "_problem Helper app can not communicate with Grove Zero Error 250"
    elif (L[0] == 251):
        print("_problem Helper app can not communicate with Grove Zero Error 251: wrong firmware or no device")
        return "_problem Helper app can not communicate with Grove Zero Error 251"
    elif (L[0] == 252):
        print("_problem Helper app can not communicate with Grove Zero Error 252: unknown")
        return "_problem Helper app can not communicate with Grove Zero Error 252"
    else:
        device_state["wasButtonPressed/A"] = "false"
        device_state["wasButtonPressed/B"] = "false"

    device_state["temperatureValue"] = np.int16(L[1] + L[2]*256)
    device_state["lightValue"] = L[3] + L[4]*256
    device_state["soundValue"] = L[5] + L[6]*256

    device_state["wasTilted/Left"] = "false"
    device_state["wasTilted/Right"] = "false"
    device_state["wasTilted/Up"] = "false"
    device_state["wasTilted/Down"] = "false"
    
    if L[7] == 1:
        device_state["wasTilted/Left"] = "true"
    elif L[7] == 2:
        device_state["wasTilted/Right"] = "true"
    elif L[7] == 3:
        device_state["wasTilted/Up"] = "true"
    elif L[7] == 4:
        device_state["wasTilted/Down"] = "true"
    
    device_state["accelerationValue/X"] = np.int16(L[8] + L[9]*256)
    device_state["accelerationValue/Y"] = np.int16(L[10] + L[11]*256)
    device_state["accelerationValue/Z"] = np.int16(L[12] + L[13]*256)

    return "\n".join(["{} {}".format(i, device_state[i]) for i in device_state])


@app.route('/displayText/<jobId>/<string:text>')
def display_text(jobId, text):
    # s = '\x82\xf0\x04'
    s = bytes([130, 240, 4])
    count = 0
    for byte in text:
        # s += '{}'.format(byte)
        s += bytes(byte,'ascii')
        count += 1
        if (count >= 26):
            break
    # s += '\xf7'
    s += bytes([247])
    try:
        task_q.put_nowait(s)
        addjobID(jobId, count)
    except Queue.Full:
        print("task queue full")
    return "OK"


@app.route('/displayNumber/<jobId>/<num>')
def display_number(jobId, num):
    # s = '\x82\xf0\x04'
    s = bytes([130, 240, 4])
    # s += '{}'.format(num)
    s += bytes(num,'ascii')
    # s += '\xf7'
    s += bytes([247])
    try:
        task_q.put_nowait(s)
        addjobID(jobId, len('{}'.format(num)))
    except Queue.Full:
        print("task queue full")
    return "OK"

gamut_dict = {"C3":1, "C#3":22, "D3":2, "D#3":23, "E3":3, "F3":4, "F#3":24, "G3":5, "G#3":25, "A3":6, "A#3":26, "B3":7,
               "C4":8, "C#4":27, "D4":9, "D#4":28, "E4":10, "F4":11, "F#4":29, "G4":12, "G#4":30, "A4":13, "A#4":31, "B4":14,
               "C5":15, "C#5":32, "D5":16, "D#5":33, "E5":17, "F5":18, "F#5":34, "G5":19, "G#5":35, "A5":20, "A#5":36, "B5":21}

beat_dict = {"1":0, "2":1, "4":2, "8":3, "0.5":4, "0.25":5, "0.125":6, "0.0625":7}
beat_delay_dict = {"1":0.5, "2":1, "4":2, "8":4, "0.5":0.25, "0.25":0.13, "0.125":0.07, "0.0625":0.04}
@app.route('/playTone/<jobId>/<gamut>/<scale>/<beat>')
def play_tone(jobId, gamut, scale, beat):
    # s = '\x81\xf0\x01'
    # s += chr(gamut_dict[gamut+scale])
    # s += chr(beat_dict[beat])
    # s += '\xf7'
    s = bytes([129, 240, 1])
    s += bytes([gamut_dict[gamut+scale]])
    s += bytes([beat_dict[beat]])
    s += bytes([247])
    try:
        task_q.put_nowait(s)
        addjobID(jobId, beat_delay_dict[beat])
    except Queue.Full:
        print("task queue full")
    return "OK"

melody_dict = {"BaDing":0, "Wawawawaa":1, "JumpUp":2, "JumpDown":3, "PowerUp":4, "PowerDown":5, "MagicWand":6, "Siren":7}
melody_delay_dict = {"BaDing":0.5, "Wawawawaa":2.63, "JumpUp":0.63, "JumpDown":0.63, "PowerUp":1.13, "PowerDown":1.13, "MagicWand":2, "Siren":3}

@app.route('/playMelody/<jobId>/<melody>')
def play_melody(jobId, melody):
    # s = '\x81\xf0\x03'
    s = bytes([129, 240, 3])
    # s += chr(melody_dict[melody])
    s += bytes([melody_dict[melody]])
    # s += '\xf7'
    s += bytes([247])
    try:
        task_q.put_nowait(s)
        addjobID(jobId, melody_delay_dict[melody])
    except Queue.Full:
        print("task queue full")
    return "OK"

def addjobID(jobID, delay):
    s = '_busy ' + str(jobID)
    device_state.setdefault(s, '')
    timer = threading.Timer(delay, deljobID, [jobID,])
    timer.start()

def deljobID(jobID):
    s = '_busy ' + str(jobID)
    device_state.pop(s)

@app.route('/reset_all')
def reset_all():
    return "OK"

@app.route('/crossdomain.xml')
def cross_domain_check():
    return """
<cross-domain-policy>
    <allow-access-from domain="*" to-ports="32781"/>
</cross-domain-policy>
"""

t = serialThread(task_q, result_q)

def run():
    t.start()
    app.run('0.0.0.0', port=32781)

def terminate():
    t.exit = True
    # func = request.environ.get('werkzeug.server.shutdown')
    # if func is None:
        # raise RuntimeError('Not running with the Werkzeug Server')
    raise SystemExit
    # func()

def main():
    run()

if __name__ == '__main__':
    main()
