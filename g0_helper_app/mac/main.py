#coding:utf-8
import sys 
# from PySide.QtCore import *
# from PySide.QtGui import *
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QWidget, QFrame
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QPixmap, QFontDatabase
import os

import scan
import time
# import server
import server_new as server
import _thread as thread


class checkPortThread(QThread):
    printPortList = pyqtSignal(str)
    cleanPortList = pyqtSignal()
    isScratchConnect = pyqtSignal(int)
    isDeviceConnect = pyqtSignal(int)

    def __init__(self, parent=None):
        super(checkPortThread, self).__init__(parent)
        self.exit = False
        self.now_list = []
        self.last_list = []
        self.last_count = 0
        self.scratch_status_flag = False
    
    def scan(self):
        self.now_list = scan.scanGroveZero()
        # print(self.now_list)
        if (self.last_list != self.now_list):
            self.last_list = self.now_list
            self.cleanPortList.emit()
            # server.device_port = None
            for i in self.now_list:
                self.printPortList.emit(str(i))
                # print("come in")
            try:
                if (server.device_port in self.now_list) and (server.device_port != None):
                    # light green led
                    self.isDeviceConnect.emit(1)
                    print("keep this port")
                else:
                    server.device_port = str(self.now_list[0])
                    # when now_list is empty, ERROR will raise
                    # light green led
                    self.isDeviceConnect.emit(1)
                    print("change port to {}".format(server.device_port, ))
            except Exception as e:
                server.device_port = None
                # light red led
                self.isDeviceConnect.emit(0)
    
    def checkScratch(self):
        if (server.is_scratch_connected_count != self.last_count):
            # connecting
            self.last_count = server.is_scratch_connected_count
            if not self.scratch_status_flag:
                self.isScratchConnect.emit(1)
                self.scratch_status_flag = True
        else:
            # not connect
            if self.scratch_status_flag:
                self.isScratchConnect.emit(0)
                self.scratch_status_flag = False

    def run(self):
        while not self.exit:
            self.scan()
            self.checkScratch()
            time.sleep(0.5)


class Window(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self)

        if getattr(sys, 'frozen', False):
            self.macpath = os.path.dirname(sys.executable)
        else:
            self.macpath = os.path.dirname(os.path.realpath(__file__))

        # set size
        self.setGeometry(300, 300, 300, 320)
        self.setWindowTitle('Grove Zero Helper')
        self.setMaximumSize(300,320)
        self.setMinimumSize(300,320)
        # self.setWindowFlags(Qt.FramelessWindowHint)

        # add font
        fontid1 = QFontDatabase.addApplicationFont('{}/../Resources/Quicksand/Quicksand-Medium.ttf'.format(self.macpath))
        fontid2 = QFontDatabase.addApplicationFont('{}/../Resources/Quicksand/Quicksand-Bold.ttf'.format(self.macpath))
        # print(fontid2)
        # print(QFontDatabase.applicationFontFamilies(fontid1))
        # print(QFontDatabase.applicationFontFamilies(fontid2))        
        # self.setFont('Quicksand Medium')
        # QFont('Quicksand')
        self.setFont(QFont('Quicksand'))

        #background
        self.lb1 = QLabel(self)
        self.background_pic = QPixmap('{}/../Resources/background.png'.format(self.macpath))
        self.lb1.resize(300,320)
        self.lb1.setPixmap(self.background_pic)
        self.lb1.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        
        #label1 label2
        self.label1 = QLabel(self)
        self.label2 = QLabel(self)
        self.label1.setText('Main Board is not connected')
        self.label2.setText('Scratch is not connected')
        self.label1.move(40,260)
        self.label2.move(40,275)

        #led1 led2
        self.led1 = QLabel(self)
        self.led2 = QLabel(self)
        self.green_point = QPixmap('{}/../Resources/green.png'.format(self.macpath))
        self.red_point = QPixmap('{}/../Resources/red.png'.format(self.macpath))
        self.led1.setPixmap(self.red_point)
        self.led1.move(252,264)
        self.led2.setPixmap(self.red_point) 
        self.led2.move(252,279)

        #combo
        self.combo_board = QComboBox(self)
        self.combo_port = QComboBox(self)
        
        self.combo_board.addItem("Grove Zero")
        self.combo_board.resize(120, 35)
        self.combo_board.move(90, 97)

        self.combo_port.resize(120, 35)
        self.combo_port.move(90, 149)

        # check port thread
        self.check_port_thread = checkPortThread()
        self.check_port_thread.printPortList.connect(self.comboSlot)
        self.check_port_thread.cleanPortList.connect(self.combo_port.clear)
        self.check_port_thread.start()
        self.combo_port.activated[str].connect(self.changePort)

        # start http server
        thread.start_new_thread(server.run, ())

        # check is scratch connected
        self.check_port_thread.isScratchConnect.connect(self.updateScratchStatus)
        self.check_port_thread.isDeviceConnect.connect(self.updateDeviceStatus)

    # @Slot(str)
    def changePort(self, s):
        # global server.port
        try:
            server.device_port = s
            print(server.device_port)
        except Exception as e:
            print(e)

    # @Slot(int)
    def updateScratchStatus(self, num):
        if num == 1:
            self.led2.setPixmap(self.green_point)
            self.label2.setText('Scratch is connected')
        else:
            self.led2.setPixmap(self.red_point)
            self.label2.setText('Scratch is not connected')

    # @Slot(int)
    def updateDeviceStatus(self, num):
        if num == 1:
            self.led1.setPixmap(self.green_point)
            self.label1.setText('Main Board is connected')
        else:
            self.led1.setPixmap(self.red_point)
            self.label1.setText('Main Board is not connected')

    # @Slot(str)
    def comboSlot(self, s):
        self.combo_port.addItem(s)

    def closeEvent(self, event):
        if self.check_port_thread.isRunning():
            self.check_port_thread.exit = True
            while self.check_port_thread.isRunning():
                pass
        server.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Window()
    ui.show()
    sys.exit(app.exec_())