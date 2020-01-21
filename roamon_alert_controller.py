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
file_path_vrps = os.path.join(dir_path_data, "vrps.dat")
file_path_rib = os.path.join(dir_path_data, "rib.dat")
log_path = "/tmp/alertd.log"

pid_file_path = "/var/run/alertd.pid"

# ロゴの描画
f = Figlet(font='slant')
print(f.renderText('roamon-alert'))

checker = roamon_alert_watcher.RoamonAlertWatcher(file_path_contact_list, dir_path_data, file_path_vrps, file_path_rib)
checker.init()

# getサブコマンドの実際の処理を記述するコールバック関数
def command_add(args):
    checker.add_contact_info_to_list(asn=args.asn, prefix=args.prefix, contact_type=args.type, contact_info=args.dest)
    # いちいち保存すると遅い？
    checker.save_contact_list()


# 連絡先のリストアップ
def command_list(args):
    checker.print_conatct_lists()


# デーモンの開始と終了
def command_daemon(args):
    alertd = roamon_alert_daemon.RoamonAlertDaemon(pid_file_path, log_path, checker)
    # 起動
    if args.start:
        alertd.start()

    # 終了
    if args.stop:
        alertd.stop()


def command_help(args):
    print(parser.parse_args([args.command, '--help']))
    # TODO: ヘルプをうまくやる


# コマンドラインパーサーを作成
parser = argparse.ArgumentParser(description='ROA - BGP Diff command !')
subparsers = parser.add_subparsers()

# get コマンドの parser を作成
parser_add = subparsers.add_parser('add', help="see `get -h`. It's command to add contact info." )
parser_add.add_argument('--asn', default="-1", help='specify watch ASN')
parser_add.add_argument('--prefix', default="255.255.255.255", help='specify watch ip prefix')
parser_add.add_argument('--type', default="email", help='specify contact type, such as email or slack.')
parser_add.add_argument('--dest', default="DUMMY_DEST@example.com", help='specify contact dest, such as e-mail address or Slack info')
# parser_add.add_argument('-p', '--path', default="/tmp", help='specify data dirctory')
parser_add.set_defaults(handler=command_add)

# list コマンドの parser を作成
parser_list = subparsers.add_parser('list', help="see `get -h`. It's command to list up contact info.")
parser_list.set_defaults(handler=command_list)

# daemonコマンドのパーサを作成
parser_daemon = subparsers.add_parser('daemon', help="see `get -h`. It's command to control daemon.")
parser_daemon.add_argument('--start', action='store_true', help='start daemon (DEFAULT)')
parser_daemon.add_argument('--stop', action='store_true', help='stop daemon')
parser_daemon.set_defaults(handler=command_daemon)

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
