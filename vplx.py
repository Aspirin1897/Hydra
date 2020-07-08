#  coding: utf-8

import connect
import sundry as s
import time
import sys
import os
import re
import logdb
import consts

# global SSH
SSH = None

global _ID
global _STR
global _RPL
global _TID

host = '10.203.1.199'
port = 22
user = 'root'
password = 'password'
timeout = 3

target_iqn = "iqn.2020-06.com.example:test-max-lun"
initiator_iqn = "iqn.1993-08.org.debian:01:885240c2d86c"
target_name = 't_test'

def init_ssh(logger):
    global SSH
    if not SSH:
        SSH = connect.ConnSSH(host, port, user, password, timeout, logger)
    else:
        pass

class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self, logger):
        print('VplxDrbd __init__')
        self.res_name = f'res_{_STR}_{_ID}'
        self.logger = logger
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to configure DRDB resource and crm resource on VersaPLX')
        self.logger.write_to_log('T','INFO','info','start','',f'    Start to configure DRBD resource {self.res_name}')
    
    def prepare_config_file(self):
        pass

    def _get_drbd_init_cmd(self):
        unique_str = 'usnkegs'
        print(consts.get_value('ID'))
        print(consts.get_value('LOG_SWITCH'))
        if _RPL == 'no':
            oprt_id = s.get_oprt_id()
            cmd_drbd_init = f'drbdadm create-md {self.res_name}'
            self.logger.write_to_log('F','DATA','STR',unique_str,[],oprt_id)
            self.logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd_drbd_init)
            result_drbd_init = SSH.execute_command(cmd_drbd_init, oprt_id)
            self.logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_drbd_init)
            if result_drbd_init['sts']:
                return result_drbd_init['rst'].decode('utf-8')
            else:
                print('execute drbd init command failed')
        elif _RPL == 'yes':
            db = logdb.LogDB()
            db_id,oprt_id = db.find_oprt_id_via_string(_TID,unique_str)
            result_drbd_init = db.get_cmd_result(oprt_id)
            if result_drbd_init:
                result_drbd_init = eval(result_drbd_init[0])
            if result_drbd_init['sts']:
                result = result_drbd_init['rst'].decode('utf-8')
            else:
                result = None
                print('execute drbd init command failed')
            s.change_pointer(db_id)
            print(consts.get_value('ID'))
            return result

    def _drbd_init(self):
        '''
        Initialize DRBD resource
        '''
        info_msg = f'      Initialize drbd for {self.res_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', info_msg)

        init_result = self._get_drbd_init_cmd()
        print('ID:',consts.get_value('ID'))
        re_drbd = re.compile('New drbd meta data block successfully created')
        re_init = re_drbd.findall(init_result)
        # oprt_id = s.get_oprt_id()
        # self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {'New drbd meta data block successfully created':drbd_init})
        # self.logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_init)
        if re_init:
            print(f'{self.res_name} initialize success')
            # self.logger.write_to_log('INFO','info','',(f'{self.res_name} initialize success'))
            return True
        else:
            s.pwe(self.logger, f'drbd resource {self.res_name} initialize failed')



    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        up_cmd = f'drbdadm up {self.res_name}'
        unique_str = '_drdb_up'
        if _RPL == 'no':
            oprt_id = s.get_oprt_id()
            self.logger.write_to_log('T','INFO','info','start','',f'      Start to drbd up for {self.res_name}')
            # self.logger.write_to_log('F','DATA','oprt_id',oprt_id_dec,'',oprt_id) #还需要吗
            self.logger.write_to_log('F', 'DATA', '', '', oprt_id, unique_str)
            self.logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, up_cmd)
            drbd_up = SSH.execute_command(up_cmd)
            self.logger.write_to_log('F','DATA','cmd','ssh',oprt_id,drbd_up)
            if drbd_up['sts']:
                print(f'{self.res_name} up success')
                self.logger.write_to_log('T','INFO','info','finish','',f'      {self.res_name} started successfully')
                return True
            else:
                s.pwe(self.logger,f'drbd resource {self.res_name} up failed')
        elif _RPL == 'yes':
            print('-------------------------------------')
            print('_drbd_up replay:')
            db = logdb.LogDB()
            db_id,oprt_id = db.find_oprt_id_via_string(_TID,unique_str)
            drbd_up = db.get_cmd_result(oprt_id)
            if drbd_up:
                drbd_up = eval(drbd_up[0])
            s.change_pointer(db_id)
            print('ID:',consts.get_value('ID'))
            if drbd_up['sts']:
                print(f'{self.res_name} up success')
                return True
            else:
                print(f'drbd resource {self.res_name} up failed')
                sys.exit()


    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        self.logger.write_to_log('T','INFO','info','start','',f'      Start to initial synchronization for {self.res_name}')
        primary_cmd = f'drbdadm primary --force {self.res_name}'
        drbd_primary = SSH.execute_command(primary_cmd)
        if drbd_primary['sts']:
            print(f'{self.res_name} primary success')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', f'      {self.res_name} synchronize successfully')
            return True
        else:
            s.pwe(self.logger,f'drbd resource {self.res_name} primary failed')

    def drbd_cfg(self):
        if self._drbd_init():
            if self._drbd_up():
                pass
                # if self._drbd_primary():
                #     return True


# if __name__ == '__main__':
#     test_crm = VplxCrm('72', 'luntest')
#     test_crm.discover_new_lun()
