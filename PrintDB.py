#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
from datetime import datetime, timedelta


def latestdate(db_name:str):
    with sqlite3.connect(db_name) as cn:
        cc = cn.cursor()

        range_date = timedelta(days = 1)
        base_date = datetime.now()
        select_date = (base_date - range_date).isoformat(timespec = "seconds")

        db_command_select = "SELECT * FROM environment WHERE DateTime > ?"
        cc.execute(db_command_select, (select_date, ))
        for row in cc.fetchall():
            print(row)

if __name__ == '__main__':
    latestdate("sensor1.sqlite3")
    latestdate("sensor2.sqlite3")
    latestdate("sensor3.sqlite3")
    latestdate("sensor4.sqlite3")
