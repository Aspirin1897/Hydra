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

def discover_new_lun(logger, cmd_rescan):
    '''
    Scan and find the disk from NetApp
    '''
    init_ssh(logger)
    logger.write_to_log('T', 'INFO', 'info', 'start', '',
                        f'  Discover_new_lun for id {_ID}')
    # self.logger.write_to_log('INFO','info','',f'start to discover_new_lun for id {ID}')
    result_rescan = SSH.execute_command(cmd_rescan,787878)
    # print(result_rescan)
    if result_rescan['sts']:
        cmd_lsscsi = 'lsscsi'
        result_lsscsi = SSH.execute_command(cmd_lsscsi, 787878)
        if result_lsscsi['sts']:
            result_lsscsi = result_lsscsi['rst'].decode('utf-8')
        else:
            print(f'command {cmd_lsscsi} execute failed')
            logger.write_to_log('T', 'INFO', 'warning', 'start',
                                '', f'command {cmd_lsscsi} execute failed')
        # log DAT:output:cmd:lsscsi:result_lsscsi
    # if SSH.execute_command('/usr/bin/rescan-scsi-bus.sh'):#新的返回值有状态和数值,以状态判断,记录数值
    #     result_lsscsi = SSH.execute_command('lsscsi')
    else:
        s.pwe(logger, f'Scan new LUN failed on NetApp')
    re_find_id_dev = r'\:(\d*)\].*NETAPP[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
    blk_dev_name = s.get_disk_dev(
        str(_ID), re_find_id_dev, result_lsscsi, 'NetApp', logger)

    print(f'Find device {blk_dev_name} for LUN id {_ID}')
    logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                        f'    Find device {blk_dev_name} for LUN _ {_ID}')
    # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
    return blk_dev_name


def retry_rescan(logger):
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    blk_dev_name = discover_new_lun(logger, cmd_rescan)
    # print(blk_dev_name)
    if blk_dev_name:
        return blk_dev_name
    else:
        print('Rescanning...')
        cmd_rescan = '/usr/bin/rescan-scsi-bus.sh -a'
        blk_dev_name = discover_new_lun(logger, cmd_rescan)
        if blk_dev_name:
            return blk_dev_name
        else:
            s.pwe(logger, 'Did not find the new LUN from Netapp,program exit...')


class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self, logger):
        print('VplxDrbd __init__')
        self.res_name = f'res_{_STR}_{_ID}'
        global DRBD_DEV_NAME
        DRBD_DEV_NAME = f'drbd{_ID}'
        self.blk_dev_name = retry_rescan(logger)
        self.logger = logger
        init_ssh(self.logger)
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', 'Start to configure DRDB resource and crm resource on VersaPLX')
        self.logger.write_to_log('T','INFO','info','start','',f'    Start to configure DRBD resource {self.res_name}')
    
    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start prepare config fiel for resource {self.res_name}')
        context = [rf'resource {self.res_name} {{',
                   rf'\ \ \ \ on maxluntarget {{',
                   rf'\ \ \ \ \ \ \ \ device /dev/{DRBD_DEV_NAME}\;',
                   rf'\ \ \ \ \ \ \ \ disk {self.blk_dev_name}\;',
                   rf'\ \ \ \ \ \ \ \ address 10.203.1.199:7789\;',
                   rf'\ \ \ \ \ \ \ \ node-id 0\;',
                   rf'\ \ \ \ \ \ \ \ meta-disk internal\;',
                   r'\ \ \ \}',
                   r'}']

        # self.logger.write_to_log('DATA','input','context',context)
        # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
        # [time],[transaction_id],[-],[DATA],[value],[list],['content of drbd config file'],[data]
        self.logger.write_to_log(
            'F', 'DATA', 'value', 'list', 'content of drbd config file', context)

        # for echo_command in context:
        #     echo_result = SSH.execute_command(
        #         f'echo {echo_command} >> /etc/drbd.d/{self.res_name}.res')
        #     if echo_result is True:
        #         continue
        #     else:
        #         s.pe('fail to prepare drbd config file..')
        config_file_name = f'{self.res_name}.res'
        for i in range(len(context)):
            if i == 0:
                echo_result = SSH.execute_command(
                    f'echo {context[i]} > /etc/drbd.d/{config_file_name}', 787878)
            else:
                echo_result = SSH.execute_command(
                    f'echo {context[i]} >> /etc/drbd.d/{config_file_name}', 787878)
            # result of ssh command like (1,'done'),1 for status, 'done' for data.
            if echo_result['sts']:
                continue
            else:
                # print('fail to prepare drbd config file..')
                # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
                # [time],[transaction_id],[s],[INFO],[error],[exit],[d2],['fail to prepare drbd config file..']
                # ??? oprt
                s.pwe(self.logger, 'fail to prepare drbd config file..')
                # sys.exit()

                # s.pwe(self.logger,'fail to prepare drbd config file..')
        print(f'create DRBD config file "{self.res_name}.res" done')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                 f'      Create DRBD config file "{self.res_name}.res" done')
        # [time],[transaction_id],[display],[INFO],[info],[finish],[d2],[data]
        # self.logger.write_to_log('INFO','info','',f'Create DRBD config file "{self.res_name}.res" done')


    def _get_drbd_init_cmd(self):
        
        unique_str = 'usnkegs'
        print(consts.get_value('ID'))
        if _RPL == 'no':
            oprt_id = s.get_oprt_id()
            cmd_drbd_init = f'drbdadm create-md {self.res_name}'
            self.logger.write_to_log('F','DATA','STR',unique_str,'',oprt_id)
            self.logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd_drbd_init)
            result_drbd_init = SSH.execute_command(cmd_drbd_init, oprt_id)
            print(result_drbd_init)
            self.logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_drbd_init)
            if result_drbd_init['sts']:
                return result_drbd_init['rst'].decode('utf-8')
            else:
                print('execute drbd init command failed')
        elif _RPL == 'yes':
            db = logdb.LogDB()
            ww = db.find_oprt_id_via_string(_TID,unique_str)
            print(ww)
            db_id,oprt_id = ww
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
        print('---------------')
        print(init_result)
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
            drbd_up = SSH.execute_command(up_cmd, 787878)
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
        self.prepare_config_file()
        if self._drbd_init():
            if self._drbd_up():
                pass
                # if self._drbd_primary():
                #     return True


# if __name__ == '__main__':
#     test_crm = VplxCrm('72', 'luntest')
#     test_crm.discover_new_lun()
