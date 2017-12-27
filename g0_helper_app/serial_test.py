import serial
import time
L = []
count = 0

def testSerial():
    global count
    L = []
    time0 = time.time()
    with serial.Serial("/dev/cu.usbmodem1411", 115200, timeout=0.2) as ser:
        try:
            # ser.write('\x80')
            ser.write(bytes([128]))
            for i in range(14):
                L.append(ord(ser.read()))
            # L = ser.read(size=100)
            print(L)
            ser.close()
        except TypeError as e:
            print(e)
        #     print("type error")            

    time0 = time.time() - time0
    if (time0 >= 0.1):
        print(time0)
        print(count)
    count += 1


def main():
    while True:
        testSerial()

if __name__ == '__main__':
    main()