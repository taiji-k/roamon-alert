Roamon-alert is developed and maintained by JPNIC young dev team.

## Documentation

Roamon-alert is a managing tool for alerting mis-originating BGP routes with email and Slack API. This tool is intended for alerting to IP address holders who can update ROA to solve invalid results from ROV.

## Installation & quick start

To clone from GitHub:
```shell
$ git clone https://github.com/taiji-k/roamon-alert.git
```

## Run in Vagrant

Start VM in Vagrant:
```shell
$ cd roamon-alert/vagrant/
$ vagrant up && vagrant ssh
```

Run a SMTP server for testing:
Shell's I/O will be used for the server. Use tmux or different terminal or launch docker-compose with '-d' option for daemon-mode.
Standard output shows received emails.
```shell
> $ cd roamon-alert
> $ cd test/docker-mailhog
> $ sudo docker-compose up
```

In the VM, start roamon-alert with different shell.
```shell
> $ cd roamon-alert
> $ sudo env "PATH=$PATH" python3 roamon_alert_controller.py daemon --start
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

In docker container, other docker used for SMTP server cannot be launched. You may need different SMTP server accessible from the roamon-alert docker container.
(Currently, if alerting email is not sent correctly, the processes re-start from downloading.)

## Configuration

Specify directory and SMTP server.

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

## Usage

### Add contact

As an example, when INVALID found for AS 3333's announcing prefix, notification is sent via email to example3333@example.com.
```
$ sudo python3 roamon_alert_controller.py add --asn 3333 --type email --dest example3333@example.com
```

### List contacts
List format:
`watched ASN | watched prefix | contact type | contact info`

```
$ sudo python3 roamon_alert_controller.py list
3333    192.168.30.0/24 email   example3333@example.com
196615  192.168.30.0/24 email   example196615@example.com       
327687  192.168.30.0/24 email   example327687@example.com       
201354  192.168.30.0/24 email   example196615@example.com       
135821  192.168.30.0/24 email   example327687@example.com   
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
