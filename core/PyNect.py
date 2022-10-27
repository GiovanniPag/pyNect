import cv2 as open_cv
from pylibfreenect2 import Freenect2
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from tkinter import HORIZONTAL, VERTICAL

from core import open_message_dialog
from core.util import call_by_ws, config as c, check_if_folder_exist, check_if_is_project
from core.util.config import logger, nect_config, purge_option_config
from core.util.constants import OPEN_PROJECTS, P_PATH, ERROR_ICON, I18N_MODALITY, I18N_FRAMES
from core.util.language_resource import i18n
from core.controllers.controller import MenuController, Controller, TreeController, \
    SensorController, SelectedFileController, SelectedProjectController, ProjectActionController
from core.views.view import MenuBar, View, ProjectTreeView, SensorView, ScrollWrapperView, \
    SelectedFileView, ProjectInfoView, ProjectActionView


# main window of PyNect MVC app
class PyNect(tk.Tk):

    def __init__(self):
        super().__init__()
        self.option_add('*tearOff', tk.FALSE)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.title(i18n.title)
        c.windowing_system = self.tk.call('tk', 'windowingsystem')
        logger.debug("windowing system: " + c.windowing_system)

        logger.debug("Disable Libfreenect2 logger")
        # setGlobalLogger(None)
        log = createConsoleLogger(LoggerLevel.Debug)
        setGlobalLogger(log)

        self.fn = Freenect2()
        self.devices = []
        self.open_projects = {}
        self.selected_project = None

        self.__check_devices()
        self.__recover_model()
        self.__create_style()
        self.__create_gui()
        self.__create_controllers()
        self.__bind_controllers()

        logger.debug("make opencv use only 1 thread")
        open_cv.setNumThreads(1)  # since OpenCV 4.1.2

        logger.debug("make app full-screen")
        call_by_ws(x11_func=lambda: self.attributes('-zoomed', True), aqua_func=lambda: self.state("zoomed"),
                   win32_func=lambda: self.state("zoomed"))

    @staticmethod
    def __bind_controller(controller: Controller, view: View):
        logger.debug(f"bind {controller.__class__} to {view.__class__}")
        controller.bind(view)

    def has_connected_device(self) -> bool:
        logger.debug(f"enumerate kinect devices")
        return self.fn.enumerateDevices() != 0

    def __check_devices(self):
        logger.debug(f"check connected devices")
        if self.has_connected_device():
            self.devices = [self.fn.getDeviceSerialNumber(i).decode('utf-8') for i in range(self.fn.enumerateDevices())]
            logger.debug(f"connected devices {self.devices}")
        else:
            logger.debug(f"no device connected")
            open_message_dialog(self, "no_device", icon=ERROR_ICON)

    def __recover_model(self):
        logger.debug("recover open projects")
        # recover open projects from file
        open_projects = nect_config[OPEN_PROJECTS]
        for option in open_projects:
            logger.debug("opening project: " + open_projects[option] + ", from path: " + option)
            path = Path(option)
            purge = not check_if_folder_exist(path)
            if not purge:
                logger.debug("project: " + open_projects[option] + " folder exist")
                is_project, metadata = check_if_is_project(path, open_projects[option])
                if is_project:
                    logger.debug("project: " + option + " exists, add it to open projects")
                    self.add_project(metadata, open_projects[option])
                else:
                    purge = True
            if purge:  # purge not found
                purge_option_config(option)

    def add_project(self, project_data, project_name):
        logger.debug(f"add {project_data} from {project_data[project_name][P_PATH]} to open projects")
        self.open_projects[project_data[project_name][P_PATH]] = project_data

    @staticmethod
    def __create_style():
        logger.debug("create style")
        # Initialize style
        s = ttk.Style()
        # Create style used by default for all Frames
        s.configure('TFrame', background='green')
        # Create style for the first frame
        s.configure('Right.TFrame', background='red')
        s.configure('Image.TFrame', background='blue')
        s.configure('Device.TFrame', background='purple')
        s.configure('Sensor.TFrame', background='yellow')
        s.configure('SList.TFrame', background='pink')
        s.configure('SButtons.TLabelframe', background="orange")

    # create all view classes
    def __create_gui(self):
        logger.debug("create gui")

        # create menu bar
        self.menu_bar = MenuBar(self)

        # create mainframe
        logger.debug("main frame initialization")
        mainframe = ttk.PanedWindow(self, orient=HORIZONTAL)
        mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        logger.debug("right frame initialization")
        right_frame = ttk.PanedWindow(self, orient=VERTICAL, style="Right.TFrame")
        logger.debug("center frame initialization")
        center_frame = ttk.PanedWindow(self, orient=VERTICAL)
        # create views
        # left views
        scroll_wrapper = ScrollWrapperView(master=mainframe)
        self.project_tree_view = ProjectTreeView(master=scroll_wrapper, data=self.open_projects)
        scroll_wrapper.add(self.project_tree_view)
        # center views
        self.project_info = ProjectInfoView(self)
        self.project_actions = ProjectActionView(self)
        center_frame.add(self.project_info, weight=1)
        center_frame.add(self.project_actions, weight=5)
        # right views
        self.kinect = SensorView(self, style="Sensor.TFrame")
        self.selected_file = SelectedFileView(self)
        right_frame.add(self.kinect, weight=5)
        right_frame.add(self.selected_file, weight=1)

        mainframe.add(scroll_wrapper, weight=0)
        mainframe.add(center_frame, weight=5)
        mainframe.add(right_frame, weight=10)

    def __create_controllers(self):
        logger.debug("create controllers")
        # create controllers
        self.menu_controller = MenuController(self)
        self.tree_controller = TreeController(self)
        self.sensor_controller = SensorController(self)
        self.selected_controller = SelectedFileController(self)
        self.info_controller = SelectedProjectController(self)
        self.action_controller = ProjectActionController(self)

    def __bind_controllers(self):
        logger.debug("bind all controllers")
        # bind views to controllers
        self.__bind_controller(controller=self.menu_controller, view=self.menu_bar)
        self.__bind_controller(controller=self.tree_controller, view=self.project_tree_view)
        self.__bind_controller(controller=self.sensor_controller, view=self.kinect)
        self.__bind_controller(controller=self.selected_controller, view=self.selected_file)
        self.__bind_controller(controller=self.info_controller, view=self.project_info)
        self.__bind_controller(controller=self.action_controller, view=self.project_actions)

        # attach menu_bar
        logger.debug("attach menu_bar")
        self['menu'] = self.menu_bar
        # attach virtual event controllers
        logger.debug("attach virtual event controllers for <<FPSChange>>")
        self.bind("<<FPSChange>>", lambda event: self.update_fps())
        logger.debug("attach virtual event controllers for <<LanguageChange>>")
        self.bind("<<LanguageChange>>", lambda event: self.update_app_language())
        logger.debug("attach virtual event controllers for <<UpdateTree>>")
        self.bind("<<UpdateTree>>", lambda event: self.tree_controller.update_tree_view(populate_root=True))
        logger.debug("attach virtual event controllers for <<selected_project>>")
        self.bind("<<selected_project>>", self.select_project)
        logger.debug("attach virtual event controllers for <<selected_file>>")
        self.bind("<<selected_file>>", self.select_file)

    def select_project(self, event):
        path = self.tree_controller.get_last_selected_project()
        self.selected_project = self.open_projects[str(path)]
        logger.debug(f"select project event {event} path {path}, selected project {self.selected_project}")
        self.info_controller.update_view(self.selected_project)
        self.action_controller.select_project(self.selected_project)

    def select_file(self, event):
        path = self.tree_controller.get_last_selected_file()
        logger.debug(f"select file event {event} data {path}")
        self.selected_controller.update_view(path)

    def take_pictures(self, data, calibration=False):
        if calibration:
            self.sensor_controller.take_calibration_pictures(data)
        else:
            return

    def update_fps(self):
        pass

    def update_app_language(self):
        logger.debug("update app language")
        self.menu_bar.update_language()
        self.project_tree_view.update_language()
        self.kinect.update_language()
        self.selected_file.update_language()
        self.project_info.update_language()
        self.project_actions.update_language()
