import time
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import serial
import crcmod

BAUDRATE = [115200, 9600, 19200, 38400, 57600]  # 定义波特率列表
DIS_CMD = 'ADDR 03 00 00 00 01'
DIS_DIFF = 20
FPS_DIFF = 20
RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59

# 定义Modbus CRC16校验码生成函数
def ModbusCRC16(data):
    crc16 = crcmod.predefined.Crc('modbus')  # 创建一个CRC校验对象
    crc16.update(data)  # 添加指令
    crc = crc16.crcValue.to_bytes(2, byteorder='little')
    return crc


# 判断测距回显是否正确
def checkDataFrame_MODBUS(self):
    time.sleep(0.03)
    if self.ser.in_waiting:
        rx = self.ser.read(7)
        if rx[1] == 0x03 and rx[2] == 0x02:
            self.rx = rx
            print('rx:', rx.hex())
            return True
    return False


# 轮询波特率和从机地址
def pollBaudID_MODBUS(self):
    start_time = time.time()
    print('1 self.ser.baudrate:', self.ser.baudrate)
    for baud in BAUDRATE:
        self.ser.baudrate = baud
        print('2 self.ser.baudrate:', self.ser.baudrate)
        for id in range(1, 248):
            SlaveID = hex(id)[2:].zfill(2).upper()  # 将十进制转十六进制
            modCmd_str = DIS_CMD.replace('ADDR', SlaveID)
            modCmd = bytes.fromhex(modCmd_str)
            crc = ModbusCRC16(modCmd)
            modCmd += crc
            print('baud:', baud, 'id:', id, 'modCmd:', ' '.join(format(x, '02X') for x in modCmd))
            self.ser.reset_input_buffer()
            self.ser.write(modCmd)

            if checkDataFrame_MODBUS(self):
                self.SlaveID = '0x{:02}'.format(self.rx[0])  # str类型
                self.MODBUSCmd = modCmd
                self.ser.baudrate = baud
                print('3 self.ser.baudrate:', self.ser.baudrate)
                print('check finish, self.ser.baudrate and self.SlaveID:', self.ser.baudrate, self.SlaveID)
                print('self.MODBUSCmd:', self.MODBUSCmd.hex(), 'self.rx:', self.rx.hex())
                diff = time.time() - start_time
                print('diff:', diff)
                print('------------------------------')
                return self.ser.baudrate, self.SlaveID

    self.ser.baudrate = None
    self.rx = b''
    self.MODBUSCmd = b''
    diff = time.time() - start_time
    print('diff:', diff)
    print('------------------------------')
    return None


# 若 JSON 文件有指令发送,则根据从机地址改写并发送指令
def sendCmd_MODBUS(self):
    if self.data[self.index]['widget'] == 'QLabel':
        print('common cmd:', self.data[self.index]['cmd'])  # 获取对应的指令
        if self.data[self.index]['cmd'] != '':  # 判断指令是否为空
            # SlaveID 为空，轮询波特率和地址
            if self.SlaveID is None:
                pollBaudID_MODBUS(self)

            Cmd_str = self.data[self.index]['cmd'].replace('ADDR', self.SlaveID[2:])
            print('1 Cmd:', Cmd_str)
            Cmd = bytes.fromhex(Cmd_str)  # str 转为 byte
            crc = ModbusCRC16(Cmd)  # 计算校验和
            Cmd += crc  # 加上校验和后的指令
            print('2 Cmd:', Cmd)
            self.MODBUSCmd = Cmd
            print('self.MODBUSCmd:', self.MODBUSCmd.hex())
            self.ser.reset_input_buffer()
            self.ser.write(self.MODBUSCmd)
            print('------------------------------')


# 发送指令后接收指令回显并判断
def recvData_MODBUS(self):
    start_time = time.time()
    while True:
        if self.ser.in_waiting:
            rxhead = self.ser.read(1)
            print('rxhead:', rxhead)
            if rxhead == bytes.fromhex(self.SlaveID[2:]):  # 判断回显 SlaveID 是否和发送的相同
                rxdata = self.ser.readall()
                self.rx = rxhead + rxdata
                print('self.rx:', self.rx.hex())
                print('------------------------------')
                break
            else:
                print('rx head is not SlaveID')  # 帧头不是 SlaveID 接收剩下数据观察
                rxdata = self.ser.readall()
                self.rx = rxhead + rxdata
                print('self.rx:', self.rx.hex())
                #self.labelReturnlist[self.index].setText('NG')
                #self.labelReturnlist[self.index].setStyleSheet('color: red')
                #if self.data[self.index]['widget'] == 'QLabel':
                #    self.widgetslist[self.index].setText('')
                break

        elif (time.time() - start_time) > 1:
            pollBaudID_MODBUS(self)  # 尝试再次轮询地址,看是否是发送指令的读写地址位错误
            sendCmd_MODBUS(self)  # 轮询地址后再次尝试发送指令
            time.sleep(0.1)
            if self.ser. in_waiting:
                rxhead = self.ser.read(1)
                rxdata = self.ser.readall()
                if rxhead == bytes.fromhex(self.SlaveID[2:]):
                    self.rx = rxhead + rxdata
                    print('time out retry self.rx:', self.rx.hex())
                    break
                else:
                    self.rx = rxhead + rxdata
                    print('time out retry rxhead is not SlaveID')
                print('self.rx:', self.rx.hex())
                print('------------------------------')
            else:
                print('time out retry no rx')
                self.rx = b''
            break


# 根据配置标签名称对rx进行处理和回显正误判断
def recvAnalysis_MODBUS(self):
    if self.data[self.index]['name'] == '固件版本':
        if self.rx[1] == 0x03 and self.rx[2] == 0x04:
            version_rxhex = self.rx[4:7].hex()
            # 每两个字符由hex转为int，用'.'连接为str
            version_rxstr = '.'.join(str(int(version_rxhex[i:i + 2], 16)) for i in range(0, len(version_rxhex), 2))
            self.widgetslist[self.index].setText(version_rxstr)
            print('固件版本是：', version_rxstr)
            print('------------------------------')
        else:
            self.widgetslist[self.index].setText('')
    elif self.data[self.index]['name'] == '测距结果':
        if self.rx[1] == 0x03 and self.rx[2] == 0x02:
            self.dist = int.from_bytes(self.rx[3:5], byteorder='big')
            self.widgetslist[self.index].setText(str(self.dist) + ' (cm)')
            print('测距结果是：', self.dist)
            print('------------------------------')
        else:
            self.widgetslist[self.index].setText('')
    elif self.data[self.index]['name'] == '测试强度':
        if self.rx[1] == 0x03 and self.rx[2] == 0x02:
            strength = int.from_bytes(self.rx[3:5], byteorder='big')
            self.widgetslist[self.index].setText(str(strength))
            print('测试强度是：', strength)
            print('------------------------------')
    elif self.data[self.index]['name'] == '测试结果':
        if self.rx[1] == 0x03 and self.rx[2] == 0x04:
            dist = int.from_bytes(self.rx[3:5], byteorder='big')
            strength = int.from_bytes(self.rx[5:7], byteorder='big')
            text = 'D=' + str(dist) + '(cm)' + ';S=' + str(strength)
            self.widgetslist[self.index].setText(text)
        else:
            self.widgetslist[self.index].setText('')
    elif self.data[self.index]['widget'] == 'QLabel':
        self.widgetslist[self.index].setText(' '.join([hex(x)[2:].zfill(2) for x in self.rx]))


# 判断期望值和检查值是否相同(方法同UART)
def recvJudge_MODBUS(self):
    if self.data[self.index]['widget'] == 'QLabel' or self.data[self.index]['widget'] == 'QLineEdit':
        if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
        elif self.data[self.index]['name'] == '测距结果':
            if self.data[self.index]['std'] != '':
                stddis = int(self.data[self.index]['std'])
            else:
                stddis = 0
            if abs(stddis - self.dist) <= DIS_DIFF:
                self.labelReturnlist[self.index].setText('OK')
                self.labelReturnlist[self.index].setStyleSheet('color: green')
                print('Distance is Correct')
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


# 通过轮询检查 Slave ID
def checkSlaveID_MODBUS(self):
    pollBaudID_MODBUS(self)  # 轮询波特率和地址
    if self.SlaveID is not None and self.rx != b'':
        self.widgetslist[self.index].setText(self.SlaveID)
    else:
        self.widgetslist[self.index].setText('')
    recvJudge_MODBUS(self)


# 通过轮询检查波特率
def checkBaud_MODBUS(self):
    pollBaudID_MODBUS(self)  # 轮询波特率和地址
    if self.ser.baudrate is not None and self.rx != b'':
        self.widgetslist[self.index].setText(str(self.ser.baudrate))
    else:
        self.widgetslist[self.index].setText('')
    recvJudge_MODBUS(self)


# 从串口接收3次帧头，检查当前波特率接收是否是数据帧
def checkDataFrame_UART(self):
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
def pollBaudrate_MODBUS(self):
    try:
        for baudrate in BAUDRATE:
            print('baudrate is:', baudrate)
            self.ser.baudrate = baudrate
            if checkDataFrame_UART(self):  # 如果帧头检查正确，返回当前波特率值
                print('------------------------------')
                return baudrate
        # self.ser.close()

    except Exception as e:
        print(type(e))
        print(e)
        if type(e) == serial.serialutil.SerialException:  # 如果转接板不支持当前波特率
            BAUDRATE.remove(baudrate)  # 从波特率列表中移除当前波特率
            print(BAUDRATE)
            for baudrate in BAUDRATE:
                self.ser.baudrate = baudrate
                if checkDataFrame_UART(self):  # 如果帧头检查正确，返回当前波特率值
                    print('------------------------------')
                    return baudrate
            # self.ser.close()


# 检查输出帧率
def checkFramerate_MODBUS(self):
    self.ser.reset_input_buffer()
    pollBaudrate_MODBUS(self)  # 通过轮询获得波特率
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
    self.widgetslist[self.index].setText(str(round(fps)) + ' (Hz)')
    # 判断帧率是否正确
    if self.data[self.index]['std'] != '':
        stdfps = int(self.data[self.index]['std'])
    else:
        stdfps = 0
    # 判断结果是 OK 还是 NG
    if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
        self.labelReturnlist[self.index].setText('OK')
        self.labelReturnlist[self.index].setStyleSheet('color: green')
        print('Framerate is Correct')
    elif self.data[self.index]['std'] != '' and abs(fps - stdfps) <= FPS_DIFF:
        self.labelReturnlist[self.index].setText('OK')
        self.labelReturnlist[self.index].setStyleSheet('color: green')
        print('Framerate is Correct')
    else:
        self.labelReturnlist[self.index].setText('NG')
        self.labelReturnlist[self.index].setStyleSheet('color: red')
        print('Framerate is Error')

    self.rx = b''
    self.MODBUSCmd = b''
    print('------------------------------')
