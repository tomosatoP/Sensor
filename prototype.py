#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sqlite3
from configparser import ConfigParser
from datetime import datetime
from subprocess import PIPE, Popen

from cgsensor import BME280, TSL2572  # type: ignore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
logger_sh = logging.StreamHandler()
logger_sh.setFormatter(logger_formatter)
logger.addHandler(logger_sh)

ERROR_VALUE: float = -999.9


class SENSORError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.error(f"SENSORError: {args}")


class _sensor:
    cpu_table: list
    bme280_table: list
    tsl2572_table: list

    def __init__(self, name: str) -> None:
        self.status: bool = True
        self.tablelist: list
        self.name: str = name
        self.data: dict = dict()

    def check(self) -> bool:
        self.status = False
        return self.status

    def measure(self) -> bool:
        self.status = False
        self.now: str = datetime.now().isoformat(timespec="seconds")
        return self.status

    def store(self) -> bool:
        self.status = False

        db_command_create: list = ["CREATE TABLE IF NOT EXISTS"]
        db_command_create.append(self.name)
        db_command_create.append("(")
        db_command_create.append(",".join(self.tablelist))
        db_command_create.append(")")

        values: tuple = tuple([self.now] + list(self.data.values()))
        db_command_insert: list = ["INSERT INTO"]
        db_command_insert.append(self.name)
        db_command_insert.append("VALUES(")
        db_command_insert.append(",".join(["?"] * len(values)))
        db_command_insert.append(")")

        with sqlite3.connect(database=f"{self.name}.sqlite3") as cn:
            cc = cn.cursor()
            cc.execute(" ".join(db_command_create))
            cc.execute(" ".join(db_command_insert), values)

            self.status = True

        return self.status

    def backup(self) -> bool:
        self.status = False
        return self.status


class SensorCpu(_sensor):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.data = {"Temp": ERROR_VALUE}

    def check(self) -> bool:
        super().check()

        self.status = True
        return self.status

    def measure(self) -> bool:
        super().measure()

        command: list = ["cat", "/sys/class/thermal/thermal_zone0/temp"]
        with Popen(args=command, stdout=PIPE, text=True) as res:
            if not res.returncode:
                self.data["Temp"] = float(res.communicate()[0]) / 1000.0
                self.status = True

        return self.status

    def store(self) -> bool:
        self.tablelist = self.cpu_table
        super().store()

        return self.status


class SensorBme280(_sensor):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.data = {"Temp": ERROR_VALUE, "Humi": ERROR_VALUE, "Pres": ERROR_VALUE}

    def check(self) -> bool:
        super().check()

        try:
            self.i2c_address: int = 0x76 if self.name == "extbme280" else 0x77
            self.sensor = BME280(self.i2c_address)
            self.status = self.sensor.check_id()
            logger.info(f"BME280 {self.i2c_address:#x} check id: {self.status}")
        except IOError as ioerr:
            raise SENSORError(ioerr)

        finally:
            return self.status

    def measure(self) -> bool:
        super().measure()

        try:
            if self.sensor.forced():
                self.data["Temp"] = self.sensor.temperature
                self.data["Humi"] = self.sensor.humidity
                self.data["Pres"] = self.sensor.pressure
                self.status = True
            else:
                logger.warning(f"Sensor {self.name} did not function properly.")

        except IOError as ioerr:
            raise SENSORError(ioerr)

        finally:
            return self.status

    def store(self) -> bool:
        self.tablelist = self.bme280_table
        super().store()

        return self.status


class SensorTsl2572(_sensor):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.data = {"Illu": ERROR_VALUE}

    def check(self) -> bool:
        super().check()

        try:
            self.i2c_address: int = 0x39
            self.sensor = TSL2572()
            self.status = self.sensor.check_id()
            logger.info(f"TSL2572 {self.i2c_address:#x} check id: {self.status}")

        except IOError as ioerr:
            raise SENSORError(ioerr)

        finally:
            return self.status

    def measure(self) -> bool:
        super().measure()

        try:
            if self.sensor.single_auto_measure():
                self.data["Illu"] = self.sensor.illuminance
                self.status = True
            else:
                logger.warning(f"Sensor {self.name} did not function properly.")

        except IOError as ioerr:
            raise SENSORError(ioerr)

        finally:
            return self.status

    def store(self) -> bool:
        self.tablelist = self.tsl2572_table
        super().store()

        return self.status


def config(sensor_type: str) -> list:
    result: list = list()

    def str2list(target: str, sep: str = ",") -> list:
        return list(map(lambda x: x.strip(), target.split(sep=sep)))

    config = ConfigParser(converters={"list": str2list})
    config.read("config.ini")

    result = config.getlist(sensor_type, "sensorlist")  # type: ignore
    _sensor.cpu_table = config.getlist(sensor_type, "cputable")  # type: ignore
    _sensor.bme280_table = config.getlist(sensor_type, "bme280table")  # type: ignore
    _sensor.tsl2572_table = config.getlist(sensor_type, "tsl2572table")  # type: ignore

    return result


if __name__ == "__main__":
    # "DEFAULT", "PRZWO" ,"ADRWB", "ADRWO"
    sensors: list = config("DEFAULT")

    sensor: list = list()
    for sensorname in sensors:
        if sensorname == "cpu":
            sensor.append(SensorCpu(sensorname))
        elif sensorname in ["extbme280", "mntbme280"]:
            sensor.append(SensorBme280(sensorname))
        elif sensorname == "mnttsl2572":
            sensor.append(SensorTsl2572(sensorname))

    for s in sensor:
        if s.check():
            s.measure()
            s.store()
            s.backup()
            print(s.data)
