import sys 
from PySide.QtCore import *
from PySide.QtGui import *

import scan
import time
import server
import thread



        

# class ledWidget(QWidget):
#     def __init__(self):
#         super(ledWidget, self).__init__()
#         # self.resize(275,50)
#         self.label = QLabel(self)
#         self.label.resize(275,50)
#         self.label.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
#         self.label.setStyleSheet("background-color: white")
        
#         self.led1 = myLabelWidget()
#         self.led2 = myLabelWidget()
#         self.led2.setColor(2)

#         self.grid = QVBoxLayout(self)
#         self.grid.addWidget(self.led1)
#         self.grid.addWidget(self.led2)
#         self.grid.addStretch(6)
    
    # def setColor(self, color):
    #     self.
    

    # def setText(self, Text):

class checkPortThread(QThread):
    printPortList = Signal(str)
    cleanPortList = Signal()

    def __init__(self, parent=None):
        super(checkPortThread, self).__init__(parent)
        self.exit = False
        self.now_list = []
        self.last_list = []
    
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
                    print("keep this port")
                else:
                    server.device_port = str(self.now_list[0])
                    print("change port to {}".format(server.device_port, ))
            except Exception as e:
                server.device_port = None
    
    def run(self):
        while not self.exit:
            self.scan()
            time.sleep(0.5)


class Window(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self)

        # set size
        self.setGeometry(300, 300, 300, 320)
        self.setWindowTitle('Grove Zero Helper')
        self.setMaximumSize(300,320)
        self.setMinimumSize(300,320)
        # self.setWindowFlags(Qt.FramelessWindowHint)

        # add font
        fontid1 = QFontDatabase.addApplicationFont('.\Resources\Quicksand\Quicksand-Medium.ttf')
        fontid2 = QFontDatabase.addApplicationFont('.\Resources\Quicksand\Quicksand-Bold.ttf')
        # print(fontid2)
        # print(QFontDatabase.applicationFontFamilies(fontid1))
        # print(QFontDatabase.applicationFontFamilies(fontid2))        
        # self.setFont('Quicksand Medium')
        self.setFont('Quicksand')

        #background
        self.lb1 = QLabel(self)
        self.background_pic = QPixmap('.\Resources\\background.png')
        self.lb1.resize(300,320)
        self.lb1.setPixmap(self.background_pic)
        self.lb1.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        
        #label1 label2
        self.label1 = QLabel(self)
        self.label2 = QLabel(self)
        self.label1.setText('Main Board is connected')
        self.label2.setText('Scratch is connected')
        self.label1.move(40,260)
        self.label2.move(40,275)

        #led1 led2
        self.led1 = QLabel(self)
        self.led2 = QLabel(self)
        self.green_point = QPixmap('.\Resources\\green.png')
        self.red_point = QPixmap('.\Resources\\red.png')
        self.led1.setPixmap(self.green_point)
        self.led1.move(300-17-11-20,264)
        self.led2.setPixmap(self.green_point) 
        self.led2.move(300-17-11-20,279)

        #button
        # self.button = QPushButton("Stop server", self)

        #combo
        self.combo_board = QComboBox(self)
        self.combo_port = QComboBox(self)
        
        self.combo_board.addItem("Grove Zero")
        self.combo_board.resize(120, 35)
        self.combo_board.move(90,50+17+30)

        self.combo_port.resize(120, 35)
        self.combo_port.move(90,50+17+35+17+30)

        # check port thread
        self.check_port_thread = checkPortThread()
        self.check_port_thread.printPortList.connect(self.comboSlot)
        self.check_port_thread.cleanPortList.connect(self.combo_port.clear)
        self.check_port_thread.start()
        self.combo_port.activated[str].connect(self.changePort)
        thread.start_new_thread(server.run, ())

    @Slot(str)
    def changePort(self, s):
        # global server.port
        try:
            server.device_port = s
            print(server.port)
        except Exception:
            pass

    
    @Slot(str)
    def comboSlot(self, s):
        self.combo_port.addItem(s)


    # @Slot()
    # def startServer(self):
    #     pass
        # self.server.terminate()
    @Slot(int)
    def changeLed1(self, color):
        if color == 2:
            self.led1.setPixmap(self.green_point)
        else:
            self.led1.setPixmap(self.red_point)

    @Slot(int)
    def changeLed1(self, color):
        if color == 2:
            self.led1.setPixmap(self.green_point)
        else:
            self.led1.setPixmap(self.red_point)

    # @Slot(str)
    # def changelabel1(self, text):

    # @Slot(str)
    # def changelabel1(self, text):

    
    def closeEvent(self, event):
        if self.check_port_thread.isRunning():
            self.check_port_thread.exit = True
            while self.check_port_thread.isRunning():
                pass
        server.terminate()
        event.accept()

# class myLabelWidget(QWidget):
#     def __init__(self):
#         super(myLabelWidget, self).__init__()
#         # self.setFont('Quicksand')

#         self.label_1 = QLabel(self)
#         self.text = "hello"
#         self.label_1.setText(self.text)

#         self.label_2 = QLabel(self)
#         self.color = 1  # 1-red 2-green
#         self.red_point = QPixmap('.\Resources\\green.png')
#         self.green_point = QPixmap('.\Resources\\red.png')
#         self.setColor(self.color)

#         self.grid = QHBoxLayout(self)
#         self.grid.addWidget(self.label_1)
#         self.grid.addStretch(6)
#         self.grid.addWidget(self.label_2)
#         self.show()
    
#     def setText(self, text):
#         self.label_1.setText(text)

#     def setColor(self, color):
#         if color == 1:
#             self.label_2.setPixmap(self.red_point)
#         else:
#             self.label_2.setPixmap(self.green_point)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Window()
    ui.show()
    sys.exit(app.exec_())