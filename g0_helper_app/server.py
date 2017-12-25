
from flask import Flask, request
import logging
import serial
import numpy as np
import threading
import time

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

def getValue(port):
    L = []
    try:
        with serial.Serial(port, 115200, timeout=0.03) as ser:
            ser.write('\x80')
            for i in range(14):
                # str object
                L.append(ord(ser.read()))
            ser.close()
    except Exception as e:
        L = [0] * 14
        return False
    print(L)
    if (L[0] == 1):
        device_state["wasButtonPressed/A"] = "true"
        device_state["wasButtonPressed/B"] = "false"
    elif (L[0] == 2):
        device_state["wasButtonPressed/A"] = "false"
        device_state["wasButtonPressed/B"] = "true"   
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

    return True


@app.route('/poll')
def poll():
    global is_scratch_connected_count
    is_scratch_connected_count += 1
    if not getValue(device_port):
        print(is_scratch_connected_count)
        return "_problem Helper app can not communicate with Grove Zero"
    else:
        return "\n".join(["{} {}".format(i, device_state[i]) for i in device_state])

@app.route('/displayText/<jobId>/<string:text>')
def display_text(jobId, text):
    if (device_port):
        with serial.Serial(device_port, 115200, timeout=0.2) as ser:
            s = '\x82\xf0\x04'
            count = 0
            for byte in text:
                s += '{}'.format(byte)
                count += 1
                if (count >= 26):
                    break
            s += '\xf7'
            ser.write(s)
            ser.close()
        addjobID(jobId, count)
        return "OK"
    else:
        return "ERROR"

@app.route('/displayNumber/<jobId>/<num>')
def display_number(jobId, num):
    if (device_port):
        with serial.Serial(device_port, 115200, timeout=0.2) as ser:
            s = '\x82\xf0\x04' 
            s += '{}'.format(num)
            s += '\xf7'
            ser.write(s)
            ser.close()
        addjobID(jobId, len('{}'.format(num)))        
        return "OK"
    else:
        return "ERROR"

gamut_dict = {"C3":1, "C#3":22, "D3":2, "D#3":23, "E3":3, "F3":4, "F#3":24, "G3":5, "G#3":25, "A3":6, "A#3":26, "B3":7,
               "C4":8, "C#4":27, "D4":9, "D#4":28, "E4":10, "F4":11, "F#4":29, "G4":12, "G#4":30, "A4":13, "A#4":31, "B4":14,
               "C5":15, "C#5":32, "D5":16, "D#5":33, "E5":17, "F5":18, "F#5":34, "G5":19, "G#5":35, "A5":20, "A#5":36, "B5":21}

# beat_dict = {"Whole":0, "Double":1, "Quadruple":2, "Octuple":3, "Half":4, "Quarter":5, "Eighth":6, "Sixteenth":7}
# beat_delay_dict = {"Whole":0.5, "Double":1, "Quadruple":2, "Octuple":4, "Half":0.25, "Quarter":0.13, "Eighth":0.07, "Sixteenth":0.04}

beat_dict = {"1":0, "2":1, "4":2, "8":3, "0.5":4, "0.25":5, "0.125":6, "0.0625":7}
beat_delay_dict = {"1":0.5, "2":1, "4":2, "8":4, "0.5":0.25, "0.25":0.13, "0.125":0.07, "0.0625":0.04}
@app.route('/playTone/<jobId>/<gamut>/<scale>/<beat>')
def play_tone(jobId, gamut, scale, beat):
    if (device_port):
        with serial.Serial(device_port, 115200, timeout=0.2) as ser:
            s = '\x81\xf0\x01'
            s += chr(gamut_dict[gamut+scale])
            s += chr(beat_dict[beat])
            s += '\xf7'
            ser.write(s)
            ser.close()
        addjobID(jobId, beat_delay_dict[beat])
        return "OK"
    else:
        return "ERROR"

melody_dict = {"BaDing":0, "Wawawawaa":1, "JumpUp":2, "JumpDown":3, "PowerUp":4, "PowerDown":5, "MagicWand":6, "Siren":7}
melody_delay_dict = {"BaDing":0.5, "Wawawawaa":2.63, "JumpUp":0.63, "JumpDown":0.63, "PowerUp":1.13, "PowerDown":1.13, "MagicWand":2, "Siren":3}

@app.route('/playMelody/<jobId>/<melody>')
def play_melody(jobId, melody):
    if (device_port):
        with serial.Serial(device_port, 115200, timeout=0.2) as ser:
            s = '\x81\xf0\x03'
            s += chr(melody_dict[melody])
            s += '\xf7'
            # print(s)
            ser.write(s)
            ser.close()
        addjobID(jobId, melody_delay_dict[melody])
        return "OK"
    else:
        return "ERROR"

def addjobID(jobID, delay):
    s = '_busy ' + str(jobID)
    device_state.setdefault(s, '')
    timer = threading.Timer(delay, deljobID, [jobID,])
    timer.start()

def deljobID(jobID):
    s = '_busy ' + str(jobID)
    device_state.pop(s)
    # timer = threading.Timer(1, addjobID, [jobID+1,])
    # timer.start()


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

def run():
    app.run('0.0.0.0', port=32781)

def terminate():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    # raise KeyboardInterrupt

def main():
    run()

if __name__ == '__main__':
    main()
