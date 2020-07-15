#  coding: utf-8
import sundry
import consts
import logdb

import sys
import re
import time
import os
import getpass
import traceback
import socket
from random import shuffle


def pwe(logger, print_str):
    """
    print, write to log and exit.
    :param logger: Logger object for logging
    :param print_str: Strings to be printed and recorded
    """
    print(print_str)
    logger.write_to_log('T', 'INFO', 'error', 'exit', '', print_str)
    sys.exit()


def get_disk_dev(lun_id, re_string, lsscsi_result, dev_label, logger):
    '''
    Use re to get the blk_dev_name through lun_id
    '''
    # print(lsscsi_result)
    # self.logger.write_to_log('GetDiskPath','host','find_device',self.logger.host)
    re_find_path_via_id = re.compile(re_string)
    # self.logger.write_to_log('GetDiskPath','regular_before','find_device',lsscsi_result)
    re_result = re_find_path_via_id.findall(lsscsi_result)
    oprt_id = sundry.get_oprt_id()
    logger.write_to_log('T', 'OPRT', 'regular', 'findall', oprt_id, {re_string: lsscsi_result})
    logger.write_to_log('F', 'DATA', 'regular', 'findall', oprt_id, re_result)
    if re_result:
        dict_id_disk = dict(re_result)
        if lun_id in dict_id_disk.keys():
            blk_dev_name = dict_id_disk[lun_id]
            return blk_dev_name
        else:
            print(f'no disk device with SCSI ID {lun_id} found')
            logger.write_to_log('T', 'INFO', 'warning', 'failed', '', f'no disk device with SCSI ID {lun_id} found')

    else:
        print(f'no equal {dev_label} disk device found')
        logger.write_to_log('T', 'INFO', 'warning', 'failed', '', f'no equal {dev_label} disk device found')


def record_exception(func):
    """
    Decorator
    Get exception, throw the exception after recording
    :param func:Command binding function
    """

    def wrapper(self, *args):
        try:
            return func(self, *args)
        except Exception as e:
            self.logger.write_to_log('F', 'DATA', 'debug', 'exception', '', str(traceback.format_exc()))
            raise e

    return wrapper


def get_transaction_id():
    return int(time.time())


def get_oprt_id():
    time_stamp = str(get_transaction_id())
    str_list = list(time_stamp)
    shuffle(str_list)
    return ''.join(str_list)


def get_username():
    return getpass.getuser()


def get_hostname():
    return socket.gethostname()


# Get the path of the program
def get_path():
    return os.getcwd()


def change_pointer(new_id):
    consts.set_value('ID', new_id)


if __name__ == 'main':
    get_disk_dev()
