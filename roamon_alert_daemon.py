# encoding: UTF-8

import json
from roamon_diff import roamon_diff_checker
from roamon_diff import roamon_diff_getter
import roamon_alert_watcher
import os
import signal
import daemon
import sys
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RoamonAlertDaemon():
    def __init__(self, file_path_pid_lockfile, log_path, checker):
        self.path_pid_lockfile = file_path_pid_lockfile
        self.log_file_path = log_path
        self.checker = checker

        # self.work_dir_path = ""
        # self.vrps_file_path = ""
        # self.rib_file_path = ""
        # self.contact_list_file_path = ""




    # def init(self):
    #     # ファイルのフェッチ
    #     #(これはdebug用のif文)
    #     # if not os.path.exists(self.vrps_file_path):
    #     #     self.checker.fetch_vrps_data()
    #     # if not os.path.exists(self.rib_file_path):
    #     #     self.checker.fetch_rib_data()
    #
    #     # ロード
    #     self.checker.load_all_data()


    @classmethod
    def __start_daemon_with_func(cls, func, *args, logpath, pidpath, **kws):
        logger.debug("DAEMON_INVOKER: invoke daemon")
        # [ここ](https://qiita.com/KosukeJin/items/e626ddda850aa8407cee)からコピペ気味
        # 多重起動防止
        if pidpath:
            pid = daemon.pidfile.PIDLockFile(pidpath)
            logger.debug("DAEMON_INVOKER: pid: {}".format(pid))
            if pid.is_locked():
                raise Exception('Process is already started.')

        # PID指定がなければフォアグラウンド
        else:
            pid = None
        # ログ
        if logpath:
            std_out = open(logpath, mode='a+', encoding='utf-8')
            std_err = std_out

        # 指定がなければ標準出力
        else:
            std_out = sys.stdout
            std_err = sys.stderr

        dc = daemon.DaemonContext(
            umask=0o002,

            pidfile=pid,
            stdout=std_out,
            stderr=std_err,
        )

        # 内部で実行される
        def forever():
            # while 1は実行失敗時にまた行うためのもの(渡されるfuncは中でループするので基本的にこっちではループしないはず)
            while 1:
                try:
                    func(*args, **kws)

                # kill -SIGTERM {pid} で停止する
                except SystemExit as e:
                    print('Killed by SIGTERM.')
                    raise

                # それ以外のエラーは無視して動き続ける
                except Exception as e:
                    print('Uncaught exception was raised, but process continue.', e)

        with dc:
            forever()


    def main_loop(self, kws=None):
        logger.debug("enter main_loop")
        interval_min_fetch_rib = 60
        interval_min_fetch_vrps = 60
        interval_min_check_roa_with_wtached_asn = 10

        while 1:
            logger.debug("start loop")
            # TODO: いい感じの間隔でデータのfetchとロード、チェックをするようにする

            self.checker.load_all_data()
            self.checker.check_roa_with_all_watched_asn()
            logger.debug("end working in loop")
            time.sleep(300)
            logger.debug("end loop")

            # # 現在時刻と次回起動時刻
            # t = datetime.now().replace(second=0, microsecond=0)
            # next_up_time_fetch_rib  = t + timedelta(minutes=interval_min_fetch_rib)
            # next_up_time_fetch_vrps = t + timedelta(minutes=interval_min_fetch_vrps)
            # next_up_time_check_roa_with_wtached_asn = t + timedelta(minutes=interval_min_check_roa_with_wtached_asn)
            #
            # # intervalの倍数ジャストに起動 (非同期でやらないのは、書き込み中のファイルを読み込んだりしないように)
            # if t.minute % interval_min_fetch_rib == 0:
            #     self.checker.fetch_rib_data()
            # # 1周目 次回実行時間まで調整
            # else:
            #     stop = stop = interval_min_fetch_rib - t.minute % interval_min_fetch_rib
            #     n = t + timedelta(minutes=stop)
            #
            # if t.minute % interval_min_fetch_vrps == 0:
            #     self.checker.fetch_vrps_data()
            #
            # if t.minute % interval_min_check_roa_with_wtached_asn == 0:
            #     self.checker.check_roa_with_all_watched_asn()
            #
            #
            #
            # w = (n - datetime.now()).total_seconds()
            # log_to_stdout('[INFO]', 'Sleep', w, 'seconds.')
            # time.sleep(w)


    def start(self):
        logger.debug("call start daemon!")
        self.__start_daemon_with_func(self.main_loop, logpath=self.log_file_path, pidpath=self.path_pid_lockfile, kws=None)


    def stop(self):
        pid = daemon.pidfile.PIDLockFile(self.path_pid_lockfile)
        # 起動中?なら
        if pid.is_locked():
            os.kill(pid.pid, signal.SIGKILL)




