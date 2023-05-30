# 温度/湿度/気圧/明るさ/赤外線 ホームIoT拡張ボード
Raspberry Pi 用 RPZ-IR-Sensor を使った室内環境モニタリング

## ハードウェア
[Raspberry Pi Zero WH](https://www.raspberrypi.com/products/raspberry-pi-zero/)<br>
microSD Card : 16G<br>
[PRZ-IR-Sensor Ver.2](https://www.indoorcorgielec.com/products/rpz-ir-sensor/)<br>
[外付けBME280センサー](https://www.indoorcorgielec.com/products/rpz-ir-sensor/)<br>
> [ADRSZBM](https://btoshop.jp/collections/iotcategory_iot/products/adrszbm)も可

## ソフトウェア
[RaspberryPi OS Lite 32bit](https://downloads.raspberrypi.org/raspios_lite_armhf/release_notes.txt)<br>
[cgsensor](https://github.com/IndoorCorgi/cgsensor)

## 使い方
### I2C の有効化と確認
Raspberry Pi Zero WH, PRZ-IR-Sensor Ver.2, 外付けBME280センサーを接続して、
~~~sh
~ $ sudo raspi-config
# [3 Interface Options] - [I5 I2C] - [Yes]
~ $ sudo apt install -y i2c-tools
~ $ i2cdetect -y 1
~~~
> 接続済みの i2cアドレス を検出<br>
>> 0x39: 実装の TSL2572<br>
>> 0x76: 外付けの BME280<br>
>> 0x77: 実装の BME280

### インストール
~~~sh
~ $ sudo apt -y install python3 python3-pip
~ $ sudo -H python3 -m pip install --upgrade pip
~ $ sudo -H python3 -m pip install -U cgsensor
~ $ sudo apt install -y git
~ $ git clone https://github.com/tomosatoP/Sensor.git
~~~

### 実行
~~~sh
~/Sensor $ python3 IndoorEnvironment.py
~~~
> [タイマー駆動](timer/README.md)も参照
---
