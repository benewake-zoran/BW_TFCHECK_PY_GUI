import time

CMD_FRAME_HEADER = b'Z'  # 指令帧头定义 0x5A
RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59
DIS_DIFF = 20  # 允许测距误差范围
FPS_DIFF = 20  # 允许帧率误差范围
timeout = 1
SingleRangeCmd = '5A 04 04 62'  # 单次测距指令


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
        # if (time.time() %0.5) == 0 : 
        #     # sendCmd_UART(self)
        #     print('send cmd:', self.data[self.index]['cmd'])  # 获取对应的指令
        #     if self.data[self.index]['cmd'] != '':  # 判断指令是否为空
        #         self.labelCmdb = bytes.fromhex(self.data[self.index]['cmd'])
        #         print('cmdb', self.labelCmdb)
        #         self.ser.reset_input_buffer()
        #         self.ser.write(self.labelCmdb)  # 发送指令
        #         print('------------------------------')

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
            elif (time.time() - start_time) > timeout:  # 数据接收超过 1s 都无帧头跳出循环
                print('Timeout 1s, rx read 18 bytes')
                self.rx = self.ser.read(18)  # 超时读取两个帧来观察
                break
        elif (time.time() - start_time) > timeout:  # 超过 1s 都无数据接收跳出循环  没有数据接收超过一秒 
            print('Timeout 1s, empty rx')
            self.rx = b''
            break


# 根据配置标签名称对rx进行处理和回显正误判断
def recvAnalysis_UART(self):
    if self.data[self.index]['name'] == '序列号' or self.data[self.index]['name'] == 'SerialNumber':
        if self.rx != b'' and self.rx[2] == 0x12:
            SN_rxhex = self.rx[3:17]
            SN_rxstr = ''.join([chr(x) for x in SN_rxhex])
            self.widgetslist[self.index].setText(SN_rxstr)
            print('序列号是：', SN_rxstr)
            print('------------------------------')
        elif self.rx != b'' and self.rx[2] == 0x56:     #TF03比较特殊
            SN_rxhex = self.rx[4:18]
            SN_rxstr = ''.join([chr(x) for x in SN_rxhex])
            self.widgetslist[self.index].setText(SN_rxstr)
            print('序列号是：', SN_rxstr)
            print('------------------------------')

    elif self.data[self.index]['name'] == '固件版本' or self.data[self.index]['name'] == 'FirmwareVer':
        if self.rx != b'' and self.rx[2] == 0x01:
            version_rxhex = self.rx[3:6][::-1].hex()  # 取出字节数组并反转后转为十六进制
            # 每两个字符由hex转为int，用'.'连接为str
            version_rxstr = '.'.join(str(int(version_rxhex[i:i + 2], 16)) for i in range(0, len(version_rxhex), 2))
            self.widgetslist[self.index].setText(version_rxstr)
            print('固件版本是：', version_rxstr)
            print('------------------------------')
    elif self.data[self.index]['widget'] == 'QLabel':
        self.widgetslist[self.index].setText(' '.join([hex(x)[2:].zfill(2) for x in self.rx]).upper())


# 判断期望值和检查值是否相同
# @zoran 2023.08.14 去除重复的控件显示，在 MyMainWindow 类中增加辅助方法 _set_judgment_result
def recvJudge_UART(self):
    widget = self.data[self.index]['widget']
    if widget in ('QLabel', 'QLineEdit'):
        actual = self.widgetslist[self.index].text()
    elif widget == 'QComboBox':
        actual = self.widgetslist[self.index].currentText()
    else:
        return  # 可根据需要添加其他类型的处理逻辑
    expected = self.data[self.index]['std']
    self._set_judgment_result(expected, actual)

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
    if abs(fps - stdfps) <= FPS_DIFF:
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
    start_time = time.time()  # 记录开始时间
    self.ser.reset_input_buffer()
    time.sleep(0.1)
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
                elif abs(stddis - dist) <= DIS_DIFF:
                    self.labelReturnlist[self.index].setText('OK')
                    self.labelReturnlist[self.index].setStyleSheet('color: green')
                    print('Distance is Correct')
                else:
                    self.labelReturnlist[self.index].setText('NG')
                    self.labelReturnlist[self.index].setStyleSheet('color: red')
                    print('Distance is Error')
                print('std disVal:', stddis, 'actual disVal:', dist)
                break
            elif (time.time() - start_time) > timeout:  # 数据接收超过 0.5s 都无帧头跳出循环
                print('Timeout 1s, rx read 18 bytes')
                self.rx = self.ser.read(18)  # 超时读取两个帧来观察
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')
                if self.data[self.index]['widget'] == 'QLabel':
                    self.widgetslist[self.index].setText('')
                break
        else:
            self.ser.write(bytes.fromhex(SingleRangeCmd))
            print('send range cmd')
            time.sleep(0.1)
            if self.ser.in_waiting:
                rxhead = self.ser.read(2)
                if rxhead == RECV_FRAME_HEADER:
                    rxdata = self.ser.read(7)
                    self.rx = rxhead + rxdata
                    print('rx:', ' '.join([hex(x)[2:].zfill(2) for x in self.rx]))
                    dist = int.from_bytes(self.rx[2:4], byteorder='little')
                    self.widgetslist[self.index].setText(str(dist) + ' (cm)')
                    if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
                        self.labelReturnlist[self.index].setText('OK')
                        self.labelReturnlist[self.index].setStyleSheet('color: green')
                        print('send range cmd Distance is Correct')
                    elif abs(stddis - dist) <= DIS_DIFF:
                        self.labelReturnlist[self.index].setText('OK')
                        self.labelReturnlist[self.index].setStyleSheet('color: green')
                        print('send range cmd Distance is Correct')
                    else:
                        self.labelReturnlist[self.index].setText('NG')
                        self.labelReturnlist[self.index].setStyleSheet('color: red')
                        print('send range cmd Distance is Error')
                    print('send range cmd std disVal:', stddis, 'actual disVal:', dist)
                    print('------------------------------')
                break
            elif (time.time() - start_time) > timeout:  # 超过 0.5s 都无数据接收跳出循环
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
                if (self.data[self.index]['widget'] == 'QLabel'and self.data[self.index]['name'] != 'SlaveID' 
                    and self.data[self.index]['name'] != 'I2C从机地址'): #防止和其他文本判断逻辑冲突，没得到和文本标签对应的结果还OK
                    self.widgetslist[self.index].setText(text)
                    self.labelReturnlist[self.index].setText('OK')
                    self.labelReturnlist[self.index].setStyleSheet('color: green')      
                else:
                    self.labelReturnlist[self.index].setText('NG')
                    self.labelReturnlist[self.index].setStyleSheet('color: red')
                print('------------------------------')
                break
            elif (time.time() - start_time) > timeout:  # 数据接收超过 1s 都无帧头跳出循环
                print('Timeout 1s, rx read 18 bytes')
                self.rx = self.ser.read(18)  # 超时读取两个帧来观察
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')
                if self.data[self.index]['widget'] == 'QLabel':
                    self.widgetslist[self.index].setText('')
                break
        else:
            if (time.time() - start_time) > timeout:  # 超过 1s 都无数据接收跳出循环
                print('Timeout 1s, empty rx')
                self.rx = b''
                self.labelReturnlist[self.index].setText('NG')
                self.labelReturnlist[self.index].setStyleSheet('color: red')
                if self.data[self.index]['widget'] == 'QLabel':
                    self.widgetslist[self.index].setText('')
                break
