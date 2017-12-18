from serial.tools.list_ports import *
import serial
import time
import numpy as np
import threading

device_state = {"wasButtonPressed/A"    : "false", 
                "wasButtonPressed/B"    : "false", 
                "wasTilted/up"          : "false",
                "wasTilted/down"        : "false",
                "wasTilted/left"        : "false",
                "wasTilted/right"       : "false",
                "lightValue"            : 0,
                "soundValue"            : 0,
                "temperatureValue"      : 0,
                "accelerationValue/X"   : 0,
                "accelerationValue/Y"   : 0,
                "accelerationValue/Z"   : 0,}

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
        with serial.Serial(path, 115200, timeout=1) as ser:
            ser.write('\x80')
            for i in range(14):
                # str object
                L.append(ord(ser.read()))
            ser.close()
    except Exception as e:
        L = [0] * 14
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

    device_state["wasTilted/left"] = "false"
    device_state["wasTilted/right"] = "false"
    device_state["wasTilted/up"] = "false"
    device_state["wasTilted/down"] = "false"
    
    if L[7] == 1:
        device_state["wasTilted/left"] = "true"
    elif L[7] == 2:
        device_state["wasTilted/right"] = "true"
    elif L[7] == 3:
        device_state["wasTilted/up"] = "true"
    elif L[7] == 4:
        device_state["wasTilted/down"] = "true"
    
    device_state["accelerationValue/X"] = np.int16(L[8] + L[9]*256)
    device_state["accelerationValue/Y"] = np.int16(L[10] + L[11]*256)
    device_state["accelerationValue/Z"] = np.int16(L[12] + L[13]*256)



def writeLedMatrixText(path, text):
    try:
        with serial.Serial(path, 115200, timeout=1) as ser:
            s = '\x82\xf0\x04'
            count = 0
            for byte in text:
                s += '{}'.format(byte)
                count += 1
                if (count >= 26):
                    break
            s += '\xf7'
            print(s)
            ser.write(s)
            ser.close()
            return "OK"
    except Exception as e:
        return "ERROR"

# 0x03 melody = 0~7

melody_dict = {"BaDing":0, "Wawawawaa":1, "JumpUp":2, "JumpDown":3, "PowerUp":4, "PowerDown":5, "MagicWand":6, "Siren":7}
melody_delay_dict = {"BaDing":0.5, "Wawawawaa":2.63, "JumpUp":0.63, "JumpDown":0.63, "PowerUp":1.13, "PowerDown":1.13, "MagicWand":1, "Siren":3}

def writeBuzzerPlayMelody(path, melody):
    try:
        with serial.Serial(path, 115200, timeout=1) as ser:
            s = '\x81\xf0\x03'
            s += chr(melody_dict[melody])
            s += '\xf7'
            print(s)
            ser.write(s)
            ser.close()
            return "OK"
    except Exception as e:
        return "ERROR"    

gamut_dict = {"C3":1, "C#3":22, "D3":2, "D#3":23, "E3":3, "F3":4, "F#3":24, "G3":5, "G#3":25, "A3":6, "A#3":26, "B3":7,
               "C4":8, "C#4":27, "D4":9, "D#4":28, "E4":10, "F4":11, "F#4":29, "G4":12, "G#4":30, "A4":13, "A#4":31, "B4":14,
               "C5":15, "C#5":32, "D5":16, "D#5":33, "E5":17, "F5":18, "F#5":34, "G5":19, "G#5":35, "A5":20, "A#5":36, "B5":21}

beat_dict = {"Whole":0, "Double":1, "Quadruple":2, "Octuple":3, "Half":4, "Quarter":5, "Eighth":6, "Sixteenth":7}
beat_delay_dict = {"Whole":0.5, "Double":1, "Quadruple":2, "Octuple":4, "Half":0.25, "Quarter":0.13, "Eighth":0.07, "Sixteenth":0.04}

# 0x01
def writeBuzzerPlayTone(path, gamut, beat):
    try:
        with serial.Serial(path, 115200, timeout=1) as ser:
            s = '\x81\xf0\x01'
            s += chr(gamut_dict[gamut])
            s += chr(beat_dict[beat])
            s += '\xf7'
            print(s)
            ser.write(s)
            ser.close()
            return "OK"
    except Exception as e:
        return "ERROR"   


def addjobID(jobID):
    device_state.setdefault(str(jobID), '_wait')
    timer = threading.Timer(1, deljobID, [100,])
    timer.start()

def deljobID(jobID):
    device_state.pop(str(jobID))
    timer = threading.Timer(1, addjobID, [100,])
    timer.start()


def main():
    getValue(findGroveZeroNormal())
    print ("\n".join(["{} {}".format(i, device_state[i]) for i in device_state]))
    time.sleep(0.2)
    

if __name__ == '__main__':
    timer = threading.Timer(1, addjobID, [100,])
    timer.start()
    while True:
        main() 
    # main()