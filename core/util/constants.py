from pathlib import Path

# config file path
CONFIG_FILE = Path.cwd() / "var" / ".conf" / "pynect.ini"
# config file sections
OPEN_PROJECTS = "open projects"
CONFIG = "config"
# config file config section items
LANGUAGE = "language"
I18N_PATH = "i18n_path"
LOGGER = "logger"
LOGGER_PATH = "logger_path"
LOG_FOLDER = "log_folder"
LOG_FILENAME = "log_filename"
PROJECTS_FOLDER = "projects_folder"
GUIDE_FILE = "guide_file"
REFRESH_RATE = "fps"
# config file config section default values
LANGUAGE_DEFAULT = "it"
I18N_PATH_DEFAULT = "var/i18n/"
LOGGER_DEFAULT = "pynectLogger"
LOGGER_PATH_DEFAULT = "var/.conf/logging.ini"
LOG_FOLDER_DEFAULT = "var/.logs/"
PROJECTS_FOLDER_DEFAULT = "projects/"
GUIDE_FILE_DEFAULT = "var/guide.pdf"

# project config file items
P_NAME = "name"
P_PATH = "path"
P_INDEX = "index"

P_EMPTY = ""
P_SCAN = "scan"
P_SCAN_ROT = "rot"
P_SCAN_CAMERA = "rot_cam"
P_SCAN_OBJECT = "rot_obj"
P_REG = "reg"
P_FINAL = "final"
P_DONE = "done"
P_TRUE = "true"
P_FALSE = "false"
# project folders
F_SCANS = "scans"
F_REG = "reg"
F_FINAL = "final"

# tk icons
BASENAME_ICON = "::tk::icons::"
INFORMATION_ICON = "information"
ERROR_ICON = "error"
FULL_QUESTION_ICON = "::tk::icons::question"
# i18n constants
I18N_TITLE = "title"
I18N_NAME = "name"
I18N_MESSAGE = "message"
I18N_DETAIL = "detail"
I18N_NAME_TIP = "name_tip"
I18N_oK_BUTTON = "ok"
I18N_BACK_BUTTON = "back"
I18N_CONFIRM_BUTTON = "confirm"
I18N_CANCEL_BUTTON = "cancel"

# Mac specific
MAC_SHOW_HELP = 'tk::mac::ShowHelp'

# menu options
M_UNDERLINE = "underline"
M_MASTER = "master"
M_LABEL = "label"
M_INDEX = "index"
M_STATE = "state"
M_DEFAULT_STATE = "default_state"
M_STATE_NORMAL = "normal"
M_ACCELERATOR = "accelerator"
M_VALUE = "value"
M_VARIABLE = "variable"
M_RADIO = "radio"
M_COMMAND = "command"

# menu commands names
M_APPLE = "apple"
M_FILE = "file"
M_EDIT = "edit"
M_HELP = "help"
M_SENSOR = "sensor"
M_FPS = "fps"
M_10FPS = "10fps"
M_15FPS = "15fps"
M_30FPS = "30fps"
M_60FPS = "60fps"
M_NEW = "new"
M_OPEN = "open"
M_SETTINGS = "settings"
M_EXIT = "exit"
M_UNDO = "undo"
M_REDO = "redo"
M_CUT = "cut"
M_COPY = "copy"
M_PASTE = "paste"
M_DELETE = "delete"
M_ITEMS = "items"
M_LANGUAGE = "language"
M_ABOUT = "about"
M_LOGS = "logs"
M_GUIDE = "guide"
M_IT = "it"
M_EN = "en"

# tree view strings
T_COLUMNS = "columns"
T_CENTER = "center"
T_NAME = "#0"
T_NAME_HEADING = "name"
T_SIZE = "size"
T_MODIFIED = "modified"
T_END = "end"
T_TEXT = "text"
T_VALUES = "values"
T_FILE_TYPE = "type"
T_PARENT = "parent"

# project view strings
PV_PATH = "path"
PV_NAME = "name"
PV_SCAN = "scan"
PV_REG = "reg"
PV_FINAL = "final"
PV_DONE = "done"
PV_NOT_DONE = "not_done"
PV_NO = "no_project"

# file view strings
FV_PATH = "path"
FV_NO = "no_file"

# project actions strings
PA_NAME = "name"
PA_DISABLED = "disabled"
PA_NORMAL = "normal"

# project actions scans strings
PAS_EXIST = "exist"
PAS_MERGE = "merge"
PAS_OVERRIDE = "override"
PAS_ROT = "rot"
PAS_ROT_OBJ = "rot_obj"
PAS_ROT_CAM = "rot_cam"
PAS_FACE = "face"
PAS_FACE_CROP = "face_crop"
PAS_FACE_DETECT = "face_detect"
PAS_DATA = "data"
PAS_DEPTH = "data_depth"
PAS_BOTH = "data_both"
PAS_FPS = "fps"
PAS_TIME = "time"
PAS_SEC = "time_sec"
PAS_SEC_NAN = "time_sec_nan"
PAS_SEC_INCORRECT = "time_sec_wrong"
PAS_SEC_INFO = "time_sec_info"
PAS_MANUAL = "time_manual"
PAS_START = "time_start"
PAS_STOP = "time_stop"
PAS_SEC_START = "time_start_sec"
PAS_SEC_STOP = "time_stop_sec"

# device view strings
D_RGB = "rgb"
D_IR = "ir"
D_DEPTH = "depth"
# image buffer
IB_IR = "ir"
IB_DEPTH = "depth"
IB_COLOR = "color"

# kinect refresh rate in ms, should run at 15 and 30 fps
REFRESH_RATE_10FPS = "100"
REFRESH_RATE_15FPS = "66"
REFRESH_RATE_30FPS = "33"
REFRESH_RATE_60FPS = "16"
