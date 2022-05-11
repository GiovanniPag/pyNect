import json

from core.util.config import write_config, nect_config, logger
from core.util.constants import *


class I18N:
    # Internationalization
    def __init__(self):
        # init all strings to none
        self.title = None
        self.menu_file = None
        self.menu_edit = None
        self.menu_sensor = None
        self.menu_view = None
        self.menu_window = None
        self.menu_help = None

        self.language = nect_config[CONFIG][LANGUAGE]
        self.i18n_path = Path(nect_config[CONFIG][I18N_PATH])
        logger.debug(f"application language: {self.language} i18n path: {self.i18n_path}")
        self.__resource_language()

    def change_language(self, language) -> bool:
        if self.language == language:
            logger.debug("tried to change language but it's the same language")
            return False
        else:
            logger.debug(f"try to change language from: {self.language} to: {language}")
            nect_config[CONFIG][LANGUAGE] = language
            write_config()
            self.language = language
            self.__resource_language()
            return True

    def __resource_language(self):
        read_file = None
        try:
            logger.debug(f"try to open the language json: {self.i18n_path}/{self.language}.json")
            read_file = open(self.i18n_path / (self.language+".json"), "r")
        except IOError:
            logger.exception("file not found")
            logger.debug(f"open config language json file: {self.i18n_path}/en.json")
            read_file = open(self.i18n_path / "en.json", "r")
        finally:
            with read_file:
                logger.debug("save json data in variables")
                data = json.load(read_file)
                # program title
                self.title = data['title']
                # menu cascade items
                self.menu_file = data['menu']['menu_file']
                self.menu_edit = data['menu']['menu_edit']
                self.menu_help = data['menu']['menu_help']
                self.menu_sensor = data['menu']['menu_sensor']
                # menu file items
                self.menu_file_new = data['menu']['menu_file']["new_project"]
                self.menu_file_open = data['menu']['menu_file']["open_project"]
                self.menu_file_settings = data['menu']['menu_file']["settings"]
                self.menu_file_exit = data['menu']['menu_file']["exit"]
                # menu edit items
                self.menu_edit_undo = data['menu']['menu_edit']["undo"]
                self.menu_edit_redo = data['menu']['menu_edit']["redo"]
                self.menu_edit_cut = data['menu']['menu_edit']["cut"]
                self.menu_edit_copy = data['menu']['menu_edit']["copy"]
                self.menu_edit_paste = data['menu']['menu_edit']["paste"]
                self.menu_edit_delete = data['menu']['menu_edit']["delete"]
                # menu help items
                self.menu_help_language = data['menu']['menu_help']["language"]
                self.menu_help_language_it = data['menu']['menu_help']["language"]['it']
                self.menu_help_language_en = data['menu']['menu_help']["language"]['en']
                self.menu_help_about = data['menu']['menu_help']["about"]
                self.menu_help_logs = data['menu']['menu_help']["logs"]
                self.menu_help_guide = data['menu']['menu_help']["guide"]
                # menu sensor items
                self.menu_sensor_fps = data['menu']['menu_sensor']['fps']
                self.menu_sensor_fps_10 = data['menu']['menu_sensor']['fps']['10fps']
                self.menu_sensor_fps_15 = data['menu']['menu_sensor']['fps']['15fps']
                self.menu_sensor_fps_30 = data['menu']['menu_sensor']['fps']['30fps']
                self.menu_sensor_fps_60 = data['menu']['menu_sensor']['fps']['60fps']
                # dialog buttons
                self.dialog_buttons = data['dialog']['buttons']
                # project exist error dialog
                self.project_message = data['dialog']["project_message"]
                # about dialog
                self.p_options_dialog = data['dialog']["p_options"]
                # choose folder dialog
                self.choose_folder_dialog = data['dialog']["choose_folder"]
                # tree view
                self.tree_view = data['tree_view']
                # device view
                self.device_view_frames = data['device_view']['frames']
                # selected file view
                self.selected_file_view = data['selected_file']
                # selected project view
                self.selected_project_view = data['selected_project']
                # project actions
                self.project_actions_scan = data['project_actions']['scan']
                self.project_actions_reg = data['project_actions']['registration']
                self.project_actions_final = data['project_actions']['final']


i18n = I18N()
