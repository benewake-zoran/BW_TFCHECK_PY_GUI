# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'd:\北醒资料\Benewake_CheckWINCC\CheckWINCC.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(594, 653)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("d:\\北醒资料\\Benewake_CheckWINCC\\BenewakeLogo.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(0, 0, 591, 51))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.pushButton_connect = QtWidgets.QPushButton(self.frame)
        self.pushButton_connect.setGeometry(QtCore.QRect(380, 8, 100, 28))
        self.pushButton_connect.setAutoRepeat(False)
        self.pushButton_connect.setObjectName("pushButton_connect")
        self.label_serial = QtWidgets.QLabel(self.frame)
        self.label_serial.setGeometry(QtCore.QRect(10, 15, 41, 16))
        self.label_serial.setObjectName("label_serial")
        self.comboBox_serial = QtWidgets.QComboBox(self.frame)
        self.comboBox_serial.setGeometry(QtCore.QRect(45, 12, 80, 21))
        self.comboBox_serial.setObjectName("comboBox_serial")
        self.line = QtWidgets.QFrame(self.frame)
        self.line.setGeometry(QtCore.QRect(5, 30, 580, 41))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.pushButton_refresh = QtWidgets.QPushButton(self.frame)
        self.pushButton_refresh.setGeometry(QtCore.QRect(485, 8, 100, 28))
        self.pushButton_refresh.setObjectName("pushButton_refresh")
        self.comboBox_port = QtWidgets.QComboBox(self.frame)
        self.comboBox_port.setGeometry(QtCore.QRect(300, 12, 70, 22))
        self.comboBox_port.setObjectName("comboBox_port")
        self.comboBox_port.addItem("")
        self.comboBox_port.addItem("")
        self.comboBox_port.addItem("")
        self.comboBox_port.addItem("")
        self.label_port = QtWidgets.QLabel(self.frame)
        self.label_port.setGeometry(QtCore.QRect(265, 15, 41, 15))
        self.label_port.setObjectName("label_port")
        self.label_baud = QtWidgets.QLabel(self.frame)
        self.label_baud.setGeometry(QtCore.QRect(130, 15, 50, 16))
        self.label_baud.setObjectName("label_baud")
        self.comboBox_baud = QtWidgets.QComboBox(self.frame)
        self.comboBox_baud.setGeometry(QtCore.QRect(180, 12, 80, 22))
        self.comboBox_baud.setObjectName("comboBox_baud")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.comboBox_baud.addItem("")
        self.widget1 = QtWidgets.QWidget(self.centralwidget)
        self.widget1.setGeometry(QtCore.QRect(-1, 49, 591, 521))
        self.widget1.setObjectName("widget1")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(0, 570, 591, 41))
        self.widget.setObjectName("widget")
        self.pushButton_check = QtWidgets.QPushButton(self.widget)
        self.pushButton_check.setGeometry(QtCore.QRect(120, 0, 341, 28))
        self.pushButton_check.setObjectName("pushButton_check")
        self.label_return = QtWidgets.QLabel(self.widget)
        self.label_return.setGeometry(QtCore.QRect(490, 0, 51, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        self.label_return.setFont(font)
        self.label_return.setText("")
        self.label_return.setObjectName("label_return")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 594, 26))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionChinese = QtWidgets.QAction(MainWindow)
        font = QtGui.QFont()
        font.setUnderline(False)
        font.setKerning(False)
        self.actionChinese.setFont(font)
        self.actionChinese.setObjectName("actionChinese")
        self.actionEnglish = QtWidgets.QAction(MainWindow)
        self.actionEnglish.setObjectName("actionEnglish")
        self.menu.addAction(self.actionOpen)
        self.menu_2.addAction(self.actionChinese)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.actionEnglish)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUi(MainWindow)
        self.actionOpen.triggered.connect(MainWindow.trigger_actOpen) # type: ignore
        self.pushButton_connect.clicked.connect(MainWindow.connectSerial) # type: ignore
        self.pushButton_refresh.clicked.connect(MainWindow.refreshSerial) # type: ignore
        self.pushButton_check.clicked.connect(MainWindow.checkAll) # type: ignore
        self.actionChinese.triggered.connect(MainWindow.trigger_actChinese) # type: ignore
        self.actionEnglish.triggered.connect(MainWindow.trigger_actEnglish) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BW_CheckWINCC"))
        self.pushButton_connect.setText(_translate("MainWindow", "连接"))
        self.label_serial.setText(_translate("MainWindow", "串口"))
        self.pushButton_refresh.setText(_translate("MainWindow", "刷新"))
        self.comboBox_port.setItemText(0, _translate("MainWindow", "UART"))
        self.comboBox_port.setItemText(1, _translate("MainWindow", "IIC"))
        self.comboBox_port.setItemText(2, _translate("MainWindow", "RS485"))
        self.comboBox_port.setItemText(3, _translate("MainWindow", "RS232"))
        self.label_port.setText(_translate("MainWindow", "接口"))
        self.label_baud.setText(_translate("MainWindow", "波特率"))
        self.comboBox_baud.setItemText(0, _translate("MainWindow", "115200"))
        self.comboBox_baud.setItemText(1, _translate("MainWindow", "9600"))
        self.comboBox_baud.setItemText(2, _translate("MainWindow", "19200"))
        self.comboBox_baud.setItemText(3, _translate("MainWindow", "38400"))
        self.comboBox_baud.setItemText(4, _translate("MainWindow", "57600"))
        self.comboBox_baud.setItemText(5, _translate("MainWindow", "256000"))
        self.comboBox_baud.setItemText(6, _translate("MainWindow", "460800"))
        self.comboBox_baud.setItemText(7, _translate("MainWindow", "921600"))
        self.pushButton_check.setText(_translate("MainWindow", "一键检查"))
        self.menu.setTitle(_translate("MainWindow", "文件"))
        self.menu_2.setTitle(_translate("MainWindow", "语言"))
        self.actionOpen.setText(_translate("MainWindow", "打开"))
        self.actionOpen.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.actionChinese.setText(_translate("MainWindow", "中文"))
        self.actionEnglish.setText(_translate("MainWindow", "English"))
