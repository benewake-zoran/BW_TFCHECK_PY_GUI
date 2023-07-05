import time

RECV_FRAME_HEADER = b'YY'  # 接收数据帧头定义 0x59 0x59


def checkBaud_UART(self):
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


def checkFrame_UART(self):
    if self.data[self.index]['name'] == '输出帧率':
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


def checkDis_UART(self):
    if self.data[self.index]['name'] == '测距结果':
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