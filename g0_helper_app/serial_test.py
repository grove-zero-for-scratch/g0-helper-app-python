import serial
import time
L = []
count = 0

def testSerial():
    global count
    L = []
    time0 = time.time()
    with serial.Serial("COM3", 115200, timeout=0.005) as ser:
        try:
            ser.write('\x80')
            for i in range(14):
                L.append(ord(ser.read()))
            # L = ser.read(size=100)
        except TypeError:
            print("type error")
        finally:
            ser.close()

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