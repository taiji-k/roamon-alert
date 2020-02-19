# encoding: UTF-8

# Copyright (c) 2019-2020 Japan Network Information Center ("JPNIC")
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute and/or sublicense of
# the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
from roamon_verify import roamon_verify_checker
from roamon_verify import roamon_verify_getter
import os
import logging
import roamon_alert_slack

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RoamonAlertWatcher():
    def __init__(self, work_dir_path, vrps_file_path, rib_file_path, mailer, db_controller):
        self.work_dir_path = work_dir_path
        self.vrps_file_path = vrps_file_path
        self.rib_file_path = rib_file_path

        self.mailer = mailer
        self.db_controller = db_controller

        self.vrps_data = None
        self.rib_data = None

        self.init()

    def init(self):
        # このインスタンスが破棄されるときにDBとの接続を自動で破棄したかったが...
        # 別スレッドで動くデーモンに渡したりしたせいか、psycopg2が `could not receive data from server: Bad file descriptor`
        # とかいうエラーときどきだすのでやめていちいち明示的に切ることにした
        # atexit.register(self.db_controller.disconnect)

        logger.debug("watche　initiated.")
        # ファイルがない作る
        if not os.path.exists(self.vrps_file_path):
            self.fetch_vrps_data()
        if not os.path.exists(self.rib_file_path):
            self.fetch_rib_data()

        # DBにテーブルを作成しておく
        self.db_controller.connect()
        self.db_controller.init_table()
        # 連絡先リストが存在しない場合にそなえて、適当にダミーの連絡先を作る
        # TODO: これはデバッグ用。ダミーの連絡先が邪魔になるので本番では消すべき
        self.add_contact_info_to_list("email", "example1899@example.com", None, [1899])
        self.add_contact_info_to_list("email", "example137@example.com", ["147.162.0.0/15"], [137])
        self.add_contact_info_to_list("email", "example327687@example.com", ["192.168.30.0/24"], [327687])
        self.add_contact_info_to_list("slack",
                                      "https://hooks.slack.com/services/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",
                                      ["192.168.30.0/24", "147.162.0.0/15"], [201354, 137])
        self.db_controller.disconnect()

        self.load_all_data()

    def fetch_rib_data(self):
        roamon_verify_getter.fetch_rib_data(self.work_dir_path, self.rib_file_path)

    def fetch_vrps_data(self):
        roamon_verify_getter.fetch_vrps_data(self.vrps_file_path)

    def load_all_data(self):
        loaded_db = roamon_verify_checker.load_all_data(self.vrps_file_path, self.rib_file_path)
        self.vrps_data = loaded_db["vrps"]
        self.rib_data = loaded_db["rib"]

    def print_contact_lists(self):
        # いちいちDB接続 & 切断をしてるのはカッコわるいが、クラス作成時にDB接続して破棄時にDB切断だとうまくいかない
        # psycopg2が `could not receive data from server: Bad file descriptor`とかエラー出す。たぶんデーモン起動時に別スレッドに渡したりするせい？
        # だからいちいちDB接続 & 切断をしてる。
        self.db_controller.connect()
        #print(json.dumps(self.db_controller.get_all_contact_info_as_old_style(), indent=4))
        for row in self.db_controller.get_all_contact_info_as_old_style():
            for col in row:
                print(col, end="\t")
            print("")
        self.db_controller.disconnect()

    def add_contact_info_to_list(self, contact_type, contact_info, prefixes, asns):
        self.db_controller.connect()
        self.db_controller.write_contact_info(contact_type, contact_info, prefixes, asns)
        self.db_controller.disconnect()

    def delete_contact_info_from_list(self, contact_type, contact_info, prefixes, asns):
        self.db_controller.connect()
        self.db_controller.write_contact_info(contact_type, contact_info, prefixes, asns)
        self.db_controller.disconnect()

    # ROVして、監視対象のprefixやASNに異常あったなら連絡する関数
    def check_roa_with_all_watched_asn(self):
        logger.debug("start checking")

        # watchしてるprefixについてROVする
        prefix_rov_result_struct_dict = roamon_verify_checker.check_specified_prefixes(self.vrps_data, self.rib_data,
                                                                                       ["192.168.30.0/24",
                                                                                        "147.162.0.0/15"])

        # TODO: こちら(監視対象だけでなく全てのprefixをROVする)に切り替える
        # 全てのprefixについてROVする
        # prefix_rov_result_struct_dict = roamon_verify_checker.check_all_prefixes_in_vrps(self.vrps_data, self.rib_data)

        logger.debug("fin ROV ...")
        logger.debug("start writing ROV results to DB...")

        # ROVの結果をDBに書き込む
        self.db_controller.connect()
        # TODO: データ取得時間は、データを本当に取得した時刻にセットすべき(まぁこれでもいいけど)
        import datetime
        data_fetched_time = datetime.datetime.now()  # これはデータ取得時にセットすべき
        try:
            self.db_controller.write_prefix_rov_result_structs(prefix_rov_result_struct_dict.values(),
                                                               data_fetched_time)
        except:
            import traceback
            traceback.print_exc()

        # DBの内容をデバッグのために出力する
        logger.debug(" ---DB output--- START")
        logger.debug("{}".format(self.db_controller.pickup_rov_failed_contact_info_about_watched_prefix()))
        logger.debug(("{}".format(self.db_controller.pickup_rov_failed_contact_info_about_watched_asn())))
        logger.debug(" ---DB output--- FIN")

        logger.debug("fin checking, start sending msg...")

        # 異常検知メッセージを送信してくれる関数
        #  contact_type: 連絡先タイプ, emailとかslackとか
        #  contact_dest: 連絡先。メールアドレスやslack webhook
        #  rov_result_dict: ROVの結果
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
                    "ROA ERROR \n{}".format(
                        json.dumps(rov_result_dict, sort_keys=True, indent=4, default=support_json_default)))

            # slack送信
            elif contact_type == "slack":
                logger.debug(
                    "SEND SLACK MSG TO {} watching object:".format(contact_dest))
                roamon_alert_slack.send_slack("ROA ERROR \n{}".format(json.dumps(rov_result_dict,
                                                                                 sort_keys=True, indent=4,
                                                                                 default=support_json_default)))

        # watched_prefixについて、ROVの結果がVALIDじゃなかったものを調べて連絡先に通知する
        logger.debug("start sending msg about wtached prefix...")
        rov_failed_entry_having_watched_prefix = self.db_controller.pickup_rov_failed_contact_info_about_watched_prefix()
        logger.debug("SQL result : {}".format(rov_failed_entry_having_watched_prefix))
        for contact_info, rov_info in rov_failed_entry_having_watched_prefix.items():
            send_alert(contact_info[0], contact_info[1], rov_info)

        # watched_asnについて、ROVの結果がVALIDじゃなかったものを調べて連絡先に通知する
        logger.debug("start sending msg about wtached asn...")
        rov_failed_entry_having_watched_asn = self.db_controller.pickup_rov_failed_contact_info_about_watched_asn()
        for contact_info, rov_info in rov_failed_entry_having_watched_asn.items():
            logger.debug("sending {} {} {}...".format(contact_info[0], contact_info[1], rov_info))
            send_alert(contact_info[0], contact_info[1], rov_info)

        logger.debug("fin sending msg.")
        self.db_controller.disconnect()

