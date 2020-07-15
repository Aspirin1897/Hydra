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



# global _ID
# global _STR
# global _RPL
# global _TID

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
    oprt_id = s.get_oprt_id()
    logger.write_to_log('T', 'INFO', 'info', 'start', '', f'  Discover_new_lun for id {consts.get_id()}')
    # self.logger.write_to_log('INFO','info','',f'start to discover_new_lun for id {ID}')
    logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd_rescan)
    result_rescan = SSH.execute_command(cmd_rescan)
    logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_rescan)
    # print(result_rescan)
    if result_rescan['sts']:
        oprt_id = s.get_oprt_id()
        cmd_lsscsi = 'lsscsi'
        logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd_lsscsi)
        result_lsscsi = SSH.execute_command(cmd_lsscsi)
        logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_lsscsi)
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
        str(consts.get_id()), re_find_id_dev, result_lsscsi, 'NetApp', logger)

    print(f'  Find device {blk_dev_name} for LUN id {consts.get_id()}')
    logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                        f'    Find device {blk_dev_name} for LUN _ {consts.get_id()}')
    # self.logger.write_to_log('INFO', 'info', '', f'Find device {blk_dev_name} for LUN id {ID}')
    return blk_dev_name


def retry_rescan(logger):
    cmd_rescan = '/usr/bin/rescan-scsi-bus.sh'
    blk_dev_name = discover_new_lun(logger, cmd_rescan)
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


def get_ssh_cmd(logger, unique_str, cmd, oprt_id):
    _RPL = consts.get_rpl()
    if _RPL == 'no':
        logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
        logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd)
        result_cmd = SSH.execute_command(cmd)
        logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_cmd)
        if result_cmd['sts']:
            return result_cmd['rst'].decode('utf-8')
        else:
            print('execute drbd init command failed')
    elif _RPL == 'yes':
        db = logdb.LogDB()
        db_id, oprt_id = db.find_oprt_id_via_string(consts.get_tid(), unique_str)
        # now_id = consts.get_value('ID')
        # print(f'DB ID now is : {now_id}')
        # print(f'  DB ID go to: {db_id}')
        # print(f'  get opration ID: {oprt_id}')
        info_start = db.get_info_start(oprt_id)
        if info_start:
            print(info_start)
        result_cmd = db.get_cmd_result(oprt_id)
        if result_cmd:
            result_cmd = eval(result_cmd)
            if result_cmd['sts']:
                result = result_cmd['rst'].decode('utf-8')
            else:
                result = None
                print('execute drbd init command failed')
        info_end = db.get_info_finish(oprt_id)
        if info_end:
            print(info_end)
        s.change_pointer(db_id)
        # print(f'  Change DB ID to: {db_id}')
        return result


class VplxDrbd(object):
    '''
    Integrate LUN in DRBD resources
    '''

    def __init__(self, logger):
        self.logger = logger
        self._STR = consts.get_str()
        self._ID = consts.get_id()
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 'Start to configure DRDB resource and crm resource on VersaPLX')
        print('Start to config DRBD resource...')
        self.res_name = f'res_{self._STR}_{self._ID}'
        global DRBD_DEV_NAME
        DRBD_DEV_NAME = f'drbd{self._ID}'
        _RPL = consts.get_rpl()
        if _RPL == 'no':
            init_ssh(self.logger)
            self.blk_dev_name = retry_rescan(logger)

        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'    Start to configure DRBD resource {self.res_name}')

    def prepare_config_file(self):
        '''
        Prepare DRDB resource config file
        '''
        _RPL = consts.get_rpl()
        if _RPL == 'yes':
            return

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
                # logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd_rescan)
                echo_result = SSH.execute_command(
                    f'echo {context[i]} > /etc/drbd.d/{config_file_name}')
                # logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd_rescan) 输出
            else:
                echo_result = SSH.execute_command(
                    f'echo {context[i]} >> /etc/drbd.d/{config_file_name}')
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
        print(f'  config file "{self.res_name}.res" created')
        self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                 f'      Create DRBD config file "{self.res_name}.res" done')
        # [time],[transaction_id],[display],[INFO],[info],[finish],[d2],[data]
        # self.logger.write_to_log('INFO','info','',f'Create DRBD config file "{self.res_name}.res" done')\

    # def execute_drbd_cmd(self,unique_str,cmd):
    #     now_id = consts.get_value('ID')
    #     print(f'DB ID now is : {now_id}')
    #     if _RPL == 'no':
    #         print(cmd)
    #         oprt_id = s.get_oprt_id()
    #         self.logger.write_to_log('F', 'DATA', 'STR', unique_str, '', oprt_id)
    #         self.logger.write_to_log('T', 'OPRT', 'cmd', 'ssh', oprt_id, cmd)
    #         result_cmd = SSH.execute_command(cmd)
    #         print(result_cmd)
    #         self.logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, result_cmd)
    #         if result_cmd['sts']:
    #             return result_cmd['rst'].decode('utf-8')
    #         else:
    #             print('execute drbd init command failed')
    #             sys.exit()
    #     elif _RPL == 'yes':
    #         db = logdb.LogDB()
    #         db.get_logdb()
    #         ww = db.find_oprt_id_via_string(_TID, unique_str)
    #         db_id, oprt_id = ww
    #         print(f'  DB ID go to: {db_id}')
    #         print(f'  get opration ID: {oprt_id}')
    #         result_cmd = db.get_cmd_result(oprt_id)
    #         if result_cmd:
    #             result_cmd = eval(result_cmd[0])
    #             if result_cmd['sts']:
    #                 result = result_cmd['rst'].decode('utf-8')
    #             else:
    #                 result = None
    #                 print('execute drbd init command failed')
    #         s.change_pointer(db_id)
    #         print(f'  Change DB ID to: {db_id}')
    #         return result

    def _drbd_init(self):
        '''
        Initialize DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'usnkegs'
        cmd = f'drbdadm create-md {self.res_name}'

        info_msg = f'      Initialize drbd for {self.res_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id, info_msg)

        init_result = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        re_drbd = re.compile('New drbd meta data block successfully created')
        re_init = re_drbd.findall(init_result)
        # oprt_id = s.get_oprt_id()
        # self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {'New drbd meta data block successfully created':drbd_init})
        # self.logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_init)
        if re_init:
            print(f'  Resource "{self.res_name}" initialize successful')
            return True
        else:
            s.pwe(self.logger, f'drbd resource {self.res_name} initialize failed')

    def _drbd_up(self):
        '''
        Start DRBD resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'elsflsnek'
        cmd = f'drbdadm up {self.res_name}'
        result = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result != None:
            print(f'  Resource "{self.res_name}" bring up successful')
            return True

    def _drbd_primary(self):
        '''
        Complete initial synchronization of resources
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '7C4LU6Xr'
        cmd = f'drbdadm primary --force {self.res_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '',
                                 f'      Start to initial synchronization for {self.res_name}')
        result = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result != None:
            print(f'    {self.res_name} synchronize successfully')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                     f'    {self.res_name} synchronize successfully')
            return True
        else:
            s.pwe(self.logger, f'drbd resource {self.res_name} primary failed')
        # drbd_primary = SSH.execute_command(primary_cmd)
        # if drbd_primary['sts']:
        #     print(f'{self.res_name} primary success')
        #     self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', f'      {self.res_name} synchronize successfully')
        #     # self.logger.write_to_log('INFO','info','',(f'{self.res_name} primary success'))
        #     return True
        # else:
        #     s.pwe(self.logger,f'drbd resource {self.res_name} primary failed')

    def drbd_cfg(self):
        if self._drbd_init():
            if self._drbd_up():
                if self._drbd_primary():
                    return True

    def drbd_status_verify(self):
        '''
        Check DRBD resource status and confirm the status is UpToDate
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'By91GFxC'
        cmd = f'drbdadm status {self.res_name}'

        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', '      Start to check DRBD resource status')
        result = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result:
            re_display = re.compile(r'''disk:(\w*)''')
            re_result = re_display.findall(result)
            oprt_id = s.get_oprt_id()
            self.logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, result)
            if re_result:
                status = re_result[0]
                self.logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, status)
                if status == 'UpToDate':
                    print(f'    {self.res_name} DRBD check successfully')
                    self.logger.write_to_log('T', 'INFO', 'info', 'finish', '',
                                             f'    {self.res_name} DRBD check successfully')
                    # self.logger.write_to_log('INFO','info','',(f'{self.res_name} DRBD check successful'))
                    return True
                else:
                    s.pwe(self.logger, f'{self.res_name} DRBD verification failed')
            else:
                s.pwe(self.logger, f'{self.res_name} DRBD does not exist')


class VplxCrm(object):
    def __init__(self, logger):
        init_ssh(logger)
        self.logger = logger
        self._ID = consts.get_id()
        self._STR = consts.get_str()
        self._RPL = consts.get_rpl()
        self.lu_name = f'res_{self._STR}_{self._ID}'  # same as drbd resource name
        self.colocation_name = f'co_{self.lu_name}'
        self.order_name = f'or_{self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', f'  Start to configure crm resource {self.lu_name}')
        # self.logger.write_to_log('INFO','info','',f'start to config crm resource {self.lu_name}') #

    def _crm_create(self):
        '''
        Create iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'LXYV7dft'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 f'    Start to create iSCSILogicalUnit resource {self.lu_name}')
        cmd = f'crm conf primitive {self.lu_name} \
            iSCSILogicalUnit params target_iqn="{target_iqn}" \
            implementation=lio-t lun={consts.get_id()} path="/dev/{DRBD_DEV_NAME}"\
            allowed_initiators="{initiator_iqn}" op start timeout=40 interval=0 op stop timeout=40 interval=0 op monitor timeout=40 interval=50 meta target-role=Stopped'
        result = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result != None:
            print('    Create iSCSILogicalUnit successfully')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', '    Create iSCSILogicalUnit successfully')
            return True
        else:
            s.pwe(self.logger, 'iscisi lun_create failed')

    def _setting_col(self):
        '''
        Setting up iSCSILogicalUnit resources of colocation
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'E03YgRBd'
        cmd = f'crm conf colocation {self.colocation_name} inf: {self.lu_name} {target_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 '      start to setting up iSCSILogicalUnit resources of colocation')
        result_crm = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result_crm != None:
            print('      Setting colocation successful')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', '      Setting colocation successful')
            return True
        else:
            s.pwe(self.logger, 'setting colocation failed')

    def _setting_order(self):
        '''
        Setting up iSCSILogicalUnit resources of order
        '''
        oprt_id = s.get_oprt_id()
        unique_str = '0GHI63jX'
        cmd = f'crm conf order {self.order_name} {target_name} {self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 '      Start to setting up iSCSILogicalUnit resources of order')
        result_crm = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result_crm != None:
            print('      Setting order succeed')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', '      Setting order succeed')
            return True
        else:
            s.pwe(self.logger, 'setting order failed')

    def _crm_setting(self):
        if self._setting_col():
            if self._setting_order():
                return True

    def _crm_start(self):
        '''
        start the iSCSILogicalUnit resource
        '''
        oprt_id = s.get_oprt_id()
        unique_str = 'YnTDsuVX'
        cmd = f'crm res start {self.lu_name}'
        self.logger.write_to_log('T', 'INFO', 'info', 'start', oprt_id,
                                 f'      Start the iSCSILogicalUnit resource {self.lu_name}')
        result_cmd = get_ssh_cmd(self.logger, unique_str, cmd, oprt_id)
        if result_cmd != None:
            print('      ISCSI LUN start successful')
            self.logger.write_to_log('T', 'INFO', 'info', 'finish', '', '      ISCSI LUN start successful')
            return True
        else:
            s.pwe(self.logger, 'iscsi lun start failed')

    def crm_cfg(self):
        if self._crm_create():
            if self._crm_setting():
                if self._crm_start():
                    return True

    def crm_verify(self):
        pass

# if __name__ == '__main__':
#     test_crm = VplxCrm('72', 'luntest')
#     test_crm.discover_new_lun()
