import configparser
import os
import subprocess
from pathlib import Path

from core.util import config as c
from core.util.config import logger, nect_config
from core.util.constants import CONFIG, GUIDE_FILE, LOG_FOLDER, P_NAME, P_PATH, F_SCANS, F_REG, F_FINAL, \
    P_SCAN, P_REG, P_FINAL, P_SCAN_ROT, P_DONE


def open_guide():
    logger.debug(" open guide.pdf file")
    path = nect_config[CONFIG][GUIDE_FILE]
    call_by_os(windows_func=lambda: os.startfile(path), darwin_func=lambda: subprocess.Popen(["open", path]),
               else_func=lambda: subprocess.Popen(["xdg-open", path]))


def is_int(s):
    try:
        value = float(str(s))
        return value.is_integer(), int(value)
    except ValueError:
        return False, None


def open_log_folder():
    logger.debug("Open logs folder")
    path = Path(nect_config[CONFIG][LOG_FOLDER])
    call_by_os(windows_func=lambda: os.startfile(path), darwin_func=lambda: subprocess.Popen(["open", path]),
               else_func=lambda: subprocess.Popen(["xdg-open", path]))


def call_by_ws(x11_func, win32_func, aqua_func):
    if not (callable(x11_func) and callable(win32_func) and callable(aqua_func)):
        logger.exception("one of the argument function is not callable")
        return
    logger.debug("windowing system: " + c.windowing_system)
    if c.windowing_system == "x11":
        x11_func()
    if c.windowing_system == "win32":
        win32_func()
    if c.windowing_system == "aqua":
        aqua_func()


def check_if_folder_exist(path: Path, folder_name="") -> bool:
    logger.debug(f"check if folder {str(path / folder_name)} exist")
    if folder_name:
        return (path / folder_name).is_dir()
    else:
        return path.is_dir()


def check_if_file_exist(path: Path, file_name) -> bool:
    logger.debug(f"check if file {str(path / file_name)} exist")
    return (path / file_name).is_file()


def validate(project_metadata: configparser.ConfigParser, project_name, project_path: Path):
    logger.debug(f"check if project {project_name} is valid")
    valid = not (not project_metadata)
    if valid:
        valid = project_metadata.has_section(project_name) and project_metadata.has_option(project_name, P_NAME) and \
                project_metadata[project_name][P_NAME] == project_name and project_metadata.has_option(project_name,
                                                                                                       P_PATH) and Path(
            project_metadata[project_name][P_PATH]).samefile(project_path) and project_metadata.has_section(
            P_SCAN) and project_metadata.has_option(P_SCAN, P_DONE) \
                and project_metadata.has_option(P_SCAN, P_SCAN_ROT) and project_metadata.has_section(
            P_REG) and project_metadata.has_option(P_REG, P_DONE) and project_metadata.has_section(
            P_FINAL) and project_metadata.has_option(P_FINAL, P_DONE)
    return valid


def check_if_is_project(path: Path, project_name):
    logger.debug(f"check if project {project_name} exist and is valid")
    project_conf = []
    is_project = check_if_file_exist(path, project_name + ".ini") and check_if_folder_exist(
        path / F_SCANS) and check_if_folder_exist(path / F_REG) and check_if_folder_exist(path / F_FINAL)
    if is_project:
        project_conf = configparser.ConfigParser()
        project_conf.read(path / (project_name + ".ini"))
        is_project = validate(project_metadata=project_conf, project_name=project_name, project_path=path)
    return is_project, project_conf


def call_by_os(windows_func, darwin_func, else_func):
    if not (callable(windows_func) and callable(darwin_func) and callable(else_func)):
        logger.exception("one of the argument function is not callable")
        return
    if c.operating_system == "Windows":
        windows_func()
    elif c.operating_system == "Darwin":
        darwin_func()
    else:
        try:
            else_func()
        except Exception as e:
            logger.exception("call_by_ws exception in else_func", e)
