#  coding: utf-8
import paramiko
import time
import telnetlib
import sys
import sundry as s
import pprint
import traceback

global replay

class ConnSSH(object):
    '''
    ssh connect to VersaPLX
    '''

    def __init__(self, host, port, username, password, timeout,logger):
        self.logger = logger
        self.logger.d1 = host
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self._connect()


    def _connect(self):
        self.logger.write_to_log('T', 'INFO', 'info', 'start', '', '  Start to connect VersaPLX via SSH')
        self.logger.write_to_log('F','DATA','value','dict','data for SSH connect',{'host':self._host,'port':self._port,'username':self._username,'password':self._password})

        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # self.logger.write_to_log('DATA','input','ssh_connect',[self._host,self._port,self._username,self._password,self._timeout])  #怎么记
            # log : SSH_connect [host,port,username,password,timeout]
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
            # 连接成功log记录？
            self.SSHConnection = objSSHClient
        except Exception as e:
            self.logger.write_to_log('F','DATA','debug','exception','ssh connect',str(traceback.format_exc()))
            s.pwe(self.logger,f'  Connect to {self._host} failed with error: {e}')



    def execute_command(self, command, oprt_id):
        # oprt_id = s.get_oprt_id()
        # self.logger.write_to_log('T','OPRT','cmd','ssh',oprt_id,command)
        stdin, stdout, stderr = self.SSHConnection.exec_command(command)
        data = stdout.read()
        if len(data) > 0:
            output = {'sts':1, 'rst':data}
            self.logger.write_to_log('F','DATA','cmd','ssh',oprt_id,output)
            return output

        err = stderr.read()
        if len(err) > 0:
            output = {'sts':0, 'rst':err}
            self.logger.write_to_log('T','INFO','warning','failed','',f'  Command "{command}" execute failed')
            self.logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, output)
            return output
        if data == b'':
            output = {'sts': 1, 'rst': data}
            self.logger.write_to_log('F', 'DATA', 'cmd', 'ssh', oprt_id, output)
            return output




    def close(self):
        self.SSHConnection.close()
        self.logger.write_to_log('T','INFO', 'info', 'finish','','Close SSH connection')


class ConnTelnet(object):
    '''
    telnet connect to NetApp 
    '''

    def __init__(self, host, port, username, password, timeout,logger):
        self.logger = logger
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self.telnet = telnetlib.Telnet()
        self._connect()

    def _connect(self):
        try:
            self.logger.write_to_log('T','INFO','info','start','','  Start to connect NetApp via telnet')
            self.logger.write_to_log('F', 'DATA', 'value', 'dict', 'data for telnet connect',
                                     {'host': self._host, 'port': self._port, 'username': self._username,
                                      'password': self._password})
            self.telnet.open(self._host, self._port)
            self.telnet.read_until(b'Username:', timeout=1)
            self.telnet.write(self._username.encode() + b'\n')
            self.telnet.read_until(b'Password:', timeout=1)
            self.telnet.write(self._password.encode() + b'\n')

        except Exception as e:
            self.logger.write_to_log('INFO', 'error', '', (str(traceback.format_exc())))
            s.pwe(self.logger,f'  Connect to {self._host} failed with error: {e}')

    # 定义exctCMD函数,用于执行命令
    def execute_command(self, cmd):
        oprt_id = s.get_oprt_id()
        self.logger.write_to_log('T','OPRT','cmd','telnet',oprt_id,cmd)

        # self.logger.write_to_log('DATA','input','cmd',cmd.encode().strip() + b'\r')
        # [time],[transaction_id],[s],[OPRT],[cmd],[telnet],[oprt_id],[lc_cmd]
        self.telnet.write(cmd.encode().strip() + b'\r')
        # 命令的结果的记录？
        # self.logger.write_to_log('Telnet','telnet_ex_cmd','','time_sleep:0.25')
        time.sleep(0.25)
        rely = self.telnet.read_very_eager().decode()# ?
        # [time],[transaction_id],[s],[DATA],[cmd],[telnet],[oprt_id],[telnet_output]
        # self.logger.write_to_log('Telnet',)

    def close(self):
        self.telnet.close()
        self.logger.write_to_log('INFO', 'info', '', 'Close Telnet connection.')

if __name__ == '__main__':
# telnet
    host='10.203.1.231'
    port='22'
    username='root'
    password='Feixi@123'
    timeout=5
    ssh=ConnSSH(host, port, username, password, timeout)
    strout=ssh.execute_command('?')
    w = strout.decode('utf-8')
    print(type(w))
    print(w.split('\n'))
    pprint.pprint(w)
    time.sleep(2)
    strout=ssh.execute_command('lun show -m')
    pprint.pprint(strout)


    # telnet
    # host='10.203.1.231'
    # Port='23'
    # username='root'
    # password='Feixi@123'
    # timeout=10

    pass
