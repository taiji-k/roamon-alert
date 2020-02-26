Roamon-alert is developed and maintained by JPNIC young dev team.

## Documentation

Roamon-alert is a managing tool for alerting mis-originating BGP routes with email and Slack API. This tool is intended for alerting to IP address holders who can update ROA to solve invalid results from ROV.

## Installation & quick start

To clone from GitHub:
```shell
$ git clone https://github.com/taiji-k/roamon-alert.git
```

### Run on docker

Run the following commands at project root directory.

```
$ sudo docker build -t roamon-alert -f ./docker/Dockerfile .
$ sudo docker run --rm -it roamon-alert /bin/bash
># cd /roamon-alert
># pipenv shell
(roamon-alert) >#
```

It starts DB server, SMTP test server, and roamon-alert server.

(Currently, if alerting email is not sent correctly, the processes re-start from downloading.)

Then, start to operate roamon-alert in the container.
```
$ sudo docker exec -it roamon-alert  /bin/bash
> /# cd roamon-alert
> /# 
```

## Configuration

Specify directory and SMTP server, and DB server.

* working directory (to put RIB files): `dir_path_data`
* RIB file as pyasn readable format: `file_path_rib`
* VRPs list as pyasn readable format: `file_path_vrps`

* Contact list as JSON format: `file_path_contact_list`
* daemon logfile: `log_path`
* daemon PID file: `pid_file_path`
* SMTP server address: `smtp_server_address`
* SMTP server port: `smtp_server_port`
* Sender email address: `sender_email_address`
* Watch interval: `watch_interval`

* DB server host name: `db_host`
* DB server port number: `db_port`
* DB name: `db_name`
* DB user name: `db_user_name`
* DB password: `db_password`

## Usage

### Add contact

As an example, when INVALID found for AS 3333's announcing prefix, notification is sent via email to example3333@example.com.
```
$ sudo python3 roamon_alert_controller.py add --asn 3333 --type email --dest example3333@example.com
```

### List contacts
List format:
`contact_info_id | contact_type | contact_dest | watched_prefix | watched asn`

```
$ sudo python3 roamon_alert_controller.py list
1       email   example1@example.com                         None            1899    
2       email   example2@example.com                         147.162.0.0/15  None    
2       email   example2@example.com                         192.168.30.0/24 None         
2       email   example2@example.com                         None            137
3       email   example3@example.com                         None            327687  
4       slack   https://hooks.slack.com/services/TBZC4xxxx   147.162.0.0/15  None  
```

### Running daemon

```
$ sudo python3 roamon_alert_controller.py daemon --start 
```

Log file is `/tmp/alertd.log`.
ROV is taken once a hour.
If specified AS announcing prefix or specified prefix became INVALID, notification is sent via email or slack.

### Stopping daemon

```
$ sudo python3 roamon_alert_controller.py daemon --stop
```

## Thanks

JPNIC roamon project is funded by Ministry of Internal Affairs and Communications, Japan (2019 Nov - 2020 Mar).
