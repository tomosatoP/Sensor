#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

external_bme280:int = 0x76
mounted_bme280:int = 0x77
mounted_tsl2572:int = 0x39

error_value: float = -999.9

db_table_name:str = "environment"
db_command_create:list[str] = ["CREATE TABLE IF NOT EXISTS", db_table_name, "(", "FIELDS", ")"]
db_command_insert:list[str] = ["INSERT INTO", db_table_name, "VALUES(", "VALUES", ")"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_logger_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
_logger_sh = logging.StreamHandler()
_logger_sh.setFormatter(_logger_formatter)
logger.addHandler(_logger_sh)


class SENSORError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.error(f"SENSORError: {args}")

def cpu_temp() -> dict:
    from subprocess import Popen, PIPE

    result:dict = {"Temp":error_value}
    command:list = ["cat", "/sys/class/thermal/thermal_zone0/temp"]
    with Popen(args=command, stdout=PIPE, text=True) as res:
        if not res.returncode:
            result["Temp"] = float(res.communicate()[0]) / 1000.0

    return result

def measure(i2c_address:int) -> dict:
    from cgsensor import BME280, TSL2572

    try:
        result: dict = dict()
        if any([i2c_address == external_bme280, i2c_address == mounted_bme280]):
            result = {"Temp":error_value, "Humi":error_value, "Pres":error_value}
            sensor = BME280(i2c_addr = i2c_address)
            if sensor.forced():
                result["Temp"] = sensor.temperature
                result["Humi"] = sensor.humidity
                result["Pres"] = sensor.pressure
            else:
                logger.warning(f"Sensor {i2c_address} did not function properly.")

        elif i2c_address == mounted_tsl2572:
            result = {"Illu":error_value}
            sensor =TSL2572()
            if sensor.single_auto_measure():
                 result["Illu"] = sensor.illuminance
            else:
                logger.warning(f"Sensor {i2c_address} did not function properly.")

    except IOError as ioerr:
        raise SENSORError(ioerr)

    finally:
        return result

def store(db_name:str, values:dict) -> bool:
    from datetime import datetime
    import sqlite3

    now:str = datetime.now().isoformat(timespec = 'seconds')
    with sqlite3.connect(database=db_name) as cn:
        cc = cn.cursor()

        db_command_create[3] = ",".join(["DateTime"] + list(values.keys()))
        cc.execute(" ".join(db_command_create))

        data:tuple = tuple([now] + list(values.values()))
        db_command_insert[3] = ",".join(["?"] * len(data))
        cc.execute(" ".join(db_command_insert), data)

    logger.info(f"Store {db_name}: {values}")
    return True


if __name__ == '__main__':
    store("sensor1.sqlite3", cpu_temp())
    store("sensor2.sqlite3", measure(external_bme280))
    store("sensor3.sqlite3", measure(mounted_bme280))
    store("sensor4.sqlite3", measure(mounted_tsl2572))
