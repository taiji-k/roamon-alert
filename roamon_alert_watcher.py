# encoding: UTF-8

import daemonize
import json
from roamon_diff import roamon_diff_checker
from roamon_diff import roamon_diff_getter
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RoamonAlertWatcher():
    def __init__(self, file_path_contact_list, work_dir_path, vrps_file_path, rib_file_path):

        self.contact_list_file_path = file_path_contact_list
        self.work_dir_path = work_dir_path
        self.vrps_file_path = vrps_file_path
        self.rib_file_path = rib_file_path

        self.contact_list = []
        self.vrps_data = None
        self.rib_data = None


    # よく知らないがプログラム終了時に未開放のオブジェクトのデストラクタが呼ばれることは期待できない？
    def __del__(self):
        if len(self.contact_list) > 0:
            self.save_contact_list()

    # roamon_diffの関数読んでるだけなんでなんとかしたい(roamon_diffをclass化してそっち呼ぶとか？)
    def fetch_rib_data(self):
        roamon_diff_getter.fetch_rib_data(self.work_dir_path, self.rib_file_path)


    def fetch_vrps_data(self):
        roamon_diff_getter.fetch_vrps_data(self.vrps_file_path)


    def load_all_data(self):
        self.load_contact_list()

        loaded_db = roamon_diff_checker.load_all_data(self.vrps_file_path, self.rib_file_path)
        self.vrps_data = loaded_db["vrps"]
        self.rib_data = loaded_db["rib"]



    @classmethod
    def make_contact_info_entry(cls, asn = -1, prefix = "0.0.0.0/0", contact_type = "Default", contact_info = "Default"):
        return {"asn": asn, "prefix": prefix, "type": contact_type, "contact_info": contact_info}


    def load_contact_list(self):
        with open(self.contact_list_file_path, "r") as f:
            self.contact_list = json.load(f)

        logger.debug("loaded contact list {} from {}".format(self.contact_list, self.contact_list_file_path))

    def save_contact_list(self):
        with open(self.contact_list_file_path, "w") as f:
            json.dump(self.contact_list, f)


    def add_contact_info_to_list(self, asn = -1, prefix = "0.0.0.0/0", contact_type = "Default", contact_info = "Default"):
        # TODO: 同じ内容のやつがいくらでも入っちゃうので注意。監視対象(AS & Prefix)と連絡先(contact_info)を元にしたIDを割り振ることで対処する？
        self.contact_list.append(self.make_contact_info_entry(asn, prefix, contact_type, contact_info))
        return

    # TODO: IP Prefix　watchへの対応
    def check_roa_with_all_watched_asn(self):
        logger.debug("start checking")
        watched_asn_list = [contact["asn"] for contact in self.contact_list]
        logger.debug("watched asn list {}".format(watched_asn_list))
        is_valid_list = roamon_diff_checker.check_specified_asns(self.vrps_data, self.rib_data, watched_asn_list)
        logger.debug("checked list {}".format(is_valid_list))
        logger.debug("fin checking, start sending msg...")
        # with open("/var/tmp/temp_mail.log", "w") as f:

        for contact_info in self.contact_list:
            c_asn = int(contact_info["asn"])
            if not is_valid_list[c_asn]:
                if contact_info["type"] == "email":
                    # TODO: メール送信を実装
                    logger.debug("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
                        #f.writelines("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
                elif contact_info["type"] == "slack":
                    # TODO: Slack送信を実装
                    logger.debug("SEND SLACK MSG TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
        logger.debug("fin sending msg.")
    #
    # def start_daemon(self, contact_list,  work_dir_path):
    #     rib_file_path = os.path.join(work_dir_path, "rib.dat")
    #     vrps_file_path = os.path.join(work_dir_path, "vrps.dat")
    #
    #     # ここで全データをフェッチする(もしくはdaemon initされたときにフェッチ)
    #     if not os.path.exists(rib_file_path):
    #         roamon_diff_getter.fetch_rib_data(work_dir_path, rib_file_path)
    #     if not os.path.exists(vrps_file_path):
    #         roamon_diff_getter.fetch_vrps_data(vrps_file_path)
    #
    #     # RIBファイル(BGPの)を一定間隔でダウンロードするデーモン起動
    #     @daemonize.interval_run(60)
    #     def fetch_rib(work_dir_path, rib_file_path, kws=None):
    #         print("start daemon to fetch rib")
    #         roamon_diff_getter.fetch_rib_data(work_dir_path, rib_file_path )
    #     daemonize.start_daemon(fetch_rib, work_dir_path, rib_file_path, pidpath='/var/run/fetch_rib.pid', logpath='/var/tmp/fetch_rib.log', kws='keyword')
    #     #
    #     VRPsファイルを一定間隔でダウンロードするデーモン起動
    #
    #     @daemonize.interval_run(60)
    #     def fetch_vrps(vrps_file_path, kws=None):
    #         print("start daemon to fetch vrps")
    #         roamon_diff_getter.fetch_vrps_data(vrps_file_path)
    #     daemonize.start_daemon(fetch_vrps, vrps_file_path, pidpath='/var/run/fetch_vrps.pid', logpath='/var/tmp/fetch_vrps.log',
    #                            kws='keyword')
    #
    #     # ダウンロードしたファイルをチェックして通知を送るデーモン起動
    #     @daemonize.do_interval_run(10)
    #     def check_all_roa(contact_list, vrps_file_path, rib_file_path, kws=None):
    #         print("start daemon to check ROA and RIB")
    #         loaded_data = roamon_diff_checker.load_all_data(vrps_file_path, rib_file_path)
    #         is_valid_list = roamon_diff_checker.check_all_asn_in_vrps(loaded_data["vrps"], loaded_data["rib"])
    #
    #         # with open("/var/tmp/temp_mail.log", "w") as f:
    #         # TODO: IP Prefix　watchへの対応 (けど、IP Prefixだけでwatchって需要ある？ASのBGPオペレータへの通知が主な目的なんだから、ASごとでも十分では ?)
    #         for contact_info in self.contact_list:
    #             c_asn = int(contact_info["asn"])
    #             if c_asn in is_valid_list and not is_valid_list[c_asn]:
    #                 if contact_info["type"] == "email":
    #                     # TODO: メール送信を実装
    #                     print("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"],
    #                                                                     contact_info["asn"]))
    #                     # f.writelines("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
    #     daemonize.start_daemon(check_all_roa, self.contact_list, vrps_file_path, rib_file_path, pidpath='/var/run/check_all_roa.pid', logpath='/var/tmp/check_all_roa.log', kws='keyword')
    #
    #
    #
    #
    #     # ここでVRPsを一定時間ごとにfetchして検証するデーモンを起動？
    #     # ここでBGPを一定時間(2時間)ごとにfetchするデーモンを起動？
    #     # ここで一定時間ごとにデータをチェックするデーモンを起動？
    #
    #
    # #
    # # def check_all_roa(self):
    #
    #
    # # TODO: delete関数の実装
    #
    # def del_contact_info_from_list(self):
    #     pass
