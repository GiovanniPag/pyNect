import os
import shutil
from configparser import ConfigParser

from core.util import nect_config
from core.util.config import write_config, logger
from core.util.constants import *


def create_project_folder(path: Path):
    try:
        path.mkdir()
        (path / F_SCANS).mkdir()
        (path / F_REG).mkdir()
        (path / F_FINAL).mkdir()
    except (FileExistsError, FileNotFoundError):
        logger.exception("Creation of the directories failed")
    else:
        logger.debug("Successfully created the project directories")


def remove_calibration_backup(serial):
    calibration_path = Path(nect_config[CONFIG][CALIBRATION_PATH])
    if (calibration_path / serial).is_dir():
        shutil.rmtree((calibration_path / (serial + "_backup")))


def restore_calibration_backup(serial):
    calibration_path = Path(nect_config[CONFIG][CALIBRATION_PATH])
    if (calibration_path / serial).is_dir():
        shutil.rmtree((calibration_path / serial))
    if (calibration_path / (serial + "_backup")).is_dir():
        os.rename((calibration_path / (serial + "_backup")), (calibration_path / serial))


def create_calibration_folder(serial, reset=False, backup=False):
    calibration_path = Path(nect_config[CONFIG][CALIBRATION_PATH])
    if (calibration_path / (serial + "_backup")).is_dir():
        shutil.rmtree((calibration_path / (serial + "_backup")))
    if backup and (calibration_path / serial).is_dir():
        os.rename((calibration_path / serial), (calibration_path / (serial + "_backup")))
    elif reset and (calibration_path / serial).is_dir():
        shutil.rmtree((calibration_path / serial))
    try:
        calibration_path.mkdir(parents=True, exist_ok=True)
        (calibration_path / serial).mkdir(parents=True, exist_ok=True)
        (calibration_path / serial / F_RESULTS).mkdir(parents=True, exist_ok=True)
        (calibration_path / serial / F_RGB).mkdir(parents=True, exist_ok=True)
        (calibration_path / serial / F_IR).mkdir(parents=True, exist_ok=True)
    except (FileExistsError, FileNotFoundError):
        logger.exception("Creation of the calibration directories failed")
    else:
        logger.debug("Successfully created the calibration directories")


def add_to_open_projects(path: Path, name=""):
    logger.debug(f"add project {path} to open projects in config file")
    if name:
        nect_config.set(OPEN_PROJECTS, str(path / name), name)
    else:
        nect_config.set(OPEN_PROJECTS, str(path), path.name)
    write_config()


def store_open_project(path, name):
    logger.debug(f"create project {name}.ini config file")
    p_config = ConfigParser()
    p_config.add_section(name)
    p_config.set(name, P_NAME, name)
    p_config.set(name, P_PATH, str(path / name))
    p_config.set(name, P_PATH, str(path / name))
    p_config.add_section(P_SCAN)
    p_config.set(P_SCAN, P_DONE, P_FALSE)
    p_config.set(P_SCAN, P_SCAN_ROT, P_EMPTY)
    p_config.add_section(P_REG)
    p_config.set(P_REG, P_DONE, P_FALSE)
    p_config.add_section(P_FINAL)
    p_config.set(P_FINAL, P_DONE, P_FALSE)
    with open((path / name / (name + '.ini')), 'w') as f:
        p_config.write(f)
    add_to_open_projects(path, name)
    return p_config
