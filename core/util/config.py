import configparser
import logging.config
import platform
from datetime import date

from core.util.constants import *


def __config_tuple_parse(tuple_string):
    return tuple(int(i) for i in tuple_string.strip("()").split(","))


def __get_log_name():
    return date.today().strftime("%Y_%m_%d.log")


def purge_option_config(option):
    logger.debug("project: " + option + " does not exist or is not valid, remove it from open projects")
    nect_config.remove_option(OPEN_PROJECTS, option)
    write_config()


def write_config():
    logger.debug(f"save pynect configuration file")
    with open(CONFIG_FILE, 'w') as config_file:
        nect_config.write(config_file)


def change_fps(fps) -> bool:
    if nect_config[CONFIG][REFRESH_RATE] == fps:
        logger.debug("tried to change fps but it's the same fps")
        return False
    else:
        logger.debug(f"try to change fps from: {nect_config[CONFIG][REFRESH_RATE]} to: {fps}")
        nect_config[CONFIG][REFRESH_RATE] = fps
        write_config()
        return True


# load config file
nect_config = configparser.ConfigParser()
nect_config.optionxform = str
exist = nect_config.read(CONFIG_FILE)
if not exist:
    nect_config[CONFIG] = {
        LANGUAGE: LANGUAGE_DEFAULT,
        I18N_PATH: I18N_PATH_DEFAULT,
        LOGGER: LOGGER_DEFAULT,
        LOGGER_PATH: LOGGER_PATH_DEFAULT,
        LOG_FOLDER: LOG_FOLDER_DEFAULT,
        PROJECTS_FOLDER: PROJECTS_FOLDER_DEFAULT,
        GUIDE_FILE: GUIDE_FILE_DEFAULT,
        REFRESH_RATE: REFRESH_RATE_15FPS,
        CALIBRATION_PATH: CALIBRATION_PATH_DEFAULT
    }
    nect_config[CALIBRATION] = {
        SQUARE_SIZE: SQUARE_SIZE_DEFAULT,
        PATTERN_SIZE: PATTERN_SIZE_DEFAULT
    }
    nect_config[FRAMES] = {
        IR_IMAGE_SIZE: IR_IMAGE_SIZE_DEFAULT,
        RGB_IMAGE_SIZE: RGB_IMAGE_SIZE_DEFAULT,
        INDEX_FOR_BACKGROUND: INDEX_FOR_BACKGROUND_DEFAULT
    }
    nect_config[OPEN_PROJECTS] = {}
# global logger
logging.config.fileConfig(fname=Path(nect_config[CONFIG][LOGGER_PATH]), disable_existing_loggers=False,
                          defaults={
                              LOG_FOLDER: str((Path(nect_config[CONFIG][LOG_FOLDER]) / __get_log_name()).resolve())})
logger = logging.getLogger(nect_config[CONFIG][LOGGER])

IR_IMAGE_SIZE_PARSED = __config_tuple_parse(nect_config[FRAMES][IR_IMAGE_SIZE])
RGB_IMAGE_SIZE_PARSED = __config_tuple_parse(nect_config[FRAMES][RGB_IMAGE_SIZE])
RGB_IMAGE_SIZE_HALVED = tuple(x // 2 for x in RGB_IMAGE_SIZE_PARSED)
PATTERN_SIZE_PARSED = __config_tuple_parse(nect_config[CALIBRATION][PATTERN_SIZE])


if not exist:
    write_config()

operating_system = platform.system()

windowing_system = ""

logger.debug("config.py imported")
