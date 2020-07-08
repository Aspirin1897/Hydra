
#  coding: utf-8
import argparse
import sys
import time

import storage
import vplx
import host_initiator
import sundry
import log
import logdb
import consts

class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''

    def __init__(self):
        self.transaction_id = sundry.get_transaction_id()
        self.logger = log.Log(self.transaction_id)
        self.argparse_init()

    def argparse_init(self):
        self.parser = argparse.ArgumentParser(prog='max_lun',
                                              description='Test max lun number of VersaRAID-SDS')
        # self.parser.add_argument(
        #     '-r',
        #     '--run',
        #     action="store_true",
        #     dest="run_test",
        #     help="run auto max lun test")
        self.parser.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming")
        self.parser.add_argument(
            '-id',
            action="store",
            dest="id_range",
            help='ID or ID range(split with ",")')

        sub_parser = self.parser.add_subparsers(dest='replay')
        parser_replay = sub_parser.add_parser(
            'replay',
            aliases=['re'],
            formatter_class=argparse.RawTextHelpFormatter
        )

        parser_replay.add_argument(
            '-t',
            '--transactionid',
            dest='transactionid',
            metavar='',
            help='transaction id')

        parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='date')


    def _vplx_drbd(self):
        '''
        Connect to VersaPLX, Config DRDB resource
        '''
        drbd = vplx.VplxDrbd(self.logger)
        # drbd.discover_new_lun() # 查询新的lun有没有map过来，返回path
        # drbd.prepare_config_file() # 创建配置文件
        drbd.drbd_cfg() # run
        # drbd.drbd_status_verify() # 验证有没有启动（UptoDate）

    def execute(self, id, string):
        self.transaction_id = sundry.get_transaction_id()
        self.logger = log.Log(self.transaction_id)

        print(f'\n======*** Start working for ID {id} ***======')

        #初始化一个全局变量ID
        
        vplx.ID = id
        vplx.STRING = string
        self._vplx_drbd()


    # @sundry.record_exception
    def run(self):
        if sys.argv:
            path = sundry.get_path()
            cmd = ' '.join(sys.argv)
            self.logger.write_to_log('T','DATA','input', 'user_input', '',cmd)
            # [time],[transaction_id],[display],[type_level1],[type_level2],[d1],[d2],[data]
            # [time],[transaction_id],[s],[DATA],[input],[user_input],[cmd],[f{cmd}]

        args = self.parser.parse_args()

        # uniq_str: The unique string for this test, affects related naming
        if args.uniq_str:
            ids = args.id_range.split(',')
            if len(ids) == 1:
                self.execute(int(ids[0]), args.uniq_str)
            elif len(ids) == 2:
                id_start, id_end = int(ids[0]), int(ids[1])
                for i in range(id_start, id_end):
                    self.execute(i, args.uniq_str)
            else:
                self.parser.print_help()

        elif args.replay:
            if args.transactionid:
                db = logdb.LogDB()
                db.get_logdb()
                string_,id_ = db.get_string_id(args.transactionid)[0]

                vplx.replay = 'yes'
                storage.replay = 'yes'
                print(f'\n======*** Start working for ID {id} ***======')

                consts._init()#初始化一个全局变量：ID

                vplx.TID = args.transactionid

                self._storage()

                vplx.ID = id_
                vplx.STRING = string_
                self._vplx_drbd()
                self._vplx_crm()
                time.sleep(1.5)


                self._host_test()
                # self.replay(args)

        else:
            # self.logger.write_to_log('INFO','info','','print_help')
            self.parser.print_help()


if __name__ == '__main__':
    w = HydraArgParse()
    w.run()
