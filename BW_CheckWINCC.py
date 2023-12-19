import sys
import json
import time
import os
import datetime
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QWidget, QMessageBox
from PyQt5.QtCore import QTimer, QTranslator
from PyQt5.QtGui import QFont
from Ui_CheckWINCC import Ui_MainWindow
import func.UART
import func.IIC
import func.MODBUS
import func.RS232

CMD_FRAME_HEADER = b'Z'  # 指令帧头定义 0x5A
RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59


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

        self.widgetslist = []  # 组件列表
        self.labelReturnlist = []  # 结果返回OK/NG标签列表

        self.address = None
        self.SlaveID = None
        self.Skipflag = False
        self.rx = b''
        self.IICCmd = ''
        self.MODBUSCmd = b''

        self.trans = QTranslator()  # 翻译家
        self.ENFlag = False  # 英文界面标识

    # 在调整窗口大小时触发自动调整QWidget的大小和位置
    def resizeEvent(self, event):
        self.widget1.setGeometry(15, 50, self.width() - 30, self.height() - 130)

    # 获取串口列表
    def getSerialPort(self):
        ports = serial.tools.list_ports.comports()
        if len(ports) == 0:
            self.comboBox_serial.addItem("None")
            self.pushButton_connect.setEnabled(False)
        else:
            for port in reversed(ports):
                self.comboBox_serial.addItem(port.device)

    # 连接按钮的信号和槽函数
    def connectSerial(self):
        try:
            self.ser = serial.Serial()
            select_port = self.comboBox_serial.currentText()  # 获取串口下拉列表值
            self.ser.port = select_port
            self.ser.baudrate = self.comboBox_baud.currentText()  # 获取波特率下拉列表值
            self.ser.timeout = 1
            self.ser.setRTS(False)  # 禁用RTS信号(IIC通信要禁用)
            self.ser.setDTR(False)
            self.ser.open()

            print('seclect port is:', select_port)
            print('baudrate is:', self.ser.baudrate)
            # 串口连接按钮状态转换
            if self.pushButton_connect.text() == '连接' or self.pushButton_connect.text() == 'connect':
                if self.ENFlag is False:
                    self.pushButton_connect.setText('已连接')
                elif self.ENFlag is True:
                    self.pushButton_connect.setText('connecting')
                self.pushButton_connect.setStyleSheet("background-color: yellow")
                self.comboBox_serial.setDisabled(True)
                self.comboBox_port.setDisabled(True)
                self.comboBox_baud.setDisabled(True)
                print('serial port is open')
            else:
                if self.ENFlag is False:
                    self.pushButton_connect.setText('连接')
                elif self.ENFlag is True:
                    self.pushButton_connect.setText('connect')
                self.pushButton_connect.setStyleSheet("background-color: none")
                self.comboBox_serial.setDisabled(False)
                self.comboBox_port.setDisabled(False)
                self.comboBox_baud.setDisabled(False)
                self.ser.close()
                print('serial port is close')
            print('------------------------------')
            self.clearLabel()
        except Exception as e:
            print(type(e))
            print(e)
            if type(e) == serial.serialutil.SerialException:
                if self.ENFlag is False:
                    QMessageBox.warning(self, '提示', '串口无法打开，请检查！\n1.可能串口松了\n2.可能被其他程序占用\n3.转接板不支持当前波特率')
                elif self.ENFlag is True:
                    QMessageBox.warning(self, 'Warning', 'The serial port cannot be opened. Please check!\n1.Maybe the serial port is loose.\n2.May be used by other programs.\n3.May be the switch board does not support the current baud rate.')

    # 刷新按钮的信号和槽函数
    def refreshSerial(self):
        try:
            self.pushButton_connect.setEnabled(True)
            self.comboBox_serial.clear()
            myWin.getSerialPort()  # 获取串口列表
            if self.pushButton_connect.text() == '已连接' or self.pushButton_connect.text() == 'connecting':
                if self.ENFlag is False:
                    self.pushButton_connect.setText('连接')
                elif self.ENFlag is True:
                    self.pushButton_connect.setText('connect')
                self.pushButton_connect.setStyleSheet("background-color: none")
                self.comboBox_serial.setDisabled(False)
                self.comboBox_port.setDisabled(False)
                self.comboBox_baud.setDisabled(False)
                if self.comboBox_port.currentText() == 'IIC':
                    func.IIC.refresh_IIC(self)  # 复位IIC转接板
                self.ser.close()
                print('serial port is close')
            print('refresh serial port')
            print('------------------------------')
            self.clearLabel()
            self.rx = b''

        except Exception as e:
            print(type(e))
            print(e)

    # 菜单栏下切换为中文界面
    def trigger_actChinese(self):
        try:
            self.pushButton_refresh.click()
            print('trigger actChinese')
            self.trans.load('translate/zh_CN')
            _app = QApplication.instance()  # 获取 app 实例
            _app.installTranslator(self.trans)
            self.retranslateUi(self)  # 重新翻译 Ui 界面
            self.ENFlag = False
            # self.actionOpen.trigger()
        except Exception as e:
            print(type(e))
            print(e)

    # 菜单栏下切换为英文界面
    def trigger_actEnglish(self):
        try:
            self.pushButton_refresh.click()
            print('trigger actEnglish')
            self.trans.load('translate/EN')
            _app = QApplication.instance()
            _app.installTranslator(self.trans)
            self.retranslateUi(self)
            self.ENFlag = True
            # self.actionOpen.trigger()
        except Exception as e:
            print(type(e))
            print(e)

    # 帮助菜单栏下打开帮助文档
    def trigger_actHelp(self):
        try:
            # current_path = os.path.abspath(os.path.dirname(__file__))  # 获取当前路径
            # html_path = os.path.join(current_path, 'help', 'help.html')  # 拼接帮助文件路径
            # os.startfile(html_path)
            os.startfile('help\help.html')
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

                    if self.ENFlag is False:
                        labelStd = QtWidgets.QLabel('期望值:' + item['std'], self)
                        labelCheck = QtWidgets.QLabel('检查值:', self)
                    elif self.ENFlag is True:
                        labelStd = QtWidgets.QLabel('StdVal:' + item['std'], self)
                        labelCheck = QtWidgets.QLabel('CheckVal:', self)
                    layout.addWidget(labelStd, item['id'], 1)  # 第二列为期望值
                    self.labelStdlist.append(labelStd)
                    layout.addWidget(labelCheck, item['id'], 2)  # 第三列为检查值
                    self.labelChecklist.append(labelCheck)

                    # 自动保存widget为各个类型
                    if item['widget'] == 'QLabel':
                        widget = QtWidgets.QLabel('', self)
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
            if self.pushButton_connect.text() == '连接' or self.pushButton_connect.text() == 'connect':
                if self.ENFlag is False:
                    QMessageBox.warning(None, 'Error', '串口未连接!')
                elif self.ENFlag is True:
                    QMessageBox.warning(None, 'Error', 'The serial port is not connected!')
            else:
                button = self.sender()  # 获取当前被点击的按钮
                self.index = self.buttonlist.index(button)  # 获取按钮在列表中的索引

                if self.comboBox_port.currentText() == 'UART':
                    func.UART.sendCmd_UART(self)
                    self.check_UART()  # 检查UART对应雷达配置
                elif self.comboBox_port.currentText() == 'IIC':
                    func.IIC.sendCmd_IIC(self)
                    self.check_IIC()  # 检查IIC对应雷达配置
                elif self.comboBox_port.currentText() == 'RS485':
                    func.MODBUS.sendCmd_MODBUS(self)
                    self.check_MODBUS()
                elif self.comboBox_port.currentText() == 'RS232':
                    func.RS232.sendCmd_RS232(self)
                    self.check_RS232()

                self.timer.start(100)  # 启动计时器为100毫秒
                # self.savelist()
                # self.saveSetting()

        except Exception as e:
            print(e)
            print(type(e))
            self.labelReturnlist[self.index].setText('NG')
            self.labelReturnlist[self.index].setStyleSheet('color: red')
            if self.data[self.index]['widget'] == 'QLabel':
                self.widgetslist[self.index].setText('')
            if type(e) == AttributeError or type(e) == serial.serialutil.PortNotOpenError or type(e) == serial.serialutil.SerialException:
                if self.ENFlag is False:
                    QMessageBox.warning(None, 'Error', '串口未连接或读取数据失败！')
                elif self.ENFlag is True:
                    QMessageBox.warning(None, 'Error', 'The serial port is not connected or data fails to be read.')
                print(e)

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

    def check_UART(self):
        # 发送指令后对回显检查和接收处理，或检查无需发送指令的雷达配置
        if self.data[self.index]['cmd'] != '':
            if self.data[self.index]['name'] == '测距结果' or self.data[self.index]['name'] == 'RangingResult': #特殊情况，单次测距的时候
                func.UART.checkDis_UART(self)
            else:
                func.UART.recvData_UART(self)
                func.UART.recvAnalysis_UART(self)
                func.UART.recvJudge_UART(self)           
        else:
            if self.data[self.index]['name'] == '输出帧率' or self.data[self.index]['name'] == 'FrameRate':
                func.UART.checkFrame_UART(self)
            elif self.data[self.index]['name'] == '测距结果' or self.data[self.index]['name'] == 'RangingResult':
                func.UART.checkDis_UART(self)
            else:
                func.UART.checkOther_UART(self)

    def check_IIC(self):
        if self.data[self.index]['cmd'] != '':
            func.IIC.recvData_IIC(self)
            func.IIC.recvAnalysis_IIC(self)
            func.IIC.recvJudge_IIC(self)
        else:
            if self.data[self.index]['name'] == 'I2C从机地址' or self.data[self.index]['name'] == 'I2C Address':
                func.IIC.checkAddress_IIC(self)
            elif self.data[self.index]['name'] == '测距结果' or self.data[self.index]['name'] == 'RangingResult':
                func.IIC.checkDistance_IIC(self)
            else:
                func.IIC.checkOther_IIC(self)

    def check_MODBUS(self):
        if self.data[self.index]['cmd'] != '':
            func.MODBUS.recvData_MODBUS(self)
            func.MODBUS.recvAnalysis_MODBUS(self)
            func.MODBUS.recvJudge_MODBUS(self)
        else:
            if self.data[self.index]['name'] == 'SlaveID':
                func.MODBUS.checkSlaveID_MODBUS(self)
            elif self.data[self.index]['name'] == '输出帧率' or self.data[self.index]['name'] == 'FrameRate':
                if self.Skipflag is False:
                    func.MODBUS.checkFramerate_MODBUS(self)
            else:
                func.MODBUS.checkOther_MODBUS(self)

    def check_RS232(self):
        if self.data[self.index]['cmd'] != '':
            func.RS232.recvData_RS232(self)
            func.RS232.recvAnalysis_RS232(self)
            func.RS232.recvJudge_RS232(self)
        else:
            if self.data[self.index]['name'] == '输出帧率' or self.data[self.index]['name'] == 'FrameRate':
                func.RS232.checkFrame_RS232(self)
            elif self.data[self.index]['name'] == '测距结果' or self.data[self.index]['name'] == 'RangingResult':
                func.RS232.checkDis_RS232(self)
            else:
                func.RS232.checkOther_RS232(self)

    def checkAll(self):
        try:
            if self.pushButton_connect.text() == '连接' or self.pushButton_connect.text() == 'connect':
                if self.ENFlag is False:
                    QMessageBox.warning(None, 'Error', '串口未连接!')
                elif self.ENFlag is True:
                    QMessageBox.warning(None, 'Error', 'The serial port is not connected!')
            else:
                self.clearlist()
                NGflag = False
                self.Skipflag = True
                self.clearLabel()
                time.sleep(1)
                for button in self.buttonlist:
                    QApplication.processEvents()
                    time.sleep(0.5)
                    button.click()
                    if self.widgetslist[self.index].text() == '':  # 若接收失败等待1s后尝试再次检验以增加稳定性
                        time.sleep(1)
                        button.click()
                        if self.widgetslist[self.index].text() == '':  # 若接收失败等待3s后尝试再次检验以增加稳定性
                            time.sleep(1)
                            button.click()
                            if self.widgetslist[self.index].text() == '':  # 若仍无接收则退出循环不再检验
                                break
                    #if 
                    # QApplication.processEvents()  # 实时更新GUI
                    # time.sleep(0.5)
                    self.savelist()  # 保存检查结果
                print('------------------------------')
                self.Skipflag = False

                for label in self.labelReturnlist:  # 轮询返回标签
                    if label.text() == 'NG':
                        NGflag = True
                        break
                if NGflag is False:
                    self.label_return.setText('OK')
                    self.label_return.setStyleSheet('color: green')
                else:
                    self.label_return.setText('NG')
                    self.label_return.setStyleSheet('color: red')

                self.gettxtname()  # 搜素文件夹下的 txt 文件
                self.saveSetting()  # 将检查的数据写入到 txt 文件中

        except Exception as e:
            print(e)
            print(type(e))

    # 清空 txt 文档的数据
    def clearlist(self):
        self.namelist = []
        self.stdlist = []
        self.vallist = []
        self.returnlist = []
        self.cmdlist = []
        self.rxlist = []

    # 保存每次点击按钮收发的数据为列表
    def savelist(self):
        self.namelist.append(self.data[self.index]['name'])
        self.stdlist.append(self.data[self.index]['std'])
        self.returnlist.append(self.labelReturnlist[self.index].text())
        self.rxlist.append(' '.join([hex(x)[2:].zfill(2) for x in self.rx]))
        if self.data[self.index]['widget'] == 'QLabel':
            self.vallist.append(self.widgetslist[self.index].text())
            if self.comboBox_port.currentText() == 'UART' or self.comboBox_port.currentText() == 'RS232':
                self.cmdlist.append(self.data[self.index]['cmd'])
            elif self.comboBox_port.currentText() == 'IIC':
                self.cmdlist.append(self.IICCmd)
            elif self.comboBox_port.currentText() == 'RS485':
                self.cmdlist.append(' '.join([hex(x)[2:].zfill(2) for x in self.MODBUSCmd]))
        print(self.namelist, self.stdlist, self.vallist, self.returnlist, self.cmdlist, self.rxlist)

    # 保存每次设置的数据到txt文档中
    def saveSetting(self):
        if '序列号' in self.namelist and self.ENFlag is False:
            index = self.namelist.index('序列号')
            SN = self.vallist[index]
            print('save SN:', SN)
            # 定义txt文件名
            file_name = SN + '_' + self.label_return.text() + '_' + '{:03d}.txt'.format(self.lentxt + 1)
        elif 'SerialNumber' in self.namelist and self.ENFlag is True:
            index = self.namelist.index('SerialNumber')
            SN = self.vallist[index]
            file_name = SN + '_' + self.label_return.text() + '_' + '{:03d}.txt'.format(self.lentxt + 1)
        elif 'SlaveID' in self.namelist:
            index = self.namelist.index('SlaveID')
            ID = self.vallist[index]
            print('save ID:', ID)
            file_name = 'RS485_ID_' + ID + '_' + self.label_return.text() + '_' + '{:03d}.txt'.format(self.lentxt + 1)
        else:
            file_name = self.label_return.text() + '_' + '{:03d}.txt'.format(self.lentxt + 1)
        # 定义待保存的文件路径（在新建的文件夹下）
        file_path = os.path.join(self.dir_path, file_name)
        # 打开文件写入数据
        with open(file_path, 'w') as f:
            for i in range(len(self.namelist)):
                if self.ENFlag is False:
                    f.write(self.namelist[i] + ': ' + '  期望值：' + self.stdlist[i] + '  检查值：' + self.vallist[i] + '    结果: ' + self.returnlist[i] + '\n' +
                            '发送cmd: ' + self.cmdlist[i].upper() + '\n' + '接收cmd: ' + self.rxlist[i].upper() + '\n' +
                            '------------------------------' + '\n')
                elif self.ENFlag is True:
                    f.write(self.namelist[i] + ': ' + '  StdVal: ' + self.stdlist[i] + '  CheckVal: ' + self.vallist[i] + '    Result: ' + self.returnlist[i] + '\n' +
                            'Send cmd: ' + self.cmdlist[i].upper() + '\n' + 'Receive cmd: ' + self.rxlist[i].upper() + '\n' +
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
        print('------------------------------')


if __name__ == '__main__':
    app = QApplication(sys.argv)  # 创建应用程序对象
    myWin = MyMainWindow()  # 实例化 MyMainWindow 类为 myWin，创建主窗口
    myWin.show()  # 在桌面显示控件 myWin
    myWin.getSerialPort()  # 获取串口列表
    # myWin.gettxtname()  # 获取创建的txt文档的名称

    sys.exit(app.exec_())  # 在主线程中退出
