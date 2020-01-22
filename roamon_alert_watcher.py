# encoding: UTF-8

import json
from roamon_diff import roamon_diff_checker
from roamon_diff import roamon_diff_getter
import os
import logging
import roamon_alert_slack
import roamon_alert_mail

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


    def init(self):
        logger.debug("watche　initiated.")
        # ファイルがない場合は話にならんので作る
        if not os.path.exists(self.vrps_file_path):
            self.fetch_vrps_data()
        if not os.path.exists(self.rib_file_path):
            self.fetch_rib_data()
        # 連絡先リストが存在しない場合、適当に作ってセーブ
        if not os.path.exists(self.contact_list_file_path):
            logger.debug("contact_list file is not exist! dummy contact info is created.")
            self.contact_list = [ self.make_contact_info_entry(asn=1899, contact_type="email", contact_info="example1899@example.com") ]
            self.save_contact_list()

        self.load_all_data()


    # よく知らないがプログラム終了時に未開放のオブジェクトのデストラクタが呼ばれることは期待できない？
    def __del__(self):
        if self.contact_list is not None and (self.contact_list) > 0:
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

    def print_conatct_lists(self):
        for contact_info in self.contact_list:
            for key, item in contact_info.items():
                print(item, end="\t")
            print("")

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

    # TODO: delete関数の実装
    def del_contact_info_from_list(s):
        pass

    # TODO: IP Prefix　watchへの対応
    def check_roa_with_all_watched_asn(self):
        logger.debug("start checking")
        watched_asn_list = [contact["asn"] for contact in self.contact_list]
        logger.debug("watched asn list {}".format(watched_asn_list))
        is_valid_list = roamon_diff_checker.check_specified_asns(self.vrps_data, self.rib_data, watched_asn_list)
        logger.debug("checked list {}".format(is_valid_list))
        logger.debug("fin checking, start sending msg...")
        # with open("/var/tmp/temp_mail.log", "w") as f:

        # ローカルで動かすSMTPサーバ、docker-mailhog用の設定。本来はSTMPサーバの設定を入れる
        mailer = roamon_alert_mail.MailSender("localhost", 1025)

        for contact_info in self.contact_list:
            c_asn = int(contact_info["asn"])
            if not is_valid_list[c_asn]:
                if contact_info["type"] == "email":
                    # TODO: メール送信を実装
                    logger.debug("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
                    mailer.send_mail("example_jpnic@example.com", contact_info["contact_info"], "ROA ERRROR!", "ROA ERROR AT ASN{}".format(contact_info["asn"]))
                        #f.writelines("SEND MAIL TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
                elif contact_info["type"] == "slack":
                    # TODO: Slack送信を実装
                    logger.debug("SEND SLACK MSG TO {} watching ASN: {}".format(contact_info["contact_info"], contact_info["asn"]))
                    roamon_alert_slack.send_slack("ROA ERROR AT ASN{}".format(contact_info["asn"], contact_info["contact_info"] ))
        logger.debug("fin sending msg.")


