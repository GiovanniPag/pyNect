import configparser
import logging.config
import platform
from datetime import date

from core.util.constants import *


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
nect_config.read(CONFIG_FILE)
if not nect_config:
    nect_config[CONFIG] = {
        LANGUAGE: LANGUAGE_DEFAULT,
        I18N_PATH: I18N_PATH_DEFAULT,
        LOGGER: LOGGER_DEFAULT,
        LOGGER_PATH: LOGGER_PATH_DEFAULT,
        LOG_FOLDER: LOG_FOLDER_DEFAULT,
        PROJECTS_FOLDER: PROJECTS_FOLDER_DEFAULT,
        GUIDE_FILE: GUIDE_FILE_DEFAULT,
        REFRESH_RATE: REFRESH_RATE_15FPS
    }
    write_config()

# global logger
logging.config.fileConfig(fname=Path(nect_config[CONFIG][LOGGER_PATH]), disable_existing_loggers=False,
                          defaults={
                              LOG_FOLDER: str((Path(nect_config[CONFIG][LOG_FOLDER]) / __get_log_name()).resolve())})
logger = logging.getLogger(nect_config[CONFIG][LOGGER])

operating_system = platform.system()

windowing_system = ""

logger.debug("config.py imported")
