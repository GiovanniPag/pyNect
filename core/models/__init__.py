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
