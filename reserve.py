import json
import logging
import datetime
import time
from random import random
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import requests

MAP = {
    '花津二楼报刊阅览室': ('nbk', 430),
    '花津二楼电子阅览室': ('ndz', 188),
    '花津三楼社科一': ('nsk1', 342),
    '花津三楼自然阅览室': ('nzr1', 343),
    '花津三楼公共东': ('ngg3e', 96),
    '花津三楼公共西': ('ngg3w', 96),
    '花津四楼社科三': ('nsk3', 318),
    '花津四楼社科二': ('nsk2', 302),
    '花津四楼公共东': ('ngg4e', 88),
    '花津四楼公共西': ('ngg4w', 100),
    '花津五楼公共': ('ngg5', 37),
    '赭山文科室': ('zsk1', 112),
    '赭山理科室': ('zzr1', 112),
    '赭山电子阅览室': ('zdz', 66)
}


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        if record.levelno == logging.INFO:
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
        elif record.levelno == logging.WARNING:
            messagebox.showwarning('警告', msg)


class Reserve:
    def __init__(self, **kwargs):
        self.info = kwargs
        self.session = requests.Session()

        # 创建窗口
        self.root = tk.Tk()
        self.root.title("安师大图书馆预约")
        self.root.geometry("300x300")

        # 创建单选框变量
        self.room = tk.StringVar()

        # 创建折叠单选框
        combobox = ttk.Combobox(self.root, textvariable=self.room, values=list(MAP.keys()))
        combobox.pack()

        frame = tk.Frame(self.root)

        # 创建输入框
        self.seat_entry = tk.Entry(frame)

        # 显示文字说明和输入框
        tk.Label(frame, text="座位号").pack(side=tk.LEFT)
        self.seat_entry.pack(side=tk.LEFT)
        frame.pack()

        frame = tk.Frame(self.root)

        # 创建输入框
        self.account_entry = tk.Entry(frame)

        # 显示文字说明和输入框
        tk.Label(frame, text="学号").pack(side=tk.LEFT)
        self.account_entry.pack(side=tk.LEFT)
        frame.pack()

        frame = tk.Frame(self.root)

        # 创建输入框
        self.password_entry = tk.Entry(frame)

        # 显示文字说明和输入框
        tk.Label(frame, text="密码").pack(side=tk.LEFT)
        self.password_entry.pack(side=tk.LEFT)
        frame.pack()

        frame = tk.Frame(self.root)

        # 创建一个 IntVar 变量，用于存储单选框的值
        self.day = tk.IntVar()

        # 创建两个单选框，分别对应值为 1 和 2
        radio_button1 = tk.Radiobutton(frame, text='今日', variable=self.day, value=1)
        radio_button1.pack(side=tk.LEFT)

        radio_button2 = tk.Radiobutton(frame, text='明日', variable=self.day, value=2)
        radio_button2.pack(side=tk.RIGHT)

        self.day.set(2)
        frame.pack()

        frame = tk.Frame(self.root)

        # 创建小时选择器
        self.start_hour = tk.StringVar()
        self.start_hour.set("00")
        hour_spinbox = tk.Spinbox(frame, from_=6, to=23, width=2, textvariable=self.start_hour)

        # 创建分钟选择器
        self.start_minute = tk.StringVar()
        self.start_minute.set("00")
        minute_spinbox = tk.Spinbox(frame, from_=0, to=59, width=2, textvariable=self.start_minute)

        # 显示选择器
        tk.Label(frame, text="起始时间：").pack(side=tk.LEFT)
        hour_spinbox.pack(side=tk.LEFT)
        tk.Label(frame, text=":").pack(side=tk.LEFT)
        minute_spinbox.pack(side=tk.LEFT)
        frame.pack()

        frame = tk.Frame(self.root)

        # 创建小时选择器
        self.end_hour = tk.StringVar()
        self.end_hour.set("00")
        hour_spinbox = tk.Spinbox(frame, from_=6, to=23, width=2, textvariable=self.end_hour)

        # 创建分钟选择器
        self.end_minute = tk.StringVar()
        self.end_minute.set("00")
        minute_spinbox = tk.Spinbox(frame, from_=0, to=59, width=2, textvariable=self.end_minute)

        # 显示选择器
        tk.Label(frame, text="结束时间：").pack(side=tk.LEFT)
        hour_spinbox.pack(side=tk.LEFT)
        tk.Label(frame, text=":").pack(side=tk.LEFT)
        minute_spinbox.pack(side=tk.LEFT)
        frame.pack()

        self.button = tk.Button(self.root, text='预约', command=self.reserve)
        self.button.pack()

        self.text_widget = tk.Text(self.root)
        self.text_widget.pack()

        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.INFO)

        self.text_handler = TextHandler(self.text_widget)
        self.text_handler.setLevel(logging.INFO)

        self.file_handler = logging.FileHandler('my_log.log')
        self.file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m-%d %H:%M:%S')

        self.text_handler.setFormatter(formatter)
        self.file_handler.setFormatter(formatter)

        self.logger.addHandler(self.text_handler)
        self.logger.addHandler(self.file_handler)

    def run(self):
        self.root.mainloop()

    def reserve(self):
        try:
            self.logger.info('开始预约')

            self.login()

            header = {
                'Host': 'libzwxt.ahnu.edu.cn',
                'Origin': 'http://libzwxt.ahnu.edu.cn',
                'Referer': 'http://libzwxt.ahnu.edu.cn/SeatWx/Seat.aspx?fid=3&sid=1438',
                'User-Agent': "Mozilla/5.0 (Linux; Android 12; M2006J10C Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/107.0.5304.141 Mobile Safari/537.36 XWEB/5061 MMWEBSDK/20230303 MMWEBID/534 MicroMessenger/8.0.34.2340(0x2800225D) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64;",
                'X-AjaxPro-Method': 'AddOrder',
            }
            url = 'http://libzwxt.ahnu.edu.cn/SeatWx/ajaxpro/SeatManage.Seat,SeatManage.ashx'

            if self.day.get() == 2:
                atData = str(datetime.date.today() + datetime.timedelta(days=1))
                print(atData)
            elif self.day.get() == 1:
                atData = str(datetime.date.today())
                print(atData)
            print(self.room.get())
            sid = MAP.get(self.room.get())[0] + self.seat_entry.get()
            print(sid)

            st = f'{self.start_hour.get()}:{self.start_minute.get()}'
            print(st)
            et = f'{self.end_hour.get()}:{self.end_minute.get()}'
            print(et)

            data = {
                'atDate': atData,
                'sid': sid,
                'st': st,
                'et': et,
            }

            # 尝试进行预约
            while True:
                reserve = self.session.post(url, data=json.dumps(data), headers=header)

                if '预约成功' in reserve.text:
                    self.logger.debug(reserve.text)
                    self.logger.info('预约成功，座位：{0}'.format(self.info['sid']))
                    break
                elif '提前' in reserve.text:
                    self.logger.debug(reserve.text)
                    self.logger.info('服务器时间不一致')
                    continue
                elif '冲突' or '重复' in reserve.text:
                    sid = MAP.get(self.room.get())[0] + str(int(self.seat_entry.get()) + 1)
                    data['sid'] = sid
                    time.sleep(random()+5)
                    self.logger.info(f'新的座位号：{sid}')

        except ValueError as ve:
            self.logger.warning(ve)
        except Exception as e:
            self.logger.warning('未知错误：' + str(e))
        except:
            self.logger.warning('未知错误：')

    def login(self) -> None:
        """
        create session and login libzwxt
        :return: void
        """
        self.logger.info('开始登陆，用户名：{0}, 密码：{1}。'.format(self.account_entry.get(), self.password_entry.get()))

        url = 'http://libzwxt.ahnu.edu.cn/SeatWx/login.aspx'
        data = {
            '__VIEWSTATE': '/wEPDwULLTE0MTcxNzMyMjZkZAl5GTLNAO7jkaD1B+BbDzJTZe4WiME3RzNDU4obNxXE',
            '__VIEWSTATEGENERATOR': 'F2D227C8',
            '__EVENTVALIDATION': '/wEWBQK1odvtBQLyj'
                                 '/OQAgKXtYSMCgKM54rGBgKj48j5D4sJr7QMZnQ4zS9tzQuQ1arifvSWo1qu0EsBRnWwz6pw',
            'tbUserName': self.account_entry.get(),
            'tbPassWord': self.password_entry.get(),
            'Button1': '登 录  ',
            'hfurl': ''
        }

        response = self.session.post(url=url, data=data)
        # print(response.content.decode())

        if '请输入用户名' not in response.content.decode():
            self.logger.info('登录成功！')
        else:
            raise ValueError('登录失败，请检查用户名和密码是否正确。')

    def convert(self, seat_code) -> int:
        """
        convert seat_code to sid
        :param seat_code:
        :return: sid
        """

        # ---------------花津二楼---------------
        # 花津二楼报刊阅览室 num 430 rid 1 fid 1
        if seat_code[:3] == 'nbk':
            sid = int(seat_code[3:])
        # 花津二楼电子阅览室 num 188 rid 18 fid 1
        elif seat_code[:3] == 'ndz':
            sid = int(seat_code[3:]) + 2875

        # ---------------花津三楼---------------
        # 花津三楼社科一 num 342 rid 5 fid 3
        elif seat_code[:4] == 'nsk1':
            sid = int(seat_code[4:]) + 1095
        # 花津三楼自然阅览室 num 343 rid 6 fid 3
        elif seat_code[:4] == 'nzr1':
            sid = int(seat_code[4:]) + 1437
        # 花津三楼公共东 num 96 rid 13 fid 3
        elif seat_code[:5] == 'ngg3e':
            number = int(seat_code[5:])
            if number < 89:
                sid = number + 2433
            else:
                sid = number - 89 + 2682
        # 花津三楼公共西 num 96 rid 14 fid 3
        elif seat_code[:5] == 'ngg3w':
            number = int(seat_code[5:])
            sid = number + 2521

        # ---------------花津四楼---------------
        # 花津四楼社科三 num 318 rid 3 fid 5
        elif seat_code[:4] == 'nsk3':
            sid = int(seat_code[4:]) + 523
        # 花津四楼社科二 num 302 rid 4 fid 5
        elif seat_code[:4] == 'nsk2':
            sid = int(seat_code[4:]) + 823
        # 花津四楼公共东 num 88 rid 15 fid 5
        elif seat_code[:5] == 'ngg4e':
            number = int(seat_code[5:])
            if number < 33:
                sid = number + 2617
            else:
                sid = number - 33 + 2754
        # 花津四楼公共西 num 100 rid 16 fid 5
        elif seat_code[:5] == 'ngg4w':
            number = int(seat_code[5:])
            if number < 33:
                sid = number + 2649
            elif 33 <= number <= 96:
                sid = number - 33 + 2690
            else:
                sid = number - 97 + 3143

        # ---------------花津五楼---------------
        # 花津五楼公共 num 37 rid 19 fid 7
        elif seat_code[:4] == 'ngg5':
            sid = int(seat_code[4:]) + 3063

        # ---------------赭山校区---------------
        # 赭山文科室 num 66 rid 7 fid 12
        elif seat_code[:4] == 'zsk1':
            sid = int(seat_code[4:]) + 1780
        # 赭山理科室 num 112 rid 9 fid 12
        elif seat_code[:4] == 'zzr1':
            sid = int(seat_code[4:]) + 2092
        # 赭山电子阅览室 num 112 rid 17 fid 12
        elif seat_code[:3] == 'zdz':
            sid = int(seat_code[3:]) + 2809
        # ----------------错误----------------
        else:
            raise ValueError(f'座位编号 {seat_code} 错误')

        self.logger.debug(f'座位编号 {seat_code} 对应的 sid 为 {sid}')

        return sid


if __name__ == '__main__':
    reverse = Reserve()
    reverse.run()
