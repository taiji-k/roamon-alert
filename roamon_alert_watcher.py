# encoding: UTF-8

import json
from roamon_verify import roamon_verify_checker
from roamon_verify import roamon_verify_getter
import os
import logging
import roamon_alert_slack
import roamon_alert_mail
import atexit
import roamon_alert_db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RoamonAlertWatcher():
    def __init__(self, file_path_contact_list, work_dir_path, vrps_file_path, rib_file_path, mailer, db_controller):

        self.contact_list_file_path = file_path_contact_list
        self.work_dir_path = work_dir_path
        self.vrps_file_path = vrps_file_path
        self.rib_file_path = rib_file_path

        self.mailer = mailer
        self.db_controller = db_controller

        self.contact_list = []
        self.vrps_data = None
        self.rib_data = None

        self.init()

        atexit.register(self.save_contact_list)


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
    # def __del__(self):
    #     if self.contact_list is not None and len(self.contact_list) > 0:
    #         self.save_contact_list()


    # roamon_diffの関数読んでるだけなんでなんとかしたい(roamon_diffをclass化してそっち呼ぶとか？)
    def fetch_rib_data(self):
        roamon_verify_getter.fetch_rib_data(self.work_dir_path, self.rib_file_path)


    def fetch_vrps_data(self):
        roamon_verify_getter.fetch_vrps_data(self.vrps_file_path)


    def load_all_data(self):
        self.load_contact_list()

        loaded_db = roamon_verify_checker.load_all_data(self.vrps_file_path, self.rib_file_path)
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


    def delete_contact_info_from_list(self, asn=None, prefix=None, contact_type=None, contact_info=None):
        target_dict = {"asn": asn, "prefix": prefix, "type": contact_type, "contact_info": contact_info}
        col_names = list(target_dict.keys())

        # 削除すべき連絡先だけを省いてここに連絡先をコピーする
        new_contact_list = []

        for index, record in enumerate(self.contact_list):
            delete_flag = False
            # 列(asnとかprefixとか)の比較
            for col_name in col_names:
                # この関数の引数 (asn, prefix, ...) として渡される条件の指定はどれも任意なので渡されたかどうかを確認する必要がある
                if target_dict[col_name] is not None:
                    # 連絡先情報の特定の列が、指定されたものと一緒ならdeleteフラグをTrueにする
                    if target_dict[col_name] == record[col_name]:
                        delete_flag = True
                    else:
                        # この関数の引数 (asn, prefix, ...) はAND条件を指定している。
                        # 一度deleteフラグが初期状態のFalseからTrueになって、再びFalseになるときは、一つでも条件に合致しなかった列があるということなので、ここで終了
                        if delete_flag:
                            delete_flag = False
                            break

            if delete_flag:
                logger.debug("delete: {}".format(record))
            else:
                # ループの元となってるリストの要素をループ内で削除すると厄介なことになるので避ける
                #  https://dev.classmethod.jp/beginners/python-delete-element-of-list/
                new_contact_list.append(record)

        self.contact_list = new_contact_list


    # 連絡先情報登録時に一緒に入れる、監視対象のASNやPrefixに異常がないかみて、あるなら連絡する関数
    def check_roa_with_all_watched_asn(self):
        # watchされてる全てのASNとprefixをリストアップ
        logger.debug("start checking")
        watched_asn_list = [contact["asn"] for contact in self.contact_list]
        watched_prefix_list = [contact["prefix"] for contact in self.contact_list]


        logger.debug("watched asn list {}".format(watched_asn_list))
        # watchしてるASNについてそれぞれが広告してる全てのprefixをROVする
        asn_rov_result_struct_dict = roamon_verify_checker.check_specified_asns(self.vrps_data, self.rib_data, watched_asn_list)
        # watchしてるprefixについてROVする
        prefix_rov_result_struct_dict = roamon_verify_checker.check_specified_prefixes(self.vrps_data, self.rib_data,
                                                                                watched_prefix_list)

        # -------DEBUG------
        self.db_controller.connect()
        self.db_controller.init_table()
        import datetime
        data_fetched_time = datetime.datetime.now()  # これはデータ取得時にセットすべき
        self.db_controller.write_prefix_rov_result_structs(prefix_rov_result_struct_dict.values(), data_fetched_time)

        self.db_controller.write_contact_info("slack", "https://hooks.slack.com/services/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", ["192.168.30.0/24", "147.162.0.0/15"], [201354,137])
        print("-----HOGEHOGOE1-----")
        print(self.db_controller.pickup_rov_failed_contact_info_about_watched_prefix())
        print(self.db_controller.pickup_rov_failed_contact_info_about_watched_asn())
        print("-----HOGEHOGOE2-----")

        # ----^^^DEBUG^^^---

        logger.debug("checked list {}".format(asn_rov_result_struct_dict))
        logger.debug("fin checking, start sending msg...")


        # 異常検知メッセージを送信してくれる関数
        #  contact_info: 連絡先情報
        #  error_at    : エラーがでたASN or prefix
        #  rov_result  : ROVの結果
        def send_alert(contact_type, contact_dest, rov_result_dict):
            # JSON serializableでない列挙型をjson.dump可能にする関数。json.dumpの引数、"default"に渡す
            def support_json_default(o):
                if isinstance(o, roamon_verify_checker.RovResult):
                    return o.text
                if isinstance(o, datetime.datetime):
                    return o.__str__()
                raise TypeError(repr(o) + " is not JSON serializable")

            # メール送信
            if contact_type == "email":
                logger.debug(
                    "SEND MAIL TO {} watching object:".format(contact_dest))
                self.mailer.send_mail(
                                 contact_dest,
                                 "ROA ERRROR!",
                                 "ROA ERROR \n{}".format(json.dumps(rov_result_dict, sort_keys=True, indent=4, default=support_json_default)))
            # slack送信
            elif contact_type == "slack":
                logger.debug(
                    "SEND SLACK MSG TO {} watching object:".format(contact_dest))
                roamon_alert_slack.send_slack("ROA ERROR \n{}".format(json.dumps(rov_result_dict,
                                                                                         sort_keys=True, indent=4, default=support_json_default)))

        logger.debug("start sending msg about wtached prefix...")
        rov_failed_entry_having_watched_prefix = self.db_controller.pickup_rov_failed_contact_info_about_watched_prefix()
        logger.debug("SQL result : {}".format(rov_failed_entry_having_watched_prefix))
        for contact_info, rov_info in rov_failed_entry_having_watched_prefix.items():
            send_alert(contact_info[0], contact_info[1], rov_info)

        logger.debug("start sending msg about wtached asn...")
        rov_failed_entry_having_watched_asn = self.db_controller.pickup_rov_failed_contact_info_about_watched_asn()
        for contact_info, rov_info in rov_failed_entry_having_watched_asn.items():
            logger.debug("sending {} {} {}...".format(contact_info[0], contact_info[1],  rov_info))
            send_alert(contact_info[0], contact_info[1], rov_info)

        logger.debug("fin sending msg.")

        self.db_controller.disconnect()