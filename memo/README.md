# プログラミングの覚書
目的：Coding で困って行ったことなどを記録

## Raspberry Pi Zero WH 設定
1. Raspberry Pi Imager で microSDカードに OSイメージを書き出し
1. Raspberry Pi Zero WH に microSDカードを挿入
1. Raspberry Pi Zero WH に PRZ-IR-Sensor Ver.2, 外付けBME280センサーを接続
1. Raspberry Pi Zero WH を起動
~~~sh
~ $ sudo apt update
~ $ sudo apt -y full-upgrade
~ $ sudo apt -y autoremove
~ $ sudo reboot
~ $ sudo raspi-config
~~~
|||||
|---|---|---|---|
|8 Update||||
|1 System Options|S5 Boot Auto Login|B2 Console Autologin||
||S6 Network at Boot|Yes||
|3 Interface Options|I5 I2C|Yes||
|5 Localisation Options|L1 Local|en_GB.UTF-8<br>ja_JP.UTF-8|ja_JP.UTF-8|
||L2 Timezone|Asia|Tokyo|
||L3 Keyboard|||
||L4 WLAN Country|JP Japan||

~~~diff
+  dtoverlay=disable-bt
~~~

## I2C の有効化と確認
[温度/湿度/気圧/明るさ/赤外線 ホームIoT拡張ボード](README.md) の `I2C の有効化と確認` を参照

## インストール
[温度/湿度/気圧/明るさ/赤外線 ホームIoT拡張ボード](README.md) の `インストール` を参照

## 開発
Raspberry Pi OS Lite 32bit版では VSCode リモート接続不可ので、SSH接続のターミナルを利用。<br>
> Ubuntu(on WSL2) のターミナル

1. GitHubサイト でリモートリポジトリ[https://github.com/tomosatoP/Sensor]を作成
1. GitHubサイト で `LICENCE` を追加
1. GitHubサイト で python 用の `.gitignore` を追加
1. ターミナルから...
~~~sh
~ $ git config --global user.name [username]
~ $ git config --global user.email [useremail]
# リモートリポジトリから取得
~ $ git clone https://github.com/tomosatoP/Sensor.git
# 作成、追加、コミット
~/Sensor $ nano README.md
~/Sensor $ git add README.md
~/Sensor $ git commit -m "Add file"
# ブランチの作成、変更
~/Sensor $ git branch -M main
# リモートリポジトリに反映
~/Sensor $ git push -u origin main
# リモートリポジトリを変更したら
~/Sensor $ git pull origin main
~~~

[git commit 時に自動コードチェックと整形](https://blog.imind.jp/entry/2022/03/11/003534)
`git commit` 時に実行され、`pass` しないとコミットされない。
~~~sh
~ $ sudo -H python3 -m pip install -U pre-commit black isort flake8 pyproject-flake8 mypy
~/Sensor $ pre-commit sample-config > .pre-commit-config.yaml
# ".pre-commit-config.yaml" を編集
~/Sensor $ pre-commit autoupdate
# rev にアップデートがあれば、".pre-commit-config.yaml" を編集
~/Sensor $ pre-commit install
~~~
`pyproject.toml` に設定を記述する。
