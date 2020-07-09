#  coding: utf-8
import connect
import time
import sundry as s
import logdb

global _ID
global _STR
global _RPL
global _TID

host = '10.203.1.231'
port = 23
username = 'root'
password = 'Feixi@123'
timeout = 3

# [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]



class Storage:
    '''
    Create LUN and map to VersaPLX
    '''


    def __init__(self,logger):

        self.logger = logger
        print('Start to configure LUN on NetApp Storage')
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to configure LUN on NetApp Storage')
        self.lun_name = f'{_STR}_{_ID}'
        if _RPL == 'no':
            self.telnet_conn = connect.ConnTelnet(host, port, username, password, timeout,logger)
        # print('Connect to storage NetApp')


    def ex_telnet_cmd(self,unique_str,cmd,oprt_id):
        if _RPL == 'no':
            self.logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
            self.logger.write_to_log('T', 'OPRT', 'cmd', 'telnet', oprt_id, cmd)
            self.telnet_conn.execute_command(cmd)
        elif _RPL == 'yes':
            db = logdb.LogDB()
            db.get_logdb()
            ww = db.find_oprt_id_via_string(_TID, unique_str)
            db_id, oprt_id = ww
            print('STORAGE:')
            print(f'  DB ID go to: {db_id}')
            print(f'  get opration ID: {oprt_id}')
            # result_cmd = db.get_cmd_result(oprt_id)
            s.change_pointer(db_id)
            print(f'  Change DB ID to: {db_id}')
            return True

    def lun_create(self):
        '''
        Create LUN with 10M bytes in size
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'jMPFwXy2'
        cmd = f'lun create -s 10m -t linux /vol/esxi/{self.lun_name}'
        info_msg = f'create lun, name: {self.lun_name}'
        print(f'  Start to {info_msg}')

        self.logger.write_to_log('T','INFO','info','start',oprt_id,f'  Start to {info_msg}')
        self.ex_telnet_cmd(unique_str,cmd,oprt_id)
        print(f'  Create LUN {self.lun_name} successful')
        self.logger.write_to_log('T','INFO','info','finish',oprt_id,f'  Create LUN {self.lun_name} successful')

    def lun_map(self):
        '''
        Map lun of specified lun_id to initiator group
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '1lvpO6N5'
        info_msg = f'map LUN, LUN name: {self.lun_name}, LUN ID: {_ID}'
        cmd = f'lun map /vol/esxi/{self.lun_name} hydra {_ID}'
        print(f'  Start to {info_msg}')
        self.logger.write_to_log('T','INFO','info','start',oprt_id,f'  Start to {info_msg}')
        self.ex_telnet_cmd(unique_str,cmd,oprt_id)
        print(f'  Finish with {info_msg}')
        self.logger.write_to_log('T','INFO','info','finish',oprt_id,f'  Finish with {info_msg}')

    def lun_create_verify(self):
        pass

    def lun_map_verify(self):
        pass


if __name__ == '__main__':
    test_stor = Storage('18', 'luntest')
    test_stor.lun_create()
    test_stor.lun_map()
    # test_stor.telnet_conn.close()
    pass
