import sys
import json
import time
import os
import datetime
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import QTimer, QFile, QTextStream
from PyQt5.QtGui import QFont
from Ui_CheckWINCC import Ui_MainWindow
import threading
import func.UART

CMD_FRAME_HEADER = b'Z'  # 指令帧头定义 0x5A
RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59
BAUDRATE = [115200, 9600, 19200, 38400, 57600, 460800, 921600, 256000]  # 定义波特率列表


class MyMainWindow(QMainWindow, Ui_MainWindow):  # 继承QMainWindow类和Ui_Maindow界面类
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)  # 初始化父类
        self.setupUi(self)  # 继承 Ui_MainWindow 界面类
        self.namelist = []  # 初始化点击按钮对应操作名称的列表
        self.stdlist = []  # 初始化点击按钮对应期望值的列表
        self.vallist = []  # 初始化点击按钮对应显示值的列表
        self.returnlist = []  # 初始化点击按钮对应操作结果的列表
        self.cmdlist = []  # 初始化点击按钮对应发送指令的列表
        self.rxlist = []  # 初始化点击按钮对应接收指令的列表
        self.warning_shown = False  # 布尔变量，记录弹窗是否已经存在

    # 获取串口列表
    def getSerialPort(self):
        ports = serial.tools.list_ports.comports()
        if len(ports) == 0:
            self.comboBox_serial.addItem("-- 无串口 --")
            self.pushButton_connect.setEnabled(False)
        else:
            for port in reversed(ports):
                self.comboBox_serial.addItem(port.device)

    # 从串口接收3次帧头，检查当前波特率接收是否是数据帧
    def checkDataFrame(self):
        cnt = 0
        start_time = time.time()  # 记录开始时间
        while True:
            try:
                if self.ser.in_waiting:
                    for i in range(3):
                        self.ser.reset_input_buffer()
                        rxdata = self.ser.read(9)  # 读取一个完整的数据帧
                        print(i, 'rxdata:', rxdata.hex())
                        if RECV_FRAME_HEADER in rxdata or (rxdata[0] == 0x59 and rxdata[-1] == 0x59):
                            cnt += 1
                        self.ser.reset_input_buffer()
                    print('true cnt:', cnt)
                    if cnt > 0:  # 计数器不为零则返回True
                        return True
                    else:
                        return False
                else:
                    if (time.time() - start_time) > 0.1:  # 100ms内串口无数据
                        print('Timeout, ser has no data')
                        return False

            except Exception as e:
                print(type(e))
                print(e)

    # 轮询波特率列表
    def pollBaudrate(self):
        try:
            for baudrate in BAUDRATE:
                print('baudrate is:', baudrate)
                self.ser.baudrate = baudrate
                if self.checkDataFrame():  # 如果帧头检查正确，返回当前波特率值
                    print('------------------------------')
                    return baudrate
            self.ser.close()
            QMessageBox.warning(self, '提示', '串口无法打开，请检查！\n1.可能串口松了\n2.可能被其他程序占用\n3.转接板不支持当前波特率\n4.设备输出关闭')

        except Exception as e:
            print(type(e))
            print(e)
            if type(e) == serial.serialutil.SerialException:  # 如果转接板不支持当前波特率
                BAUDRATE.remove(baudrate)  # 从波特率列表中移除当前波特率
                print(BAUDRATE)
                for baudrate in BAUDRATE:
                    self.ser.baudrate = baudrate
                    if self.checkDataFrame():  # 如果帧头检查正确，返回当前波特率值
                        print('------------------------------')
                        return baudrate
                self.ser.close()
                QMessageBox.warning(self, '提示', '串口无法打开，请检查！\n1.可能串口松了\n2.可能被其他程序占用\n3.串口选择错误\n4.转接板不支持当前波特率\n5.设备输出关闭')

    # 连接按钮的信号和槽函数
    def connectSerial(self):
        try:
            self.ser = serial.Serial()
            select_port = self.comboBox_serial.currentText()  # 获取串口下拉列表值
            self.ser.port = select_port
            self.ser.timeout = 2
            self.ser.setRTS(False)  # 禁用RTS信号(IIC通信要禁用)
            self.ser.setDTR(False)
            self.ser.open()

            if self.comboBox_port.currentText() == 'UART':
                self.ser.baudrate = self.pollBaudrate()  # 通过轮询获取波特率值
            elif self.comboBox_port.currentText() == 'IIC':
                self.ser.baudrate = 9600
            elif self.comboBox_port.currentText() == 'RS485':
                print('RS485 baudrate')
            elif self.comboBox_port.currentText() == 'RS232':
                print('RS232 baudrate')

            print('seclect port is:', select_port)
            print('baudrate is:', self.ser.baudrate)
            # 串口连接按钮状态转换
            if self.pushButton_connect.text() == '连接串口':
                self.pushButton_connect.setText('已连接')
                self.pushButton_connect.setStyleSheet("background-color: yellow")
                self.comboBox_serial.setDisabled(True)
                self.comboBox_port.setDisabled(True)
                print('serial port is open')
            else:
                self.pushButton_connect.setText('连接串口')
                self.pushButton_connect.setStyleSheet("background-color: none")
                self.comboBox_serial.setDisabled(False)
                self.comboBox_port.setDisabled(False)
                self.ser.close()
                print('serial port is close')
            print('------------------------------')
            self.clearLabel()
        except Exception as e:
            print(type(e))
            print(e)
            if type(e) == serial.serialutil.SerialException:
                QMessageBox.warning(self, '提示', '串口无法打开，请检查！\n1.可能串口松了\n2.可能被其他程序占用\n3.转接板不支持当前波特率\n4.设备输出关闭')

    # 刷新按钮的信号和槽函数
    def refreshSerial(self):
        try:
            self.pushButton_connect.setEnabled(True)
            self.comboBox_serial.clear()
            myWin.getSerialPort()  # 获取串口列表
            if self.pushButton_connect.text() == '已连接':
                self.pushButton_connect.setText('连接串口')
                self.pushButton_connect.setStyleSheet("background-color: none")
                self.comboBox_serial.setDisabled(False)
                self.comboBox_port.setDisabled(False)
                self.ser.close()
                print('serial port is close')
            print('refresh serial port')
            print('------------------------------')
            self.clearLabel()
        except Exception as e:
            print(type(e))
            print(e)

    # 菜单栏打开的信号和槽函数
    def trigger_actOpen(self):
        try:
            # 打开文件对话框
            file_path, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'JSON Files (*.json)')
            if file_path:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)  # 从 JSON 文件中读取数据

                Cmdlist = []  # 指令保存列表
                self.labellist = []  # 标签名称列表
                self.labelStdlist = []  # 期望值列表
                self.labelChecklist = []  # 实际检查值列表
                self.widgetslist = []  # 组件列表
                self.buttonlist = []  # 按钮列表
                self.labelReturnlist = []  # 结果返回OK/NG标签列表

                # 根据JSON数据生成控件
                layout = QtWidgets.QGridLayout()
                layout.setColumnStretch(0, 1)  # 第一列宽度设置为1
                layout.setColumnStretch(1, 1)  # 第二列宽度设置为3
                layout.setColumnStretch(2, 1)  # 第三列宽度设置为1
                layout.setColumnStretch(3, 3)  # 第四列宽度设置为1
                layout.setColumnStretch(4, 1)  # 第五列宽度设置为1
                layout.setColumnStretch(5, 1)  # 第六列宽度设置为1

                for item in self.data:
                    Cmdlist.append(item['cmd'])  # 指令保存
                    print('cmd:', item['cmd'], item['id'])
                    # 自动保存name为QLabel
                    labelName = QtWidgets.QLabel(item['name'], self)
                    layout.addWidget(labelName, item['id'], 0)  # 第一列为检查项的名称
                    self.labellist.append(labelName)

                    labelStd = QtWidgets.QLabel('期望值:' + item['std'], self)
                    layout.addWidget(labelStd, item['id'], 1)  # 第二列为期望值
                    self.labelStdlist.append(labelStd)

                    labelCheck = QtWidgets.QLabel('检查值:', self)
                    layout.addWidget(labelCheck, item['id'], 2)  # 第三列为检查值
                    self.labelChecklist.append(labelCheck)

                    # 自动保存widget为各个类型
                    if item['widget'] == 'QLabel':
                        widget = QtWidgets.QLabel(self)
                        widget.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
                        layout.addWidget(widget, item['id'], 3)  # 第四列为不同类型组件
                    elif item['widget'] == 'QComboBox':
                        widget = QtWidgets.QComboBox(self)
                        widget.setEditable(True)
                        layout.addWidget(widget, item['id'], 3)  # 第四列为不同类型组件
                    elif item['widget'] == 'QLineEdit':
                        widget = QtWidgets.QLineEdit(self)
                        if item['name'] == '测距结果':
                            widget.setPlaceholderText("单位:cm")
                        layout.addWidget(widget, item['id'], 3)  # 第四列为不同类型组件
                    else:
                        print('widget is False')
                    self.widgetslist.append(widget)  # 将组件对象添加到组件列表中

                    # 自动保存button为QPushButton
                    button = QtWidgets.QPushButton(item['button'], self)  # 构造一个QPushButton对象，item['button']是按钮的文本，self是QWidget类型，表示父组件
                    layout.addWidget(button, item['id'], 4)  # 添加的控件对象为button，控件所在的行号为item['id']，控件所在的列号为4
                    self.buttonlist.append(button)  # 将按钮对象添加到按钮列表中
                    # 自动在按钮后添加一个返回QLabel
                    labelReturn = QtWidgets.QLabel('      ', self)  # 构造一个QLabel对象，'OK'是按钮的文本，self是QWidget类型，表示父组件
                    labelReturn.setFont(QFont("Arial", 8, QFont.Bold))  # 设置字体并加粗
                    layout.addWidget(labelReturn, item['id'], 5)  # 添加的控件对象为labelReturn，控件所在的行号为item['id']，控件所在的列号为5
                    self.labelReturnlist.append(labelReturn)  # 将标签对象添加到标签列表中

                print('Cmdlist:', Cmdlist)
                print('labellist:', self.labellist)
                print('widgetslist:', self.widgetslist)
                print('buttonlist:', self.buttonlist)
                print('labelReturnlist:', self.labelReturnlist)
                print('------------------------------')

                if not self.widget1.layout():
                    self.widget1.setLayout(layout)
                else:
                    QtWidgets.QWidget().setLayout(self.widget1.layout())  # 清除原有布局
                    self.widget1.setLayout(layout)  # 设置新布局

                # 连接指令按钮的点击信号和槽函数
                for button in self.buttonlist:
                    button.clicked.connect(self.sendCmd)
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.blinkLabel)  # 计时器结束调用闪烁标签效果
        except Exception as e:
            print(type(e))
            print(e)

    # 根据点击按钮的索引发送不同的指令
    def sendCmd(self):
        try:
            button = self.sender()  # 获取当前被点击的按钮
            self.index = self.buttonlist.index(button)  # 获取按钮在列表中的索引
            # 若需要发送指令则发送指令
            if self.data[self.index]['widget'] == 'QLabel':
                print('send cmd:', self.data[self.index]['cmd'])  # 获取对应的指令
                if self.data[self.index]['cmd'] != '':
                    self.labelCmdb = bytes.fromhex(self.data[self.index]['cmd'])
                    print('cmdb', self.labelCmdb)
                    self.ser.reset_input_buffer()
                    self.ser.write(self.labelCmdb)  # 发送指令
                    print('------------------------------')
            elif self.data[self.index]['widget'] == 'QLineEdit':
                self.editVal = self.widgetslist[self.index].text()  # 获取文本框输入值
                print('editVal:', self.editVal)
                self.lineEditCmd()
                self.ser.reset_input_buffer()
                #self.ser.write(self.newCmd)
            elif self.data[self.index]['widget'] == 'QComboBox':
                self.boxVal = self.widgetslist[self.index].currentText()  # 获取当前下拉列表值
                print('boxVal:', self.boxVal)
                self.comboBoxCmd()
                self.ser.reset_input_buffer()
                self.ser.write(self.newCmd)

            # 发送指令后对回显检查和接收处理，或检查无需发送指令的雷达配置
            if self.data[self.index]['cmd'] != '':
                self.recvData_UART()
                self.recvAnalysis_UART()
                self.recvJudge_UART()
            else:
                self.checkLabel_UART()  # 检查对应雷达配置
                #self.rx = b''
            self.timer.start(100)  # 启动计时器为100毫秒
            self.savelist()
            self.saveSetting()

        except Exception as e:
            print(e)
            print(type(e))
            self.labelReturnlist[self.index].setText('NG')
            self.labelReturnlist[self.index].setStyleSheet('color: red')
            if self.data[self.index]['widget'] == 'QLabel':
                self.widgetslist[self.index].setText('')
            if type(e) == AttributeError or type(e) == serial.serialutil.PortNotOpenError or type(e) == serial.serialutil.SerialException:
                # QMessageBox.warning(None, 'Error', '串口未连接或读取数据失败！')
                print(e)
            elif type(e) == ValueError or type(e) == IndexError:
                if self.data[self.index]['widget'] != 'QLabel':
                    QMessageBox.warning(None, 'Error', '检查输入值！')
            else:
                QMessageBox.warning(None, 'Error', str(e))

    # 清除组件标签内容以及返回标签内容
    def clearLabel(self):
        for widgetlabel in self.widgetslist:
            if type(widgetlabel) == QtWidgets.QLabel:
                widgetlabel.setText('')
        for returnlabel in self.labelReturnlist:
            returnlabel.setText('      ')
        self.label_return.setText('')

    # 计时器停止后，切换标签的可见性来实现闪烁效果
    def blinkLabel(self):
        if self.widgetslist[self.index].isVisible() and self.labelReturnlist[self.index].isVisible():
            self.widgetslist[self.index].setVisible(False)
            self.labelReturnlist[self.index].setVisible(False)
        else:
            self.widgetslist[self.index].setVisible(True)
            self.labelReturnlist[self.index].setVisible(True)
            self.timer.stop()

    # 发送指令后接收指令回显并判断 5A 帧头
    def recvData_UART(self):
        start_time = time.time()  # 记录开始时间
        while True:
            if self.ser.in_waiting:  # 如果串口有数据接收
                rxhead = self.ser.read(1)  # 读取一个字节，作为帧头
                print('rxhead:', rxhead, 'rxheadhex:', rxhead.hex())
                if rxhead == CMD_FRAME_HEADER:  # 判断帧头是否是0x5A
                    rxlen = self.ser.read(1)  # 若是读取一个长度字节
                    rxlenint = rxlen[0]  # 将bytes转为int
                    rxdata = self.ser.read(rxlenint - 2)  # 读取剩下的数据字节
                    self.rx = rxhead + rxlen + rxdata
                    print('rxlen', rxlen, 'rxdata:', rxdata, 'rx:', self.rx)
                    print('rxlenhex:', rxlen.hex(), 'rxlenint:', rxlenint, 'rxdatahex:', rxdata.hex())
                    print('rxhex:', ' '.join([hex(x)[2:].zfill(2) for x in self.rx]))
                    print('------------------------------')
                    break
                elif (time.time() - start_time) > 1:  # 数据接收超过 1s 都无帧头跳出循环
                    print('Timeout 1s, rx read 18 bytes')
                    self.rx = self.ser.read(18)  # 超时读取两个帧来观察
                    self.labelReturnlist[self.index].setText('NG')
                    self.labelReturnlist[self.index].setStyleSheet('color: red')
                    if self.data[self.index]['widget'] == 'QLabel':
                        self.widgetslist[self.index].setText('')
                    break
            else:
                if (time.time() - start_time) > 1:  # 超过 1s 都无数据接收跳出循环
                    print('Timeout 1s, empty rx')
                    self.rx = b''
                    self.labelReturnlist[self.index].setText('NG')
                    self.labelReturnlist[self.index].setStyleSheet('color: red')
                    if self.data[self.index]['widget'] == 'QLabel':
                        self.widgetslist[self.index].setText('')
                    break

    # 根据配置标签名称对rx进行处理和回显正误判断
    def recvAnalysis_UART(self):
        if self.data[self.index]['name'] == '序列号':
            if self.rx[2] == 0x12:
                SN_rxhex = self.rx[3:17]
                SN_rxstr = ''.join([chr(x) for x in SN_rxhex])
                self.widgetslist[self.index].setText(SN_rxstr)
                print('序列号是：', SN_rxstr)
                print('------------------------------')
        elif self.data[self.index]['name'] == '固件版本':
            if self.rx[2] == 0x01:
                version_rxhex = self.rx[3:6][::-1].hex()  # 取出字节数组并反转后转为十六进制
                # 每两个字符由hex转为int，用'.'连接为str
                version_rxstr = '.'.join(str(int(version_rxhex[i:i + 2], 16)) for i in range(0, len(version_rxhex), 2))
                self.widgetslist[self.index].setText(version_rxstr)
                print('固件版本是：', version_rxstr)
                print('------------------------------')
        elif self.data[self.index]['widget'] == 'QLabel':
            self.widgetslist[self.index].setText(' '.join([hex(x)[2:].zfill(2) for x in self.rx]))

    def recvJudge_UART(self):
        if self.data[self.index]['widget'] == 'QLabel' or self.data[self.index]['widget'] == 'QLineEdit':
            if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text != '':
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
            elif self.data[self.index]['std'] == self.widgetslist[self.index].text():
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
            else:
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')
        elif self.data[self.index]['widget'] == 'QComboBox':
            if self.data[self.index]['std'] == '' and self.widgetslist[self.index].currentText != '':
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
            elif self.data[self.index]['std'] == self.widgetslist[self.index].text():
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
            else:
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')



    def checkLabel_UART(self):
        func.UART.checkBaud_UART(self)
        func.UART.checkFrame_UART(self)
        func.UART.checkDis_UART(self)
        '''
        if self.data[self.index]['name'] == '波特率':
            self.widgetslist[self.index].setText(str(self.ser.baudrate))
            baud = str(self.ser.baudrate)
            stdbaud = self.data[self.index]['std']
            print('期望值:', stdbaud, '检查值', baud)
            if baud == stdbaud:
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
                print('Baudrate is Correct')
            else:
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')
                print('Baudrate is Error')
            self.rx = b''
            print('------------------------------')
        elif self.data[self.index]['name'] == '输出帧率':
            # 计算帧率
            self.ser.reset_input_buffer()
            start_time = time.time()
            frame_count = 0
            while True:
                rx = self.ser.read(9)
                if len(rx) == 9:
                    frame_count += 1
                endtime = time.time()
                time_diff = endtime - start_time
                if time_diff >= 1:
                    fps = frame_count / time_diff  # 计算帧率
                    print('Frame rate: {:.2f} Hz'.format(fps))
                    break
            # 判断帧率是否正确
            stdfps = int(self.data[self.index]['std'])
            stdfps_diff = 20
            if abs(fps - stdfps) <= stdfps_diff:
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
                print('Framerate is Correct')
            else:
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')
                print('Framerate is Error')
            self.widgetslist[self.index].setText(str(round(fps)) + ' (Hz)')
            self.rx = b''
            print('------------------------------')
        elif self.data[self.index]['name'] == '测距结果':
            if self.data[self.index]['std'] != '':
                stddis = int(self.data[self.index]['std'])
            else:
                stddis = 0
            stddis_diff = 10  # 允许测距误差范围
            start_time = time.time()  # 记录开始时间
            self.ser.reset_input_buffer()
            while True:
                if self.ser.in_waiting:
                    rxhead = self.ser.read(2)  # 读取一个字节，作为帧头
                    if rxhead == RECV_FRAME_HEADER:
                        rxdata = self.ser.read(7)  # 读取剩下数据字节
                        self.rx = rxhead + rxdata
                        print('rx:', ' '.join([hex(x)[2:].zfill(2) for x in self.rx]))
                        dist = int.from_bytes(self.rx[2:4], byteorder='little')
                        strength = int.from_bytes(self.rx[4:6], byteorder='little')
                        temp = int.from_bytes(self.rx[6:8], byteorder='little')
                        self.widgetslist[self.index].setText(str(dist) + ' (cm)')
                        print('------------------------------')
                        if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text != '':
                            self.labelReturnlist[self.index].setText('OK')
                            self.labelReturnlist[self.index].setStyleSheet('color: green')
                            print('Distance is Correct')
                        elif abs(stddis - dist) <= stddis_diff:
                            self.labelReturnlist[self.index].setText('OK')
                            self.labelReturnlist[self.index].setStyleSheet('color: green')
                            print('Distance is Correct')
                        else:
                            self.labelReturnlist[self.index].setText('NG')
                            self.labelReturnlist[self.index].setStyleSheet('color: red')
                            print('Distance is Error')
                        print('std disVal:', stddis, 'actual disVal:', dist)
                        break
                    elif (time.time() - start_time) > 1:  # 数据接收超过 1s 都无帧头跳出循环
                        print('Timeout 1s, rx read 18 bytes')
                        self.rx = self.ser.read(18)  # 超时读取两个帧来观察
                        self.labelReturnlist[self.index].setText('NG')
                        self.labelReturnlist[self.index].setStyleSheet('color: red')
                        if self.data[self.index]['widget'] == 'QLabel':
                            self.widgetslist[self.index].setText('')
                        break
                else:
                    if (time.time() - start_time) > 1:  # 超过 1s 都无数据接收跳出循环
                        print('Timeout 1s, empty rx')
                        self.rx = b''
                        self.labelReturnlist[self.index].setText('NG')
                        self.labelReturnlist[self.index].setStyleSheet('color: red')
                        if self.data[self.index]['widget'] == 'QLabel':
                            self.widgetslist[self.index].setText('')
                        break
        else:
            print('------------------------------')
        '''
    # 根据QLineEdit组件的输入值得到对应的新指令
    def lineEditCmd(self):
        '''
        priCmd = self.data[self.index]['cmd']
        print('priCmd:', priCmd)
        priCmdhex_list = priCmd.split()  # 字符串存进一个列表
        priCmdhead_str = priCmdhex_list[0]  # 帧头
        priCmdlen_str = priCmdhex_list[1]  # 帧总长度
        priCmdid_str = priCmdhex_list[2]  # 帧功能码
        priCmddata_list = priCmdhex_list[3:-1]  # 帧数据段
        priCmdsum_int = int(priCmdhead_str, 16) + int(priCmdlen_str, 16) + int(priCmdid_str, 16)  # 未加数据段的校验和
        print('priCmddata_list:', priCmddata_list)
        '''

        if self.data[self.index]['name'] == '测距结果':
            inpdisVal = int(self.editVal)  # 获取输入测距值
            dist_diff = 20
            rxhead = self.ser.read(2)  # 读取一个字节，作为帧头
            if rxhead == RECV_FRAME_HEADER:
                rxdata = self.ser.read(7)  # 读取剩下数据字节
                self.rx = rxhead + rxdata
                print('rx:', ' '.join([hex(x)[2:].zfill(2) for x in self.rx]))
                dist = int.from_bytes(self.rx[2:4], byteorder='little')
                strength = int.from_bytes(self.rx[4:6], byteorder='little')
                temp = int.from_bytes(self.rx[6:8], byteorder='little')
                print('------------------------------')
                if abs(inpdisVal - dist) <= dist_diff:
                    self.labelReturnlist[self.index].setText('OK')
                    self.labelReturnlist[self.index].setStyleSheet('color: green')
                    print('Distance is Correct')
                else:
                    self.labelReturnlist[self.index].setText('NG')
                    self.labelReturnlist[self.index].setStyleSheet('color: red')
                    print('Distance is Error')
            print('input disVal:', inpdisVal, 'actual disVal:', dist)
            self.newCmd = b''
        '''
        else:
            editVal_list = self.editVal.split()  # 将输入值转为一个列表
            for i in range(len(priCmddata_list)):
                priCmddata_list[i] = editVal_list[i]
                print(i, priCmddata_list[i], editVal_list[i])
            newCmddata_str = ''.join(editVal_list)
            print(newCmddata_str)
            newCmdsum_hexstr = hex(priCmdsum_int + sum(int(x, 16) for x in editVal_list))
            print(newCmdsum_hexstr)

        newCmdsum_str = str(newCmdsum_hexstr)[-2:]  # 取出校验和最后两位字符
        newCmdstr = priCmdhead_str + priCmdlen_str + priCmdid_str + newCmddata_str + newCmdsum_str  # 连接为更新后的指令字符串
        self.newCmd = bytes.fromhex(newCmdstr)  # 将指令字符串格式转为串口发送的字节格式
        print('newCmddata_str:', newCmddata_str)
        print('newCmdsum_hexstr:', newCmdsum_hexstr, 'newCmdsum_str:', newCmdsum_str)
        print('newCmdstr:', newCmdstr, 'newCmdbytes:', self.newCmd)
        print('------------------------------')
        '''
    # 根据QComboBox组件的输入值得到对应的新指令
    def comboBoxCmd(self):
        priCmd_list = self.data[self.index]['cmd']
        index = self.widgetslist[self.index].currentIndex()
        print('priCmd_list:', priCmd_list)
        comboboxCmd = priCmd_list[index]

        self.newCmd = bytes.fromhex(comboboxCmd)
        print('index:', index, 'comboboxCmd:', comboboxCmd, 'newCmdbytes:', self.newCmd)
        print('------------------------------')

    def checkAll(self):
        try:
            self.clearLabel()
            time.sleep(0.5)
            if self.comboBox_port.currentText() == 'UART':
                for button in self.buttonlist:
                    button.click()
                    QApplication.processEvents()  # 实时更新GUI
                    time.sleep(0.5)

            elif self.comboBox_port.currentText() == 'IIC':
                print('IIC')
            elif self.comboBox_port.currentText() == 'RS485':
                print('RS485')
            elif self.comboBox_port.currentText() == 'RS232':
                print('RS232')
            print('------------------------------')

            for label in self.labelReturnlist:  # 轮询返回标签
                if label.text() == 'OK':
                    self.label_return.setText('OK')
                    self.label_return.setStyleSheet('color: green')
                else:
                    self.label_return.setText('NG')
                    self.label_return.setStyleSheet('color: red')


        except Exception as e:
            print(e)
            print(type(e))
            if type(e) == AttributeError or type(e) == serial.serialutil.PortNotOpenError or type(e) == serial.serialutil.SerialException:
                QMessageBox.warning(None, 'Error', '串口未连接或读取数据失败！！')

    def checkIIC(self):
        if self.data[self.index]['name'] == 'I2C从机地址':
            start_time = time.time()
            self.ser = serial.Serial()
            self.ser.port = self.comboBox_serial.currentText()
            self.ser.baudrate = 9600
            self.ser.setRTS(False)  # 禁用RTS信号(IIC通信要禁用)
            self.ser.setDTR(False)  # 禁用DTR信号
            self.ser.open()
            time.sleep(0.1)
            self.ser.reset_input_buffer()  # 清空输入缓存区
            #self.ser.write(bytes.fromhex('53 20 05 5A 05 00 01 60 50 53 21 09 50'))

            Cmd = '53 W 05 5A 05 00 01 60 50 53 R 09 50'  # IIC测距指令
            for i in range(0, 128):
                Whex_i = hex((i << 1) & 0xFE)[2:].zfill(2).upper()  # 左移1位后最后位置0
                Rhex_i = hex((i << 1) | 0x01)[2:].zfill(2).upper()  # 左移1位后最后位置1
                NewCmd = Cmd.replace('W', Whex_i).replace('R', Rhex_i)
                print('i', i, '0xi:',hex(i)[2:].zfill(2), 'Whex_i:',Whex_i, 'Rhex_i:',Rhex_i,'NewCmd:',NewCmd)
                self.ser.write(bytes.fromhex(NewCmd))
                time.sleep(0.05)  # 等待 50 ms
                if self.ser.in_waiting:
                    rxIIC = self.ser.read(9)
                    if rxIIC[:2] == RECV_FRAME_HEADER:
                        print('IIC address is:', hex(i))
                        self.ser.close()
                        diff = time.time()-start_time
                        print('diff:',diff)
                        break
            print('------------------------------')

    # 保存每次点击按钮收发的数据为列表
    def savelist(self):
        self.namelist.append(self.data[self.index]['name'])
        self.stdlist.append(self.data[self.index]['std'])
        self.returnlist.append(self.labelReturnlist[self.index].text())
        self.rxlist.append(' '.join([hex(x)[2:].zfill(2) for x in self.rx]))
        if self.data[self.index]['widget'] == 'QLabel':
            self.vallist.append(self.widgetslist[self.index].text())
            self.cmdlist.append(self.data[self.index]['cmd'])
        elif self.data[self.index]['widget'] == 'QLineEdit':
            self.vallist.append(self.widgetslist[self.index].text())
            self.cmdlist.append(' '.join([hex(x)[2:].zfill(2) for x in self.newCmd]))
        elif self.data[self.index]['widget'] == 'QComboBox':
            self.vallist.append(self.widgetslist[self.index].currentText())
            self.cmdlist.append(' '.join([hex(x)[2:].zfill(2) for x in self.newCmd]))
        print(self.namelist, self.stdlist, self.vallist, self.returnlist, self.cmdlist, self.rxlist)

    # 保存每次设置的数据到txt文档中
    def saveSetting(self):
        # 定义txt文件名
        file_name = '{:03d}.txt'.format(self.lentxt + 1)
        # 定义待保存的文件路径（在新建的文件夹下）
        file_path = os.path.join(self.dir_path, file_name)
        # 打开文件写入数据
        with open(file_path, 'w') as f:
            for i in range(len(self.namelist)):
                f.write(self.namelist[i] + ': ' + '  期望值：' + self.stdlist[i] + '  检查值：' + self.vallist[i] + '    结果: ' + self.returnlist[i] + '\n' +
                        '发送cmd: ' + self.cmdlist[i].upper() + '\n' + '接收cmd: ' + self.rxlist[i].upper() + '\n' +
                        '------------------------------' + '\n')
        f.close()

    # 创建以当前日期命名的文件夹，检查当前目录下的txt文档，并获取要创建的txt文档的名称
    def gettxtname(self):
        # 获取当前日期，作为文件夹名字
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        # 定义待保存的文件夹路径（在程序目录下）
        self.dir_path = os.path.join(os.getcwd(), today)
        # 如果文件夹不存在，则创建文件夹
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        # 列出当前文件夹下的所有文件和文件夹
        files = os.listdir(self.dir_path)
        # 遍历文件列表，找出以".txt"结尾的文件
        txt_files = [file for file in files if file.endswith(".txt")]
        # 输出结果
        self.lentxt = len(txt_files)
        print("当前文件夹下有%d个txt文件:" % self.lentxt)
        for txt_file in txt_files:
            print(txt_file)

    def test_IIC(self):
        if self.ser.rts is False:  # IIC转接板卡死复位
            self.ser.setRTS(True)
            self.ser.setRTS(False)
            rx = self.ser.readall()
            if rx != b'':
                print(rx.hex())
            self.ser.close()        

if __name__ == '__main__':
    app = QApplication(sys.argv)  # 创建应用程序对象
    myWin = MyMainWindow()  # 实例化 MyMainWindow 类，创建主窗口
    myWin.show()  # 在桌面显示控件 myWin
    myWin.getSerialPort()  # 获取串口列表
    myWin.gettxtname()  # 获取创建的txt文档的名称

    sys.exit(app.exec_())  # 在主线程中退出
