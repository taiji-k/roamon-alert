# roamon-alert
動きはしますが、まだできていないという扱いです

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

VMのなかでテスト用SMTPサーバを起動します。
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


## Usage

### 連絡先追加
例として、ASN 3333に関して異常があったときにemailでexample3333@example.comに連絡を送るように登録する
```
$ sudo python3 roamon_alert_controller.py add --asn 3333 --type email --dest example3333@example.com
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

### デーモン起動
```
$ sudo python3 roamon_alert_controller.py daemon --start 
```

`/tmp/alertd.log`にログが出る。 現在は一定時間ごとに経路をチェックし、異常があれば対応する連絡先にメールやSlackを送る。  
 
 将来的には...  次の機能を追加で実装したい。現状は上にあるようにすでに取得したデータに対してのチェックしかしない  
「一定時間ごとにBGPの経路常用や、VRPs(検証済みROA)を取得してくる。  」

### デーモン停止
```
$ sudo python3 roamon_alert_controller.py daemon --stop
```

