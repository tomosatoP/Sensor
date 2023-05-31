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


def initialize(sensor_type: str) -> dict:
    config = ConfigParser()
    config.read("config.ini")
    sen = config[sensor_type]

    sensorname_list: list = list(map(lambda x: x.strip(), sen["Sensorlist"].split(",")))
    for sensorname in sensorname_list:
        if sensorname == "tsl2572_0x39":
            sensor = TSL2572()
            logger.info(f"TSL2572 0x39 check id: {sensor.check_id()}")
        elif sensorname in ["bme280_0x76", "bme280_0x77"]:
            i2c_addr: int = int(sensorname.split("_")[1], 16)
            sensor = BME280(i2c_addr)
            logger.info(f"BME280 {i2c_addr:#x} check id: {sensor.check_id()}")
        elif sensorname == "cpu":
            pass
        else:
            logger.info(f"{sensorname} is not found.")

    return dict(sen)


def measure(sensorname: str) -> dict:
    try:
        result: dict = dict()

        if sensorname in ["cpu"]:
            result = {"Temp": error_value}
            command: list = ["cat", "/sys/class/thermal/thermal_zone0/temp"]
            with Popen(args=command, stdout=PIPE, text=True) as res:
                if not res.returncode:
                    result["Temp"] = float(res.communicate()[0]) / 1000.0

        elif sensorname in ["bme280_0x76", "bme280_0x77"]:
            i2c_addr: int = int(sensorname.split("_")[1], 16)
            result = {"Temp": error_value, "Humi": error_value, "Pres": error_value}
            sensor = BME280(i2c_addr=i2c_addr)
            if sensor.forced():
                result["Temp"] = sensor.temperature
                result["Humi"] = sensor.humidity
                result["Pres"] = sensor.pressure
            else:
                logger.warning(f"Sensor {i2c_addr} did not function properly.")

        elif sensorname in ["tsl2572_0x39"]:
            result = {"Illu": error_value}
            sensor = TSL2572()
            if sensor.single_auto_measure():
                result["Illu"] = sensor.illuminance
            else:
                logger.warning(f"Sensor {i2c_addr} did not function properly.")

    except IOError as ioerr:
        raise SENSORError(ioerr)

    finally:
        return result


if __name__ == "__main__":
    # "DEFAULT", "PRZWO" ,"ADRWB", "ADRWO"
    a = initialize("DEFAULT")

    for sensor in list(map(lambda x: x.strip(), a["sensorlist"].split(","))):
        print(sensor)
        print(measure(sensor))
