#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
from configparser import ConfigParser
from datetime import datetime
from subprocess import PIPE, Popen

from cgsensor import BME280, TSL2572  # type: ignore
from smb.SMBConnection import SMBConnection as NAS

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
    table: list = list()
    registered_sensornames: list = list()

    backup_ip: str
    backup_service_name: str
    backup_path: str

    def __init__(self, name: str) -> None:
        self.status: bool = True
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

        try:
            db_command_create: list = ["CREATE TABLE IF NOT EXISTS"]
            db_command_create.append("condition")
            db_command_create.append("(")
            db_command_create.append(",".join(self.table))
            db_command_create.append(")")

            values: tuple = tuple([self.now] + list(self.data.values()))
            db_command_insert: list = ["INSERT INTO"]
            db_command_insert.append("condition")
            db_command_insert.append("VALUES(")
            db_command_insert.append(",".join(["?"] * len(values)))
            db_command_insert.append(")")

            with sqlite3.connect(database=f"{self.name}.sqlite3") as cn:
                cc = cn.cursor()
                cc.execute(" ".join(db_command_create))
                cc.execute(" ".join(db_command_insert), values)

                self.status = True

        except sqlite3.DatabaseError as err:
            raise SENSORError((f"{self.__class__.__name__} Store", err))

        except OSError as err:
            raise SENSORError((f"{self.__class__.__name__} Store", err))

        finally:
            return self.status

    def backup(self) -> bool:
        self.status = False

        try:
            conn = NAS("NA", "NA", "NA", "NA", is_direct_tcp=True)
            conn.connect(ip=self.backup_ip, port=445)

            with open(file=f"{self.name}.sqlite3", mode="rb") as f:
                conn.storeFile(self.backup_service_name, f"{self.backup_path}/{self.name}.sqlite3", f)

            conn.close()

            self.status = True

        except OSError as err:
            raise SENSORError((f"{self.__class__.__name__} Backup", err))

        finally:
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
            raise SENSORError((f"{self.__class__.__name__} Check", ioerr))

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
            raise SENSORError((f"{self.__class__.__name__} Measure", ioerr))

        finally:
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
            raise SENSORError((f"{self.__class__.__name__} Check", ioerr))

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
            raise SENSORError((f"{self.__class__.__name__} Measure", ioerr))

        finally:
            return self.status


def config(sensor_type: str) -> list:
    def str2list(target: str, sep: str = ",") -> list:
        return list(map(lambda x: x.strip(), target.split(sep=sep)))

    config = ConfigParser(converters={"list": str2list})
    config.read("config.ini")

    result: list = config.getlist(sensor_type, "sensorlist")  # type: ignore

    _sensor.backup_ip = config.get(sensor_type, "ip")
    _sensor.backup_service_name = config.get(sensor_type, "service_name")
    _sensor.backup_path = config.get(sensor_type, "path")

    SensorCpu.table = config.getlist(sensor_type, "cputable")  # type: ignore
    SensorBme280.table = config.getlist(sensor_type, "bme280table")  # type: ignore
    SensorTsl2572.table = config.getlist(sensor_type, "tsl2572table")  # type: ignore

    SensorCpu.registered_sensornames = ["cpu"]
    SensorBme280.registered_sensornames = ["extbme280", "mntbme280"]
    SensorTsl2572.registered_sensornames = ["mnttsl2572"]

    return result


if __name__ == "__main__":
    # "DEFAULT", "PRZWO" ,"ADRWB", "ADRWO"
    sensornames: list = config("DEFAULT")

    sensors: list = list()
    for sensorname in sensornames:
        for sensorclass in _sensor.__subclasses__():
            if sensorname in sensorclass.registered_sensornames:
                sensors.append(sensorclass(sensorname))

    for sensor in sensors:
        if sensor.check():
            sensor.measure()
            sensor.store()
            sensor.backup()
