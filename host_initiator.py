# coding:utf-8

import connect as c
import re
import sys
import time
import sundry as s

vplx_ip = '10.203.1.199'
host = '10.203.1.200'
port = '22'
user = 'root'
password = 'password'
timeout = 3

mount_point = '/mnt'


class HostTest(object):
    '''
    Format, write, and read iSCSI LUN
    '''

    def __init__(self, unique_id):
        self.ssh = c.ConnSSH(host, port, user, password, timeout)
        self.id = unique_id
        self.dev_name=None

    def initiator_login(self):
        '''
        Discover iSCSI and login to session
        '''
        login_cmd = f'iscsiadm -m discovery -t st -p {vplx_ip} -l'
        login_result = self.ssh.excute_command(login_cmd)
        if s.iscsi_login(vplx_ip, login_result):
            return True

    def initiator_session(self):
        '''
        Execute the command and check up the status of session
        '''
        session_cmd = 'iscsiadm -m session'
        session_result = self.ssh.excute_command(session_cmd)
        if s.find_session(vplx_ip, session_result):
            return True

    # def _find_device(self, command_result):
    #     '''
    #     Use re to find device_path
    #     '''
    #     re_find_id_dev = re.compile(
    #         r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})')
    #     re_result = re_find_id_dev.findall(command_result)

    #     # [('0', '/dev/sdb'), ('1', '/dev/sdc')]
    #     if re_result:
    #         dic_result = dict(re_result)
    #         if str(self.id) in dic_result.keys():
    #             dev_path = dic_result[str(self.id)]
    #             return dev_path

    def explore_disk(self):
        '''
         Scan and get the device path from VersaPLX
        '''
        if self.ssh.excute_command('/usr/bin/rescan-scsi-bus.sh'):
            time.sleep(0.5)
            lsscsi_result = self.ssh.excute_command('lsscsi')
        else:
            s.pe(f'Scan new LUN failed on VersaPLX')
        re_find_id_dev = r'\:(\d*)\].*LIO-ORG[ 0-9a-zA-Z._]*(/dev/sd[a-z]{1,3})'
        self.dev_name=s.GetDiskPath(self.id, re_find_id_dev, lsscsi_result, 'VersaPLX').explore_disk()

    def retry_rescan(self):
        self.explore_disk()
        if self.dev_name:
            print(f'Find device {self.dev_name} for LUN id {self.id}')
            return self.dev_name
        else:
            print('Rescanning...')
            self.explore_disk()
            if not self.dev_name:
                s.pe('Did not find the new LUN from Netapp,program exit...')


    def _judge_format(self, arg_bytes):
        '''
        Determine the format status
        '''
        re_done = re.compile(r'done')
        string = arg_bytes.decode('utf-8')
        if len(re_done.findall(string)) == 4:
            return True

    def format_mount(self, dev_name):
        '''
        Format disk and mount disk
        '''
        format_cmd = f'mkfs.ext4 {dev_name} -F'
        cmd_result = self.ssh.excute_command(format_cmd)
        if self._judge_format(cmd_result):
            mount_cmd = f'mount {dev_name} {mount_point}'
            if self.ssh.excute_command(mount_cmd) == True:
                return True
            else:
                s.pe(f"mount {dev_name} to {mount_point} failed")

        else:
            s.pe("format disk %s failed" % dev_name)

    def _get_dd_perf(self, arg_str):
        '''
        Use re to get the speed of test
        '''
        re_performance = re.compile(r'.*s, ([0-9.]* [A-Z]B/s)')
        string = arg_str.decode('utf-8')
        re_result = re_performance.findall(string)
        perf = re_result
        if perf:
            return perf[0]
        else:
            s.pe('Can not get test result')

    def write_test(self):
        '''
        Execute command for write test
        '''
        test_cmd = f'dd if=/dev/zero of={mount_point}/t.dat bs=512k count=16'
        test_result = self.ssh.excute_command(test_cmd)
        time.sleep(0.5)
        if test_result:
            return self._get_dd_perf(test_result)

    def read_test(self):
        '''
        Execute command for read test
        '''
        test_cmd = f'dd if={mount_point}/t.dat of=/dev/zero bs=512k count=16'
        test_result = self.ssh.excute_command(test_cmd)
        if test_result:
            return self._get_dd_perf(test_result)

    def get_test_perf(self):
        '''
        Calling method to read&write test
        '''
        write_perf = self.write_test()
        print(f'write speed: {write_perf}')
        time.sleep(0.5)
        read_perf = self.read_test()
        print(f'read speed: {read_perf}')

    def start_test(self):
        if not self.initiator_session():
            self.initiator_login()
        dev_name = self.retry_rescan()
        mount_status = self.format_mount(dev_name)
        if mount_status:
            self.get_test_perf()
        else:
            s.pe(f'Device {dev_name} mount failed')

    def initiator_rescan(self):
        '''
        initiator rescan after delete
        '''
        rescan_cmd = 'rescan-scsi-bus.sh -r'
        self.ssh.excute_command(rescan_cmd)


if __name__ == "__main__":
    test = HostTest(21)

    # command_result = '''[2:0:0:0]    cd/dvd  NECVMWar VMware SATA CD00 1.00  /dev/sr0
    # [32:0:0:0]   disk    VMware   Virtual disk     2.0   /dev/sda
    # [33:0:0:15]  disk    LIO-ORG  res_lun_15       4.0   /dev/sdb
    # [33:0:0:21]  disk    LIO-ORG  res_luntest_21   4.0   /dev/sdc '''
    # print(command_result)
