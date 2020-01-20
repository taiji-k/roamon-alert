# encoding: UTF-8

import daemonize
import json
from roamon_diff import roamon_diff_checker
from roamon_diff import roamon_diff_getter
import os

class RoamonAlertWatcher():
    def __init__(self, file_path_contact_list):
        self.contact_list = []
        self.load_contact_list(file_path_contact_list)


    def make_contact_info_entry(self, asn = -1, prefix = "0.0.0.0/0", contact_type = "Default", contact_info = "Default"):
        return {"asn": asn, "prefix": prefix, "type": contact_type, "contact_info": contact_info}


    def load_contact_list(self, file_path_contact_list):
        with open(file_path_contact_list, "r") as f:
            self.contact_list = json.load(f)


    def save_contact_list(self, file_path_contact_list):
        with open(file_path_contact_list, "w") as f:
            json.dump(self.contact_list, f)


    def add_contact_info_to_list(self, asn = -1, prefix = "0.0.0.0/0", contact_type = "Default", contact_info = "Default"):
        # TODO: 同じ内容のやつがいくらでも入っちゃうので注意。監視対象(AS & Prefix)と連絡先(contact_info)を元にしたIDを割り振ることで対処する？
        self.contact_list.append(self.make_contact_info_entry(asn, prefix, contact_type, contact_info))
        return

    # def check_all_roa_test(self, vrps_file_path, rib_file_path):
    #     print("start daemon to check ROA and RIB")
    #     loaded_data = roamon_diff_checker.load_all_data(vrps_file_path, rib_file_path)
    #     is_valid_list = roamon_diff_checker.check_all_asn_in_vrps(loaded_data["vrps"], loaded_data["rib"])
    #
    #     # with open("/var/tmp/temp_mail.log", "w") as f:
    #     # TODO: IP Prefix　watchへの対応 (けど、IP Prefixだけでwatchって需要ある？ASのBGPオペレータへの通知が主な目的なんだから、ASごとでも十分では ?)
    #     for contact_info in self.contact_list:
    #         c_asn = int(contact_info["asn"])
    #         if c_asn in is_valid_list and  not is_valid_list[c_asn]:
    #             if contact_info["type"] == "email":
    #                 # TODO: メール送信を実装
    #                 print("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
    #                     #f.writelines("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))

    def start_daemon(self, contact_list,  work_dir_path):
        rib_file_path = os.path.join(work_dir_path, "rib.dat")
        vrps_file_path = os.path.join(work_dir_path, "vrps.dat")

        # ここで全データをフェッチする(もしくはdaemon initされたときにフェッチ)
        if not os.path.exists(rib_file_path):
            roamon_diff_getter.fetch_rib_data(work_dir_path, rib_file_path)
        if not os.path.exists(vrps_file_path):
            roamon_diff_getter.fetch_vrps_data(vrps_file_path)

        # # RIBファイル(BGPの)を一定間隔でダウンロードするデーモン起動
        # @daemonize.interval_run(60)
        # def fetch_rib(work_dir_path, rib_file_path, kws=None):
        #     print("start daemon to fetch rib")
        #     roamon_diff_getter.fetch_rib_data(work_dir_path, rib_file_path )
        # daemonize.start_daemon(fetch_rib, work_dir_path, rib_file_path, pidpath='/var/tmp/proc/fetch_rib', logpath='/var/tmp/fetch_rib.log', kws='keyword')
        #
        # # VRPsファイルを一定間隔でダウンロードするデーモン起動
        # @daemonize.interval_run(60)
        # def fetch_vrps(vrps_file_path, kws=None):
        #     print("start daemon to fetch vrps")
        #     roamon_diff_getter.fetch_vrps_data(vrps_file_path)
        # daemonize.start_daemon(fetch_vrps, vrps_file_path, pidpath='/var/tmp/proc/fetch_vrps', logpath='/var/tmp/fetch_vrps.log',
        #                        kws='keyword')

        # ダウンロードしたファイルをチェックして通知を送るデーモン起動
        @daemonize.interval_run(10)
        def check_all_roa(contact_list, vrps_file_path, rib_file_path, kws=None):
            print("start daemon to check ROA and RIB")
            loaded_data = roamon_diff_checker.load_all_data(vrps_file_path, rib_file_path)
            is_valid_list = roamon_diff_checker.check_all_asn_in_vrps(loaded_data["vrps"], loaded_data["rib"])

            # with open("/var/tmp/temp_mail.log", "w") as f:
            # TODO: IP Prefix　watchへの対応 (けど、IP Prefixだけでwatchって需要ある？ASのBGPオペレータへの通知が主な目的なんだから、ASごとでも十分では ?)
            for contact_info in self.contact_list:
                c_asn = int(contact_info["asn"])
                if c_asn in is_valid_list and not is_valid_list[c_asn]:
                    if contact_info["type"] == "email":
                        # TODO: メール送信を実装
                        print("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"],
                                                                        contact_info["asn"]))
                        # f.writelines("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
        daemonize.start_daemon(check_all_roa, self.contact_list, vrps_file_path, rib_file_path, pidpath='/var/tmp/proc/check_all_roa', logpath='/var/tmp/check_all_roa.log', kws='keyword')




        # ここでVRPsを一定時間ごとにfetchして検証するデーモンを起動？
        # ここでBGPを一定時間(2時間)ごとにfetchするデーモンを起動？
        # ここで一定時間ごとにデータをチェックするデーモンを起動？


    #
    # def check_all_roa(self):


    # TODO: delete関数の実装

    def del_contact_info_from_list(self):
        pass
