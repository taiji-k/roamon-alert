# roamon-alert
## Current status
動きはします  
あと昔のDB使ってない版とデータの構造が変わったため出力内容が変わりました  

## Installation & quick start
リポジトリのクローン
```shell
$ git clone https://github.com/taiji-k/roamon-alert.git
```

### Run on Docker
Dockerを使って実行します  
(`roamon-alert/docker/Dockerfile`の中に、プライベートリポジトリにアクセスするためにgithubのusernameとpasswordを入れるとこがあるので **書き換えておいてください** )
```
$ cd ./docker
$ sudo docker-compose build --no-cache
$ sudo docker-compose up
```
DBサーバ、テスト用SMTPサーバ、roamon-alertを動かすサーバが起動します。  
roamon-alertのサーバに接続してroamon-alertを使用しましょう。

```
$ sudo docker exec -it roamon-alert  /bin/bash
> /# cd roamon-alert
> /# 
```

## Configuration
ファイルの場所やSMTPサーバのなどをコンフィグファイルに書きます

 * ワーキングディレクトリ(RIBファイルのダウンロード先などになる)：`dir_path_data`
 * pyasnが直接読めるように変換後のBGP経路情報: `file_path_rib`
 * pyasnが直接読めるように変換後の検証済みROAのリスト: `file_path_vrps`
 
 * デーモンのログファイル: `log_path`
 * デーモンのPIDファイル: `pid_file_path`
 * SMTPサーバのアドレス: `smtp_server_address`
 * SMTPサーバのポート番号: `smtp_server_port`
 * 送信元メールアドレス: `sender_email_address`
 * チェック間隔: `watch_interval`
 
 * DBサーバホスト名: `db_host`
 * DBサーバポート番号: `db_port`
 * DB名: `db_name`
 * DBユーザ名: `db_user_name`
 * DBパスワード `db_password`
 
 
## Usage

### 連絡先追加
例として、ASN 3333か1234に関して異常があったときにemailでexample3333@example.comに連絡を送るように登録する
```
$ sudo python3 roamon_alert_controller.py add --asns 3333 1234 --type email --dest example3333@example.com
```

### 連絡先一覧
登録された連絡先一覧を表示。  
フォーマットは以下。  
`watched ASN | watched prefix | contact type | contact info`

```
$ sudo python3 roamon_alert_controller.py list
3333    192.168.30.0/24 email   example3333@example.com
196615  192.168.30.0/24 email   example196615@example.com       
327687  192.168.30.0/24 email   example327687@example.com       
201354  192.168.30.0/24 email   example196615@example.com       
135821  192.168.30.0/24 email   example327687@example.com   
```

(NOTE: 上は過去のものであって現在はJSON形式で出ます & watched_prefixやasnが出ません.   
TODO: ここの修正)

### デーモン起動
```
$ sudo python3 roamon_alert_controller.py daemon --start 
```

`/tmp/alertd.log`にログが出る。  
1時間ごとにBGP経路情報(RouteViewsのRIBファイル)と検証済みROAをとってきて、中身をチェックする。  
連絡先登録時に一緒にいれたASNやprefixに関して異常があれば対応する連絡先にメールやSlackを送る。  
 


### デーモン停止
```
$ sudo python3 roamon_alert_controller.py daemon --stop
```

