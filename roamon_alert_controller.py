# encoding: UTF-8

# 引数の処理はここを参考にした：https://qiita.com/oohira/items/308bbd33a77200a35a3d

import argparse
import roamon_alert_watcher
import roamon_alert_daemon
import os
import logging
from pyfiglet import Figlet

# ログ関係の設定 (適当)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ファイルの保存先
dir_path_data = "/var/tmp"
file_path_contact_list = os.path.join(dir_path_data, "contact_list.json")
# file_path_vrps = os.path.join(dir_path_data, "asnip_vrps.dat")
# file_path_rib = os.path.join(dir_path_data, "asnip.dat")

# ロゴの描画
f = Figlet(font='slant')
print(f.renderText('roamon-alert'))


# getサブコマンドの実際の処理を記述するコールバック関数
def command_add(args):
    pass


# 検証サブコマンド　checkのとき呼ばれる関数
def command_list(args):
    pass


def command_daemon(args):
    alertd = roamon_alert_daemon.RoamonAlertDaemon("/var/run/alertd.pid")
    alertd.init("/tmp/alertd.log", "/var/tmp", "/var/tmp/vrps.dat", "/var/tmp/rib.dat", "/var/tmp/contact_list.json")
    alertd.start()

    # watcher.start_daemon(file_path_contact_list, dir_path_data)


def command_help(args):
    print(parser.parse_args([args.command, '--help']))
    # TODO: ヘルプをうまくやる


# コマンドラインパーサーを作成
parser = argparse.ArgumentParser(description='ROA - BGP Diff command !')
subparsers = parser.add_subparsers()

# get コマンドの parser を作成
parser_add = subparsers.add_parser('add', help="see `get -h`. It's command to add contact info." )
parser_add.add_argument('--asn', action='store_true', help='specify watch ASN')
parser_add.add_argument('--type', default="mail", help='specify contact type')
parser_add.add_argument('--dest', default="DUMMY_DEST", help='specify contact dest, such as e-mail address or Slack info')
# parser_add.add_argument('-p', '--path', default="/tmp", help='specify data dirctory')
parser_add.set_defaults(handler=command_add)

# list コマンドの parser を作成
parser_list = subparsers.add_parser('list', help="see `get -h`. It's command to list up contact info.")
parser_list.set_defaults(handler=command_list)

parser_list = subparsers.add_parser('daemon', help="see `get -h`. It's command to control daemon.")
parser_list.set_defaults(handler=command_daemon)

# help コマンドの parser を作成
parser_help = subparsers.add_parser('help', help='see `help -h`')
parser_help.add_argument('command', help='command name which help is shown')
parser_help.set_defaults(handler=command_help)

# コマンドライン引数をパースして対応するハンドラ関数を実行
args = parser.parse_args()
if hasattr(args, 'handler'):
    args.handler(args)
else:
    # 未知のサブコマンドの場合はヘルプを表示
    parser.print_help()
