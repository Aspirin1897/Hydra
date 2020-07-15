# coding:utf-8
import logging
import logging.handlers
import logging.config
import consts
from functools import wraps
import traceback
import sys
import os
import getpass
import socket


class MyLoggerAdapter(logging.LoggerAdapter):
    """
    实现一个LoggerAdapter的子类，重写process()方法。
    其中对于kwargs参数的操作应该是先判断其本身是否包含extra关键字，如果包含则不使用默认值进行替换；
    如果kwargs参数中不包含extra关键字则取默认值。
    """

    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs["extra"] = self.extra
        return msg, kwargs


class Log(object):
    # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
    fmt = logging.Formatter(
        "%(asctime)s [%(transaction_id)s] [%(display)s] [%(type_level1)s] [%(type_level2)s] [%(describe1)s] [%(describe2)s] [%(data)s]|",
        datefmt='[%Y/%m/%d %H:%M:%S]')
    handler_input = logging.handlers.RotatingFileHandler(filename='Hydra_log.log', mode='a', maxBytes=10 * 1024 * 1024,
                                                         backupCount=5)
    handler_input.setFormatter(fmt)

    def __init__(self, transaction_id):
        self.transaction_id = transaction_id
        # self.log_switch = consts.get_value('LOG_SWITCH')
        # self.time = None
        # self.type1 = None
        # self.type2 = None
        # self.d1 = None
        # self.d2 = None

        # t1:data t2:ssh d1:host

    def logger_create(self):
        logger_hydra = logging.getLogger('hydra')
        logger_hydra.addHandler(self.handler_input)
        logger_hydra.setLevel(logging.DEBUG)
        extra_dict = {
            "transaction_id": "",
            "display": "",
            "type_level1": "",
            "type_level2": "",
            "describe1": "",
            "describe2": "",
            "data": ""}
        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(logger_hydra, extra_dict)
        return logger

    # write to log file
    def write_to_log(self, display, type1, type2, describe1, describe2, data):
        logger_hydra = self.logger_create()

        if consts.get_value('LOG_SWITCH') == 'OFF':
            logger_hydra.logger.removeHandler(self.handler_input)

        logger_hydra.debug(
            '',
            extra={
                'transaction_id': self.transaction_id,
                'display': display,
                'type_level1': type1,
                'type_level2': type2,
                'describe1': describe1,
                'describe2': describe2,
                'data': data}
        )
