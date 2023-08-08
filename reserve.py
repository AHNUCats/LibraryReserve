import json
import logging
import datetime
import time
from random import random
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, StringVar
from typing import Tuple
from abc import ABC, abstractmethod
import requests
from typing import Callable


# MAP = {
#     '花津二楼报刊阅览室': ('nbk', 430),
#     '花津二楼电子阅览室': ('ndz', 188),
#     '花津三楼社科一': ('nsk1', 342),
#     '花津三楼自然阅览室': ('nzr1', 343),
#     '花津三楼公共东': ('ngg3e', 96),
#     '花津三楼公共西': ('ngg3w', 96),
#     '花津四楼社科三': ('nsk3', 318),
#     '花津四楼社科二': ('nsk2', 302),
#     '花津四楼公共东': ('ngg4e', 88),
#     '花津四楼公共西': ('ngg4w', 100),
#     '花津五楼公共': ('ngg5', 37),
#     '赭山文科室': ('zsk1', 112),
#     '赭山理科室': ('zzr1', 112),
#     '赭山电子阅览室': ('zdz', 66)
# }

class Event:
    def __init__(self, event_type: str, data: dict):
        self.__event_type: str = event_type
        self.__data: dict = data

    def get_type(self) -> str:
        return self.__event_type

    def get_data(self) -> dict:
        return self.__data


class EventDispatcher:
    def __init__(self):
        self.__listeners = {}

    def add_listener(self, event_type: str, listener: Callable):
        if event_type not in self.__listeners:
            self.__listeners[event_type] = []
        self.__listeners[event_type].append(listener)

    def remove_listener(self, event_type: str, listener: Callable):
        if event_type in self.__listeners:
            if listener in self.__listeners[event_type]:
                self.__listeners[event_type].remove(listener)

    def dispatch_event(self, event: Event):
        event_type = event.get_type()
        if event_type in self.__listeners:
            for listener in self.__listeners[event_type]:
                listener(event)


class Logger:
    def __init__(self, name, level=logging.INFO, filename='log.txt'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        self.file_handler = logging.FileHandler(filename)
        self.file_handler.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m-%d %H:%M:%S')

        self.file_handler.setFormatter(formatter)

        self.logger.addHandler(self.file_handler)


class UI:
    @staticmethod
    def create_window(title: str, geometry: str = '300x300') -> tk.Tk:
        window = tk.Tk()
        window.title(title)
        window.geometry(geometry)

        return window

    @staticmethod
    def create_radio_inline(root: tk.Tk, radio_options: tuple) -> tk.StringVar:
        frame = tk.Frame(root)

        radio_var = tk.StringVar()
        for option in radio_options:
            radio_button = tk.Radiobutton(frame, text=option, variable=radio_var, value=option)
            radio_button.pack(side=tk.LEFT)
        radio_var.set(radio_options[-1])

        frame.pack()

        return radio_var

    @staticmethod
    def create_combobox(root: tk.Tk, combobox_txt: tuple) -> tk.StringVar:
        frame = tk.Frame(root)

        combobox_var = tk.StringVar()
        combobox = ttk.Combobox(frame, textvariable=combobox_var, values=combobox_txt)
        combobox.pack()

        frame.pack()

        return combobox_var

    @staticmethod
    def create_button(root: tk.Tk, button_text: str) -> tk.Button:
        button = tk.Button(root, text=button_text)
        button.pack()

        return button

    @staticmethod
    def create_entry(root: tk.Tk, label_text: str) -> tk.Entry:
        frame = tk.Frame(root)

        entry = tk.Entry(frame)
        tk.Label(frame, text=label_text).pack(side=tk.LEFT)
        entry.pack(side=tk.LEFT)

        frame.pack()

        return entry

    @staticmethod
    def create_time_selector(root: tk.Tk, label_text: str, hour_from: int = 0, hour_to: int = 23, minute_from: int = 0,
                             minute_to: int = 59) -> tuple[tk.StringVar, tk.StringVar]:
        frame = tk.Frame(root)

        hour_var = tk.StringVar()
        hour_var.set("00")
        hour_spinbox = tk.Spinbox(frame, from_=hour_from, to=hour_to, width=2, textvariable=hour_var)

        minute_var = tk.StringVar()
        minute_var.set("00")
        minute_spinbox = tk.Spinbox(frame, from_=minute_from, to=minute_to, width=2, textvariable=minute_var)

        tk.Label(frame, text=label_text).pack(side=tk.LEFT)
        hour_spinbox.pack(side=tk.LEFT)
        tk.Label(frame, text=":").pack(side=tk.LEFT)
        minute_spinbox.pack(side=tk.LEFT)

        frame.pack()

        return hour_var, minute_var

    @staticmethod
    def create_text_widget(root: tk.Tk) -> tk.Text:
        text_widget = tk.Text(root)
        text_widget.pack()

        return text_widget


class Observer(ABC):
    @abstractmethod
    def update(self, *args, **kwargs):
        pass


class App:
    def __init__(self, event_dispatcher: EventDispatcher):
        # ---------------------------------------事件系统---------------------------------------
        self.event_dispatcher = event_dispatcher
        self.event_dispatcher.add_listener("reserve_button_clicked", self.reserve_button_clicked)
        self.event_dispatcher.add_listener("reservation_notification", self.show_notification)

        # ---------------------------------------图形界面---------------------------------------
        self.window = UI.create_window('安师大图书馆预约')

        self.seat_entry: tk.Entry = UI.create_entry(self.window, '座位号：')
        self.account_entry: tk.Entry = UI.create_entry(self.window, '学号：')
        self.password_entry: tk.Entry = UI.create_entry(self.window, '密码：')

        radio_options = ('今日', '明日')
        self.day_radio: tk.StringVar = UI.create_radio_inline(self.window, radio_options)

        self.start_hour, self.start_minute = UI.create_time_selector(self.window, '起始时间：', hour_from=6)
        self.end_hour, self.end_minute = UI.create_time_selector(self.window, '结束时间：', hour_from=6)

        self.reserve_button: tk.Button = UI.create_button(self.window, '预约')

        self.text_widget: tk.Text = UI.create_text_widget(self.window)

        self.reserve_button.bind("<Button-1>", self.reserve_button_clicked)

    def get_data(self) -> dict[str:str]:
        return {'seat_code': self.seat_entry.get(),
                'account': self.account_entry.get(),
                'password': self.password_entry.get(),
                'day': self.day_radio.get(),
                'start_hour': self.start_hour.get(),
                'start_minute': self.start_minute.get(),
                'end_hour': self.end_hour.get(),
                'end_minute': self.end_minute.get()
                }

    def reserve_button_clicked(self, data):
        reserve = Reserve(self.event_dispatcher)
        reserve.reserve(self.get_data())

    def show_notification(self, event):
        if 'WARNING' in event.get_data()['level']:
            messagebox.showwarning('警告', event.get_data()['message'])
        elif 'INFO' in event.get_data()['level']:
            self.text_widget.insert(tk.END, event.get_data()['message'] + '\n')
            self.text_widget.see(tk.END)

    def run(self):
        self.window.mainloop()


class Reserve:
    def __init__(self, event_dispatcher: EventDispatcher):
        self.session = requests.Session()

        self.logger = Logger('reserve_logger').logger

        self.event_dispatcher = event_dispatcher
        self.event_dispatcher.add_listener("reservation_notification", self.reservation_notification)

    def reservation_notification(self, level, message):
        self.event_dispatcher.dispatch_event(
            Event("reservation_notification", {'level': level, "message": message}))

    def reserve(self, data):
        try:
            self.logger.info('开始预约')
            self.reservation_notification('INFO', '开始预约')

            self.__login(data['account'], data['password'])

            header = {
                'Host': 'libzwxt.ahnu.edu.cn',
                'Origin': 'http://libzwxt.ahnu.edu.cn',
                'Referer': 'http://libzwxt.ahnu.edu.cn/SeatWx/Seat.aspx?fid=3&sid=1438',
                'User-Agent': "Mozilla/5.0 (Linux; Android 12; M2006J10C Build/SP1A.210812.016; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/107.0.5304.141 Mobile Safari/537.36 XWEB/5061 MMWEBSDK/20230303 MMWEBID/534 MicroMessenger/8.0.34.2340(0x2800225D) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64;",
                'X-AjaxPro-Method': 'AddOrder',
            }
            url = 'http://libzwxt.ahnu.edu.cn/SeatWx/ajaxpro/SeatManage.Seat,SeatManage.ashx'

            if data['day'] == '明日':
                atData = str(datetime.date.today() + datetime.timedelta(days=1))
            elif data['day'] == '今日':
                atData = str(datetime.date.today())

            st = f"{data['start_hour']}:{data['start_minute']}"
            et = f"{data['end_hour']}:{data['end_minute']}"

            reserve_data = {
                'atDate': atData,
                'sid': self.__convert(data['seat_code']),
                'st': st,
                'et': et,
            }

            # 尝试进行预约
            while True:
                reserve = self.session.post(url, data=json.dumps(reserve_data), headers=header)

                if '预约成功' in reserve.text:
                    self.logger.debug(reserve.text)
                    self.logger.info('预约成功，座位：{0}'.format(reserve_data['sid']))
                    break
                elif '提前' in reserve.text:
                    self.logger.debug(reserve.text)
                    self.logger.info('服务器时间不一致')
                    continue
                elif '冲突' or '重复' in reserve.text:
                    reserve_data['sid'] += 1
                    time.sleep(random() + 5)
                    self.logger.info(f"新的座位号：{reserve_data['sid']}")

        except ValueError as ve:
            self.logger.warning(ve)
            self.reservation_notification('WARNING', str(ve))
        except Exception as e:
            self.logger.warning('未知错误：' + str(e))
            self.reservation_notification('WARNING', '未知错误：' + str(e))
        except:
            self.logger.warning('未知错误：')
            self.reservation_notification('WARNING', '未知错误：')

    def __login(self, account, password) -> None:
        """
        create session and login libzwxt
        :return: void
        """
        self.logger.info('开始登陆，用户名：{0}, 密码：{1}。'.format(account, password))
        self.reservation_notification('INFO', '开始登陆，用户名：{0}, 密码：{1}。'.format(account, password))

        url = 'http://libzwxt.ahnu.edu.cn/SeatWx/login.aspx'
        data = {
            '__VIEWSTATE': '/wEPDwULLTE0MTcxNzMyMjZkZAl5GTLNAO7jkaD1B+BbDzJTZe4WiME3RzNDU4obNxXE',
            '__VIEWSTATEGENERATOR': 'F2D227C8',
            '__EVENTVALIDATION': '/wEWBQK1odvtBQLyj'
                                 '/OQAgKXtYSMCgKM54rGBgKj48j5D4sJr7QMZnQ4zS9tzQuQ1arifvSWo1qu0EsBRnWwz6pw',
            'tbUserName': account,
            'tbPassWord': password,
            'Button1': '登 录  ',
            'hfurl': ''
        }

        response = self.session.post(url=url, data=data)

        if '请输入用户名' not in response.content.decode():
            self.logger.info('登录成功！')
            self.reservation_notification('INFO', '登录成功！')
        else:
            raise ValueError('登录失败，请检查用户名和密码是否正确。')

    def __convert(self, seat_code) -> int:
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
        self.reservation_notification('DEBUG', f'座位编号 {seat_code} 对应的 sid 为 {sid}')

        return sid


if __name__ == '__main__':
    event_dispatcher = EventDispatcher()
    app = App(event_dispatcher)
    app.run()
