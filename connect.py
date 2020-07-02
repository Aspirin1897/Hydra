#  coding: utf-8
import paramiko
import time
import telnetlib
import sys
import sundry as s
import pprint


class ConnSSH(object):
    '''
    ssh connect to VersaPLX
    '''

    def __init__(self, host, port, username, password, timeout):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self.ssh_connect()

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            self.SSHConnection = objSSHClient
        except Exception as e:
            s.pe(f'Connect to {self._host} failed with error: {e}')

    def excute_command(self, command):
        stdin, stdout, stderr = self.SSHConnection.exec_command(command)
        data = stdout.read()
        if len(data) > 0:
            return data

        err = stderr.read()
        if len(err) > 0:
            print(err.strip())
            return err

        if data == b'':
            return True

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            self._connect()

    def close(self):
        self.SSHConnection.close()


class ConnTelnet(object):
    '''
    telnet connect to NetApp 
    '''

    def __init__(self, host, port, username, password, timeout):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self.telnet = telnetlib.Telnet()
        self.telnet_connect()

    def _connect(self):
        try:
            self.telnet.open(self._host, self._port, self._timeout)
            self.telnet.read_until(b'Username:', timeout=1)
            self.telnet.write(self._username.encode() + b'\n')
            self.telnet.read_until(b'Password:', timeout=1)
            self.telnet.write(self._password.encode() + b'\n')

        except Exception as e:
            s.pe(f'Connect to {self._host} failed with error: {e}')

    # 定义exctCMD函数,用于执行命令
    def excute_command(self, cmd):
        self.telnet.read_until(b'fas270>').decode()
        self.telnet.write(cmd.encode().strip() + b'\r')
        rely = self.telnet.read_until(b'fas270>').decode()
        self.telnet.write(b'\r')
        return rely

    def telnet_connect(self):
        self._connect()
        if not self.telnet:
            self._connect()

    def close(self):
        self.telnet.close()


if __name__ == '__main__':
    # SSH
    host = '10.203.1.199'
    port = '22'
    username = 'root'
    password = 'password'
    timeout = 5
    ssh = ConnSSH(host, port, username, password, timeout)
    strout = ssh.excute_command('rescan-scsi-bus.sh -r')
    # w = strout.decode('utf-8')
    # print(type(w))
    # print(w.split('\n'))
    # pprint.pprint(w)
    # time.sleep(2)
    # strout = ssh.excute_command('lun show -m')
    # pprint.pprint(strout)

    # telnet
    # host = '10.203.1.231'
    # Port = '23'
    # username = 'root'
    # password = 'Feixi@123'
    # timeout = 10
    # w = ConnTelnet(host, Port, username, password, timeout)
    # print(w.excute_command('lun show'))

    pass
