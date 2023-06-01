#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from configparser import ConfigParser
from subprocess import PIPE, Popen

from cgsensor import BME280, TSL2572  # type: ignore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
logger_sh = logging.StreamHandler()
logger_sh.setFormatter(logger_formatter)
logger.addHandler(logger_sh)

error_value: float = -999.9


class SENSORError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        logger.error(f"SENSORError: {args}")


class _sensor:
    def __init__(self) -> None:
        self.check()

    def check(self) -> bool:
        return True

    def measure(self) -> bool:
        return True

    def store(self) -> bool:
        return True

    def backup(self) -> bool:
        return True


def config(sensor_type: str) -> dict:
    result: dict = dict()

    def str2list(target: str, sep: str = ",") -> list:
        return list(map(lambda x: x.strip(), target.split(sep=sep)))

    config = ConfigParser(converters={"list": str2list})
    config.read("config.ini")

    for option in list(config[sensor_type]):
        result[option] = config.getlist(sensor_type, option)  # type: ignore

    return result


def check(sensorlist: list) -> None:
    for sensorname in sensorlist:
        if sensorname == "mnttsl2572":
            sensor = TSL2572()
            logger.info(f"TSL2572 0x39 check id: {sensor.check_id()}")
        elif sensorname == "mntbme280":
            sensor = BME280(0x77)
            logger.info(f"BME280 0x77 check id: {sensor.check_id()}")
        elif sensorname == "extbme280":
            sensor = BME280(0x76)
            logger.info(f"BME280 0x76 check id: {sensor.check_id()}")
        elif sensorname == "cpu":
            pass
        else:
            logger.info(f"{sensorname} is not found.")


def measure(sensorname: str) -> dict:
    try:
        result: dict = dict()

        if sensorname == "cpu":
            result = {"Temp": error_value}
            command: list = ["cat", "/sys/class/thermal/thermal_zone0/temp"]
            with Popen(args=command, stdout=PIPE, text=True) as res:
                if not res.returncode:
                    result["Temp"] = float(res.communicate()[0]) / 1000.0

        elif sensorname == "extbme280":
            result = {"Temp": error_value, "Humi": error_value, "Pres": error_value}
            sensor = BME280(i2c_addr=0x76)
            if sensor.forced():
                result["Temp"] = sensor.temperature
                result["Humi"] = sensor.humidity
                result["Pres"] = sensor.pressure
            else:
                logger.warning(f"Sensor {sensorname} did not function properly.")

        elif sensorname == "mnttsl2572":
            result = {"Illu": error_value}
            sensor = TSL2572()
            if sensor.single_auto_measure():
                result["Illu"] = sensor.illuminance
            else:
                logger.warning(f"Sensor {sensorname} did not function properly.")

    except IOError as ioerr:
        raise SENSORError(ioerr)

    finally:
        return result


if __name__ == "__main__":
    # "DEFAULT", "PRZWO" ,"ADRWB", "ADRWO"
    settings: dict = config("DEFAULT")

    check(settings["sensorlist"])
    for sensor in settings["sensorlist"]:
        print(sensor)
        print(measure(sensor))
