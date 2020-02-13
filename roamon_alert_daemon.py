# encoding: UTF-8

import json
from roamon_verify import roamon_verify_checker
from roamon_verify import roamon_verify_getter
import roamon_alert_watcher
import os
import signal
import daemon
import daemon.pidfile
import sys
import logging
import time
from datetime import datetime, timedelta


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RoamonAlertDaemon():
    def __init__(self, file_path_pid_lockfile, log_path, checker, watch_interval):
        self.path_pid_lockfile = file_path_pid_lockfile
        self.log_file_path = log_path
        self.checker = checker
        self.watch_interval = watch_interval # 分指定

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
        # interval_min_fetch_rib = self.watch_interval
        # interval_min_fetch_vrps = self.watch_interval
        # interval_min_check_roa_with_wtached_asn = self.watch_interval

        while 1:
            logger.debug("start loop")
            # TODO: やっつけ実装なので、一定間隔でこれらを実行するいい案を考える (非同期にするとそれはそれで面倒で、ダウンロード中や処理中のファイルを開こうとするときはやめてリトライとかする必要がありそう。でもそうすべきかなー)


            # # BGP経路情報とVRPのフェッチ
            self.checker.fetch_rib_data()
            self.checker.fetch_vrps_data()

            # BGP経路情報とVRP,および連絡先情報をロードし直す
            self.checker.load_all_data()
            # 異常がないかチェック
            self.checker.check_roa_with_all_watched_asn()

            logger.debug("end working in loop")

            #　規定時間まつ
            time.sleep(60 * self.watch_interval)
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


    # TODO: デーモン停止時のPIDファイルの始末が正常にできているか確認 & 異常終了時のPIDファイルの始末はどうする？
    def stop(self):
        # PIDファイルがあるかどうか見る
        if not os.path.exists(self.path_pid_lockfile):
            logger.error("PID file for the daemon is not found at {}".format(self.path_pid_lockfile))


        pid = daemon.pidfile.PIDLockFile(self.path_pid_lockfile)
        # 起動中判定はどうやるのか不明
        # if pid.is_locked():

        # デーモンのプロセスを終了させる
        daemon_pid = pid.read_pid()
        logger.debug("killing daemon process with PID:{}...".format(daemon_pid))
        try:
            os.kill(daemon_pid, signal.SIGTERM)
        except ProcessLookupError:
            # プロセスが動いてなかったらここでおしまい
            logger.error("Process PID:{} is not running.".format(daemon_pid))
            return

        # PIDファイルを始末
        logger.debug("releasing daemon process with PID file:{}...".format(self.path_pid_lockfile))
        pid.break_lock()


