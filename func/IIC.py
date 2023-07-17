import time

CMD_FRAME_HEADER = b'Z'  # 指令帧头定义 0x5A
RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59
DIS_DIFF = 10  # 允许测距误差范围
DIS_Cmd = '53 W 05 5A 05 00 01 60 50 53 R 09 50'  # IIC测距指令


# 通过轮询找到从机地址
def pollAddress_IIC(self):
    start_time = time.time()
    self.ser.reset_input_buffer()  # 清空输入缓存区
    for i in range(1, 128):
        Whex_i = hex((i << 1) & 0xFE)[2:].zfill(2).upper()  # 左移1位后最后位置0
        Rhex_i = hex((i << 1) | 0x01)[2:].zfill(2).upper()  # 左移1位后最后位置1
        NewCmd = DIS_Cmd.replace('W', Whex_i).replace('R', Rhex_i)
        print('i', i, '0xi:', hex(i)[2:].zfill(2), 'Whex_i:', Whex_i, 'Rhex_i:', Rhex_i, 'NewCmd:', NewCmd)
        self.ser.write(bytes.fromhex(NewCmd))
        time.sleep(0.05)  # 等待 50 ms
        if self.ser.in_waiting:
            rxIIC = self.ser.read(9)
            print('poll address rxIIC:', rxIIC.hex())
            if rxIIC[:2] == RECV_FRAME_HEADER:
                #self.address = hex(i)
                self.address = '0x{:02}'.format(hex(i)[2:].zfill(2).upper())
                self.rx = rxIIC
                self.IICCmd = NewCmd
                print('IIC address rx:', self.rx.hex())
                print('IIC address is:', '0x{:02}'.format(hex(i)[2:].zfill(2)).upper())
                # self.ser.close()
                break
        else:
            self.rx = b''
            self.IICCmd = ''
    diff = time.time() - start_time
    print('diff:', diff)
    print('------------------------------')


# 若 JSON 文件有指令发送,则根据从机地址改写并发送指令
def sendCmd_IIC(self):
    if self.data[self.index]['widget'] == 'QLabel':
        print('common cmd:', self.data[self.index]['cmd'])  # 获取对应的指令
        if self.data[self.index]['cmd'] != '':  # 判断指令是否为空
            # 从机地址为空,进行轮询地址
            if self.address is None:
                print('when send cmd self.address is None')
                pollAddress_IIC(self)

            if self.address is not None:
                Cmd = '53 W LEN1 DATA 50 53 R LEN2 50'  # IIC通信时序
                DataCmd = self.data[self.index]['cmd']  # 将 JSON 中的指令字符串取出
                LEN1 = len(DataCmd.split())  # 计算写入指令字节数
                WCmd = hex((int(self.address, 16) << 1) & 0xFE)[2:].zfill(2).upper()  # 写操作
                RCmd = hex((int(self.address, 16) << 1) | 0x01)[2:].zfill(2).upper()  # 读操作
                NewCmd = Cmd.replace('W', WCmd).replace('LEN1', str(LEN1).zfill(2)).replace('DATA', DataCmd).replace('R', RCmd)
                if self.data[self.index]['name'] == '序列号' or self.data[self.index]['name'] == 'SerialNumber':
                    NewCmd = NewCmd.replace('LEN2', '12')
                elif self.data[self.index]['name'] == '固件版本' or self.data[self.index]['name'] == 'FirmwareVer':
                    NewCmd = NewCmd.replace('LEN2', '07')
                else:
                    NewCmd = NewCmd.replace('LEN2', '05')  # 读取9个字节观察
                self.newCmd = bytes.fromhex(NewCmd)
                self.IICCmd = NewCmd  # IIC 指令 str类型
                print('IIC newCmd:', self.IICCmd)
                self.ser.reset_input_buffer()
                self.ser.write(self.newCmd)  # 发送指令
                print('------------------------------')


# 发送指令后接收指令回显并判断 5A 帧头
def recvData_IIC(self):
    start_time = time.time()
    while True:
        if self.ser.in_waiting:
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
                break
            elif rxhead != CMD_FRAME_HEADER:  # 数据接收无帧头 5A 跳出循环
                print('rx head is not 5A')
                self.rx = rxhead + self.ser.readall()  # 读取串口所有数据来观察
                break
        elif (time.time() - start_time) > 1:  # 超过 1s 都无数据接收跳出循环
            print('time out 1s, try to poll address')
            pollAddress_IIC(self)  # 尝试再次轮询地址,看是否是发送指令的读写地址位错误
            sendCmd_IIC(self)  # 轮询地址后再次尝试发送指令
            time.sleep(0.5)
            if self.ser.in_waiting:
                rxhead = self.ser.read(1)
                print('rxhead:', rxhead.hex())
                # rxdata = self.ser.readall()
                if rxhead == CMD_FRAME_HEADER:  # 判断接收数据帧头是否为 5A
                    rxlen = self.ser.read(1)  # 若是读取一个长度字节
                    rxlenint = rxlen[0]  # 将bytes转为int
                    rxdata = self.ser.read(rxlenint - 2)  # 读取剩下的数据字节
                    self.rx = rxhead + rxlen + rxdata
                    print('poll again rx == head and rx:', self.rx.hex())
                    break
                elif rxhead != CMD_FRAME_HEADER:  # 数据接收无帧头 5A
                    self.rx = rxhead + self.ser.readall()  # 读取串口所有数据来观察
                    print('poll again rx != head and rx:', self.rx.hex())
                    break
            else:
                self.rx = b''
                print("poll again no rx")
                break
    print('------------------------------')


# 根据配置标签名称对rx进行处理和回显正误判断
def recvAnalysis_IIC(self):
    if self.data[self.index]['name'] == '序列号' or self.data[self.index]['name'] == 'SerialNumber':
        if self.rx != b'' and self.rx[2] == 0x12:
            SN_rxhex = self.rx[3:17]
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


# 判断期望值和检查值是否相同(方法同UART)
def recvJudge_IIC(self):
    if self.data[self.index]['widget'] == 'QLabel' or self.data[self.index]['widget'] == 'QLineEdit':
        if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
        elif self.data[self.index]['std'] == self.widgetslist[self.index].text() and self.widgetslist[self.index].text() != '':
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


# 通过轮询检查IIC从机地址
def checkAddress_IIC(self):
    pollAddress_IIC(self)  # 轮询地址
    if self.address is not None and self.rx != b'':
        self.widgetslist[self.index].setText(self.address)
    else:
        self.widgetslist[self.index].setText('')
    recvJudge_IIC(self)  # 判断期望值和检查值是否相同


# 检查测距
def checkDistance_IIC(self):
    if self.data[self.index]['std'] != '':
        stddis = int(self.data[self.index]['std'])  # 记录期望值
    else:
        stddis = 0

    if self.address is None:
        pollAddress_IIC(self)
        if self.rx != b'':
            dist = int.from_bytes(self.rx[2:4], byteorder='little')
            self.widgetslist[self.index].setText(str(dist) + ' (cm)')
    else:
        WCmd = hex((int(self.address, 16) << 1) & 0xFE)[2:].zfill(2).upper()  # 写操作
        RCmd = hex((int(self.address, 16) << 1) | 0x01)[2:].zfill(2).upper()  # 读操作
        NewCmd = DIS_Cmd.replace('W', WCmd).replace('R', RCmd)
        self.ser.write(bytes.fromhex(NewCmd))
        time.sleep(0.05)  # 等待 50 ms
        start_time = time.time()
        while True:
            if self.ser.in_waiting:
                rxIIC = self.ser.read(9)
                if rxIIC[:2] == RECV_FRAME_HEADER:
                    self.rx = rxIIC
                    self.IICCmd = NewCmd
                    print('IIC address rx:', self.rx.hex())
                    dist = int.from_bytes(self.rx[2:4], byteorder='little')
                    self.widgetslist[self.index].setText(str(dist) + ' (cm)')
                    break
            else:
                if (time.time() - start_time) > 1:
                    pollAddress_IIC(self)  # 尝试再次轮询地址,看是否是发送指令的读写地址位错误
                    if self.rx != b'':
                        dist = int.from_bytes(self.rx[2:4], byteorder='little')
                        self.widgetslist[self.index].setText(str(dist) + ' (cm)')
                    break
    print('------------------------------')
    if self.data[self.index]['std'] == '' and self.widgetslist[self.index].text() != '':
        self.labelReturnlist[self.index].setText('OK')
        self.labelReturnlist[self.index].setStyleSheet('color: green')
        print('Distance is Correct')
    elif self.rx != b'':
        if abs(stddis - dist) <= DIS_DIFF:
            self.labelReturnlist[self.index].setText('OK')
            self.labelReturnlist[self.index].setStyleSheet('color: green')
            print('Distance is Correct')
        else:
            self.labelReturnlist[self.index].setText('NG')
            self.labelReturnlist[self.index].setStyleSheet('color: red')
            print('Distance is Error')
    else:
        self.labelReturnlist[self.index].setText('NG')
        self.labelReturnlist[self.index].setStyleSheet('color: red')
        print('Distance rx is Empty')


# 检查其他标签
def checkOther_IIC(self):
    if self.address is None:
        pollAddress_IIC(self)
        if self.rx != b'':
            dist = int.from_bytes(self.rx[2:4], byteorder='little')
            strength = int.from_bytes(self.rx[4:6], byteorder='little')
            temp = int.from_bytes(self.rx[6:8], byteorder='little')
            tempC = int(temp / 8 - 256)
            text = 'D=' + str(dist) + ';S=' + str(strength) + ';T=' + str(tempC)
            if self.data[self.index]['widget'] == 'QLabel':
                self.widgetslist[self.index].setText(text)
    else:
        WCmd = hex((int(self.address, 16) << 1) & 0xFE)[2:].zfill(2).upper()  # 写操作
        RCmd = hex((int(self.address, 16) << 1) | 0x01)[2:].zfill(2).upper()  # 读操作
        NewCmd = DIS_Cmd.replace('W', WCmd).replace('R', RCmd)
        self.ser.write(bytes.fromhex(NewCmd))
        time.sleep(0.05)  # 等待 50 ms
        start_time = time.time()
        while True:
            if self.ser.in_waiting:
                rxIIC = self.ser.read(9)
                if rxIIC[:2] == RECV_FRAME_HEADER:
                    self.rx = rxIIC
                    self.IICCmd = NewCmd
                    print('IIC address rx:', self.rx.hex())
                    dist = int.from_bytes(self.rx[2:4], byteorder='little')
                    strength = int.from_bytes(self.rx[4:6], byteorder='little')
                    temp = int.from_bytes(self.rx[6:8], byteorder='little')
                    tempC = int(temp / 8 - 256)
                    text = 'D=' + str(dist) + ';S=' + str(strength) + ';T=' + str(tempC)
                    if self.data[self.index]['widget'] == 'QLabel':
                        self.widgetslist[self.index].setText(text)
                    break
            else:
                if (time.time() - start_time) > 1:
                    pollAddress_IIC(self)  # 尝试再次轮询地址,看是否是发送指令的读写地址位错误
                    if self.rx != b'':
                        dist = int.from_bytes(self.rx[2:4], byteorder='little')
                        strength = int.from_bytes(self.rx[4:6], byteorder='little')
                        temp = int.from_bytes(self.rx[6:8], byteorder='little')
                        tempC = int(temp / 8 - 256)
                        text = 'D=' + str(dist) + ';S=' + str(strength) + ';T=' + str(tempC)
                        if self.data[self.index]['widget'] == 'QLabel':
                            self.widgetslist[self.index].setText(text)
                    break
    print('------------------------------')
    recvJudge_IIC(self)


# 防止IIC转接板卡死
def refresh_IIC(self):
    if self.ser.rts is False:  # IIC转接板卡死复位
        self.ser.setRTS(True)
        self.ser.setRTS(False)
        rx = self.ser.read(2)
        if rx != b'':
            print(rx.hex())
