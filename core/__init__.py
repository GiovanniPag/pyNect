from core.util import logger
from core.util.constants import *
from core.util.language_resource import i18n
from core.views.dialog import DialogMessage


def open_error_dialog(master, missing, icon=ERROR_ICON):
    logger.debug(f"open error for {missing} dialog")
    detail = i18n.scan_error_dialog[I18N_DETAIL]
    for key in missing:
        detail += "\n" + i18n.scan_error_dialog[key]
    DialogMessage(master=master,
                  title=i18n.scan_error_dialog[I18N_TITLE],
                  message=i18n.scan_error_dialog[I18N_MESSAGE],
                  detail=detail,
                  icon=icon).show()


def open_message_dialog(master, message, icon=INFORMATION_ICON):
    logger.debug(f"open project_{message} dialog")
    data = i18n.project_message[message]
    DialogMessage(master=master,
                  title=data[I18N_TITLE],
                  message=data[I18N_MESSAGE],
                  detail=data[I18N_DETAIL],
                  icon=icon).show()
