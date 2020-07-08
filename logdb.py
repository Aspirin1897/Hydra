import re
import os
import subprocess
import sqlite3
import pprint
import consts

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

class LogDB():
    create_table_sql = '''
    create table if not exists logtable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time DATE(30),
        transaction_id varchar(20),
        display varchar(5),
        type1 TEXT,
        type2 TEXT,
        describe1 TEXT,
        describe2 TEXT,
        data TEXT
        );'''

    insert_sql = '''
    replace into logtable
    (
        id,
        time,
        transaction_id,
        display,
        type1,
        type2,
        describe1,
        describe2,
        data
        )
    values(?,?,?,?,?,?,?,?,?)
    '''


    drop_table_sql = "DROP TABLE if exists logtable "

    def __init__(self):
        self.con = sqlite3.connect("logDB.db", check_same_thread=False)
        self.cur = self.con.cursor()


    def insert(self, data):
        self.cur.execute(self.insert_sql, data)

    def drop_tb(self):
        self.cur.execute(self.drop_table_sql)
        self.con.commit()

    # 获取表单行数据的通用方法
    def sql_fetch_one(self, sql):
        self.cur.execute(sql)
        date_set = self.cur.fetchone()
        return date_set

    # 获取表全部数据的通用方法
    def sql_fetch_all(self, sql):
        cur = self.cur
        cur.execute(sql)
        date_set = cur.fetchall()
        return list(date_set)

    def get_all_via_tid(self, transaction_id):
        sql = "SELECT type1,type2,describe1,describe2,data FROM logtable WHERE display = 'T' and transaction_id = '%s'" % transaction_id
        return self.sql_fetch_all(sql)

    def get_cmd_result(self,oprt_id):
        sql = "SELECT data FROM logtable WHERE type1 = 'DATA' and type2 = 'cmd' and describe2 = '%s'"%(oprt_id)
        return self.sql_fetch_one(sql)

    def get_oprt_id(self,transaction_id,describe1):
        sql = "SELECT data FROM logtable WHERE type1 = 'DATA' and type2 = 'oprt_id' and transaction_id= '%s' and describe1 = '%s'"%(transaction_id,describe1)
        return self.sql_fetch_one(sql)

    def get_id(self,transaction_id,data,id_now = 0):
        sql = f"SELECT id FROM logtable WHERE transaction_id = '{transaction_id}' and data = '{data}' and id > id_now"
        return self.sql_fetch_one(sql)


    def find_oprt_id_via_string(self,transaction_id,string):
        id_now = consts.get_value('ID')
        # id_now = 20
        sql = f"SELECT id,describe2 FROM logtable WHERE data = '{string}' and id > {id_now} and transaction_id = '{transaction_id}'"
        id_and_oprt_id = self.sql_fetch_one(sql)
        # sql = f"SELECT describe2 FROM logtable WHERE id = '{db_id}' "
        # oprt_id = self.sql_fetch_one(sql)
        return id_and_oprt_id

    def get_string_id(self,transaction_id):
        sql = f"SELECT data FROM logtable WHERE describe1 = 'Start a new trasaction' and transaction_id = '{transaction_id}'"
        _id = self.sql_fetch_one(sql)
        if _id:
            _id = _id[0]
        sql = f"SELECT data FROM logtable WHERE describe1 = 'unique_str' and transaction_id = '{transaction_id}'"
        string = self.sql_fetch_one(sql)
        if string:
            string = string[0]

        return (string, _id)
        # re_ = re.compile(r'Start to create lun, name: (.*)_(.*)')
        # return re_.findall(result[0])

    def get_data_via_id(self,id):
        sql = f"SELECT data FROM logtable WHERE id = '{id}' and display = 'T' and type1 = 'INFO'"
        return self.sql_fetch_one(sql)

    def print_info_via_tid(self,transaction_id):
        all_data = self.get_all_via_tid(transaction_id)
        for data in all_data:
            if data[0] == 'INFO':
                print(data[4])

    def get_logdb(self):
        self.drop_tb()
        self.cur.execute(self.create_table_sql)
        self.con.commit()
        log_path = "./Hydra_log.log"
        logfilename = 'Hydra_log.log'
        id = (None,)
        re_ = re.compile(r'\[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?)\] \[(.*?\]?)\]\|', re.DOTALL)
        if not isFileExists(log_path):
            print('no file')
            return

        for file in get_target_file(logfilename):
            f = open('./' + file)
            content = f.read()
            file_data = re_.findall(content)
            for data_one in file_data:
                data = id + data_one
                self.insert(data)

            f.close()

        self.con.commit()



if __name__ == "__main__":
    db = LogDB()
    db.get_logdb()
    print(db.get_string_id('1594111612')) #找不到这个id的异常处理
    db.find_oprt_id_via_string('usnkegs')
    print(db.get_cmd_result('1415191169'))

