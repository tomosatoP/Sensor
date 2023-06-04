# タイマー駆動
タイマーにより自動計測する。

## systemd への登録
~~~sh
~/Sensor/timer $ sudo cp sensor.service /etc/systemd/system/
~/Sensor/timer $ sudo cp sensor.timer /etc/systemd/system/
~ $ sudo systemctl daemon-reload
~ $ sudo systemctl enable sensor.timer
~ $ sudo systemctl start sensor.timer
~~~

## ファイルの中身
sensor.service
~~~
[Unit]
Description = sensor service

[Service]
Type = simple
WorkingDirectory = [path]/Sensor/
ExecStart = python3 [path]/Sensor/sequence.py
~~~
> [path] は適宜に修正。

sensor.timer
~~~
[Unit]
Description = sensor service with timer
Wants = multi-user.target
After = multi-user.target

[Timer]
OnCalendar = *-*-* *:00/10:00
RandomizedDelaySec = 5s
Unit = sensor.service

[Install]
WantedBy = timers.target
~~~
