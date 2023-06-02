#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta


def latestdate(db_name: str, table_name: str):
    with sqlite3.connect(db_name) as cn:
        cc = cn.cursor()

        range_date = timedelta(days=1)
        base_date = datetime.now()
        select_date = (base_date - range_date).isoformat(timespec="seconds")

        db_command_select = f"SELECT * FROM {table_name} WHERE DateTime > ?"
        cc.execute(db_command_select, (select_date,))
        for row in cc.fetchall():
            print(row)


if __name__ == "__main__":
    latestdate("cpu.sqlite3", "cpu")
    latestdate("extbme280.sqlite3", "extbme280")
    latestdate("mntbme280.sqlite3", "mntbme280")
    latestdate("mnttsl2572.sqlite3", "mnttsl2572")
