# coding:utf-8

def _init():  # 初始化
    global _global_dict
    _global_dict = {'ID': 0}


def set_value(key, value):
    """ 定义一个全局变量 """
    _global_dict[key] = value


def get_value(key, defValue=0):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _global_dict[key]
    except KeyError:
        return defValue

def get_str():
    return get_value('str_one')

def get_id():
    return get_value('id_one')

def get_rpl():
    return get_value('RPL')

def get_tid():
    return get_value('tid')