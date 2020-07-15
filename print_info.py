import re
import os
import subprocess
import sqlite3
import pprint

list_cmd = []


def isFileExists(strfile):
    # 检查文件是否存在
    return os.path.isfile(strfile)


def get_target_file(filename):
    list_file = []
    file_last = None
    all_file = (os.listdir('.'))
    for file in all_file:
        if filename in file:
            list_file.append(file)
    list_file.sort(reverse=True)
    return list_file


def get_log():
    log_path = "./Hydra_log.log"
    logfilename = 'Hydra_log.log'
    id = (None,)
    re_ = re.compile(r'\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?\]?)\]', re.DOTALL)
    if not isFileExists(log_path):
        print('no file')
        return

    for file in get_target_file(logfilename):
        f = open('./' + file)
        content = f.read()
        file_data = re_.findall(content)

        for data_one in file_data:
            if data_one[2] == 'T' and data_one[3] == 'INFO':
                print(data_one[7])

        f.close()


get_log()
