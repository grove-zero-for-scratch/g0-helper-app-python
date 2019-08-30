from serial.tools.list_ports import *

def scanGroveZero():
    L = comports()
    device_list = []

    for i in L:
        if (i.vid == 0x2886 and i.pid == 0x800d):
            device_path = str(i.device)
            # device_name = str(i.description) 
            # device_list.setdefault(device_path, device_name)
            device_list.append(device_path)
    return device_list


def isDeviceConnected(port):
    L = scanGroveZero()
    if port in L:
        return True
    else:
        return False
