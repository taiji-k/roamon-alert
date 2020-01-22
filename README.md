# roamon-alert
## Current status
動きはします  
Prefix指定での監視などがまだ実装されてません

## Installation & quick start
リポジトリのクローン
```shell
$ git clone https://github.com/taiji-k/roamon-alert.git
```

VagrantでVMを起動します。  
(`roamon-alert/vagrant/Vagrantfile`の中に、プライベートリポジトリにアクセスするためにgithubのusernameとpasswordを入れるとこがあるので書き換えておいてください)
```shell
$ cd roamon-alert/vagrant/
$ vagrant up && vagrant ssh
```

VMのなかでテスト用SMTPサーバを起動します。標準出力を見ていればメールが来たことがわかります。
```shell
> $ cd roamon-alert
> $ cd test/docker-mailhog
> $ sudo docker-compose up
```

VMのなかで、別なシェルでroamon-alertのデーモンを起動します
```shell
> $ cd roamon-alert
> $ sudo python3 roamon_alert_controller.py daemon --start
```

## Files
ファイルの場所などを記していきます。

 * ワーキングディレクトリ(RIBファイルのダウンロード先などになる)：`/var/tmp`
 * pyasnが直接読めるように変換後のBGP経路情報: `/var/tmp/rib.dat`
 * pyasnが直接読めるように変換後の検証済みROAのリスト: `/var/tmp/vrps.dat`
 * 連絡先情報のJSON: `/var/tmp/contact_list.json`
 * デーモンのログファイル: `/tmp/alertd.log`
 * デーモンのPIDファイル: `/var/run/alertd.py`
 
## Usage

### 連絡先追加
例として、ASN 3333に関して異常があったときにemailでexample3333@example.comに連絡を送るように登録する
```
$ sudo python3 roamon_alert_controller.py add --asn 3333 --type email --dest example3333@example.com
```

IP Prefixを指定し、それに関して異常があったときに通知する機能は未実装。

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

### デーモン起動
```
$ sudo python3 roamon_alert_controller.py daemon --start 
```

`/tmp/alertd.log`にログが出る。  
1時間ごとにBGP経路情報(RouteViewsのRIBファイル)と検証済みROAをとってきて、中身をチェックする。 異常があれば対応する連絡先にメールやSlackを送る。  
 


### デーモン停止
```
$ sudo python3 roamon_alert_controller.py daemon --stop
```

