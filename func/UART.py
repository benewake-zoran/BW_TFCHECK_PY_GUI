import time
import serial
from PyQt5.QtWidgets import QMessageBox

CMD_FRAME_HEADER = b'Z'  # 指令帧头定义 0x5A
RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59
BAUDRATE = [115200, 9600, 19200, 38400, 57600, 460800, 921600, 256000]  # 定义波特率列表


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
def pollBaudrate_UART(self):
    try:
        for baudrate in BAUDRATE:
            print('baudrate is:', baudrate)
            self.ser.baudrate = baudrate
            if checkDataFrame(self):  # 如果帧头检查正确，返回当前波特率值
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
                if checkDataFrame(self):  # 如果帧头检查正确，返回当前波特率值
                    print('------------------------------')
                    return baudrate
            self.ser.close()
            QMessageBox.warning(self, '提示', '串口无法打开，请检查！\n1.可能串口松了\n2.可能被其他程序占用\n3.串口选择错误\n4.转接板不支持当前波特率\n5.设备输出关闭')


# 发送 JSON 文件中的指令
def sendCmd_UART(self):
    if self.data[self.index]['widget'] == 'QLabel':
        print('send cmd:', self.data[self.index]['cmd'])  # 获取对应的指令
        if self.data[self.index]['cmd'] != '':  # 判断指令是否为空
            self.labelCmdb = bytes.fromhex(self.data[self.index]['cmd'])
            print('cmdb', self.labelCmdb)
            self.ser.reset_input_buffer()
            self.ser.write(self.labelCmdb)  # 发送指令
            print('------------------------------')


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


# 判断期望值和检查值是否相同
def recvJudge_UART(self):
    if self.data[self.index]['widget'] == 'QLabel' or self.data[self.index]['widget'] == 'QLineEdit':
        if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
        elif self.data[self.index]['std'] == self.widgetslist[self.index].text():
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
        else:
            self.labelReturnlist[self.index].setText('NG')
            self.labelReturnlist[self.index].setStyleSheet('color: red')
    elif self.data[self.index]['widget'] == 'QComboBox':
        if self.data[self.index]['std'] == '' and self.widgetslist[self.index].currentText() != '':
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
        elif self.data[self.index]['std'] == self.widgetslist[self.index].currentText():
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
        else:
            self.labelReturnlist[self.index].setText('NG')
            self.labelReturnlist[self.index].setStyleSheet('color: red')


# 检查波特率
def checkBaud_UART(self):
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


# 检查输出帧率
def checkFrame_UART(self):
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
    if self.data[self.index]['std'] != '':
        stdfps = int(self.data[self.index]['std'])
    else:
        stdfps = 0
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


# 检查测距
def checkDis_UART(self):
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
                self.widgetslist[self.index].setText(str(dist) + ' (cm)')
                print('------------------------------')
                if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
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


# 检查其他标签
def checkOther_UART(self):
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
                tempC = int(temp / 8 - 256)
                text = 'D=' + str(dist) + ';S=' + str(strength) + ';T=' + str(tempC)
                if self.data[self.index]['widget'] == 'QLabel':
                    self.widgetslist[self.index].setText(text)
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
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
