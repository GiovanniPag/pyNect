import time
import tkinter as tk
from configparser import ConfigParser

from tkinter import ttk, VERTICAL
from abc import abstractmethod, ABC
from typing import Optional

from pylibfreenect2 import FrameMap, SyncMultiFrameListener, FrameType
import cv2 as open_cv
import numpy as np
import PIL.Image
import PIL.ImageTk

from core.controllers import Controller
from core.util import config
from core.util.config import logger, nect_config
from core.util.constants import *
from core.util.language_resource import i18n
from core.views import View, AutoScrollbar, AutoWrapMessage, ScrollFrame, DiscreteStep, check_num

logger.debug("import pipeline module")
try:
    from pylibfreenect2 import OpenGLPacketPipeline as Pipeline
except ImportError as error:
    logger.exception("OpenGLPacketPipeline import error", error)
    try:
        from pylibfreenect2 import OpenCLPacketPipeline as Pipeline
    except ImportError as error:
        logger.exception("OpenCLPacketPipeline import error", error)
        from pylibfreenect2 import CpuPacketPipeline as Pipeline
pipeline = Pipeline()
logger.info(f"Packet pipeline: {type(pipeline).__name__}")


class ScrollWrapperView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.widget = None
        self.scroll = None

    def add(self, widget):
        logger.debug(f"add widget {widget} to scroll wrapper view")
        self.widget = widget
        self.scroll = AutoScrollbar(self, orient=VERTICAL, command=self.widget.yview, column_grid=1, row_grid=0)
        self.widget.configure(yscrollcommand=self.scroll.set)
        self.widget.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

    def create_view(self):
        logger.debug(f"create view in scroll wrapper view")
        self.widget.create_view()

    def update_language(self):
        logger.debug(f"update language in scroll wrapper view")
        self.widget.update_language()


class TabbedView(View, ABC):

    def __init__(self, master, switch_func=None, **kw):
        super().__init__(master, **kw)
        self.master = master
        self.switch_func = switch_func
        ttk.Style().configure(type(self).__name__ + '.Toolbutton', anchor='center', padding=2, relief=tk.GROOVE)
        self.current_frame = None
        self.__count = 0
        self.__frame_choice = tk.IntVar(0)
        self.__side = tk.LEFT
        self.__options_frame = tk.Frame(self)
        self.__options_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.__buttons = {}
        self.__buttons_name = {}
        self.__width = 0
        self.i18n_frame_names = {}

    def add(self, title, frame, b_id):
        logger.debug(f"add frame: {frame} to tabbed view")
        b = ttk.Radiobutton(self.__options_frame, text=title, style=type(self).__name__ + '.Toolbutton',
                            variable=self.__frame_choice, value=self.__count, command=lambda: self.select(frame))
        b.pack(fill=tk.BOTH, side=self.__side, expand=False)
        self.__buttons[frame] = b
        self.__buttons_name[b_id] = b
        if not self.current_frame:
            self.current_frame = frame
            self.select(frame)
        else:
            frame.forget()
        self.__count += 1
        if len(title) > self.__width:
            self.__width = len(title)
        [item.config(width=self.__width) for key, item in self.__buttons.items()]
        return b

    def select(self, new_fr):
        logger.debug(f"select new frame {new_fr} in tabbed view")
        for btn in self.__buttons.values():
            btn.state(['!selected'])
        if self.switch_func is not None:
            self.switch_func(self.current_frame, new_fr)
        self.current_frame.forget()
        new_fr.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.__buttons[new_fr].state(['selected'])
        self.current_frame = new_fr

    def update_language(self):
        logger.debug(f"update language in tabbed view")
        for key, item in self.__buttons_name.items():
            item.configure(text=self.i18n_frame_names[key])


class MenuBar(tk.Menu, View):

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.menu_apple = tk.Menu(self, name=M_APPLE)
        self.menu_file = tk.Menu(self)
        self.menu_edit = tk.Menu(self)
        self.menu_sensor = tk.Menu(self)
        self.menu_help = tk.Menu(self, name=M_HELP)
        self.menu_help_language = tk.Menu(self.menu_help)
        self.menu_sensor_fps = tk.Menu(self.menu_sensor)
        self.menu_sensor_calibrate = tk.Menu(self.menu_sensor)
        self.refresh_rate = tk.StringVar()
        self.language = tk.StringVar()

        self.__menu_names = {
            M_APPLE: {
                M_MASTER: self,
            },
            M_FILE: {
                M_MASTER: self,
                M_INDEX: 0
            },
            M_EDIT: {
                M_MASTER: self,
                M_INDEX: 1
            },
            M_SENSOR: {
                M_MASTER: self,
                M_INDEX: 2
            },
            M_HELP: {
                M_MASTER: self,
                M_INDEX: 3
            },
            M_NEW: {
                M_MASTER: self.menu_file,
                M_INDEX: 0
            },
            M_OPEN: {
                M_MASTER: self.menu_file,
                M_INDEX: 1
            },
            M_SETTINGS: {
                M_MASTER: self.menu_file,
                M_INDEX: 2
            },
            M_EXIT: {
                M_MASTER: self.menu_file,
                M_INDEX: 3
            },
            M_UNDO: {
                M_MASTER: self.menu_edit,
                M_INDEX: 0
            },
            M_REDO: {
                M_MASTER: self.menu_edit,
                M_INDEX: 1
            },
            M_CUT: {
                M_MASTER: self.menu_edit,
                M_INDEX: 2
            },
            M_COPY: {
                M_MASTER: self.menu_edit,
                M_INDEX: 3
            },
            M_PASTE: {
                M_MASTER: self.menu_edit,
                M_INDEX: 4
            },
            M_DELETE: {
                M_MASTER: self.menu_edit,
                M_INDEX: 5
            },
            M_LANGUAGE: {
                M_MASTER: self.menu_help,
                M_INDEX: 0
            },
            M_ABOUT: {
                M_MASTER: self.menu_help,
                M_INDEX: 2
            },
            M_LOGS: {
                M_MASTER: self.menu_help,
                M_INDEX: 3
            },
            M_GUIDE: {
                M_MASTER: self.menu_help,
                M_INDEX: 4
            },
            M_IT: {
                M_MASTER: self.menu_help_language,
                M_RADIO: True,
                M_VARIABLE: self.language,
                M_VALUE: M_IT,
                M_INDEX: 0
            },
            M_EN: {
                M_MASTER: self.menu_help_language,
                M_RADIO: True,
                M_VARIABLE: self.language,
                M_VALUE: M_EN,
                M_INDEX: 1
            },
            M_CALIBRATE: {
                M_MASTER: self.menu_sensor,
                M_INDEX: 1
            },
            M_FPS: {
                M_MASTER: self.menu_sensor,
                M_INDEX: 0
            },
            M_10FPS: {
                M_MASTER: self.menu_sensor_fps,
                M_RADIO: True,
                M_VARIABLE: self.refresh_rate,
                M_VALUE: REFRESH_RATE_10FPS,
                M_INDEX: 0
            },
            M_15FPS: {
                M_MASTER: self.menu_sensor_fps,
                M_RADIO: True,
                M_VARIABLE: self.refresh_rate,
                M_VALUE: REFRESH_RATE_15FPS,
                M_INDEX: 1
            },
            M_30FPS: {
                M_MASTER: self.menu_sensor_fps,
                M_RADIO: True,
                M_VARIABLE: self.refresh_rate,
                M_VALUE: REFRESH_RATE_30FPS,
                M_INDEX: 2
            }
        }

    def create_view(self):
        logger.debug(f"create view in menu bar")
        if config.windowing_system == "aqua":
            self.add_cascade_item(menu_name=M_APPLE, menu_to_add=self.menu_apple, info={})
            self.master.createcommand(MAC_SHOW_HELP, ...)
        self.add_cascade_item(menu_name=M_FILE, menu_to_add=self.menu_file, info=i18n.menu_file)
        self.add_cascade_item(menu_name=M_EDIT, menu_to_add=self.menu_edit, info=i18n.menu_edit)
        self.add_cascade_item(menu_name=M_SENSOR, menu_to_add=self.menu_sensor, info=i18n.menu_sensor)
        self.add_cascade_item(menu_name=M_HELP, menu_to_add=self.menu_help, info=i18n.menu_help)
        # menu_sensor items
        self.add_cascade_item(menu_name=M_CALIBRATE, menu_to_add=self.menu_sensor_calibrate,
                              info=i18n.menu_sensor_calibrate)
        self.add_cascade_item(menu_name=M_FPS, menu_to_add=self.menu_sensor_fps, info=i18n.menu_sensor_fps)
        # menu_sensor_fps items
        self.add_command_item(cmd_name=M_10FPS, info=i18n.menu_sensor_fps_10)
        self.add_command_item(cmd_name=M_15FPS, info=i18n.menu_sensor_fps_15)
        self.add_command_item(cmd_name=M_30FPS, info=i18n.menu_sensor_fps_30)
        # menu_file items
        self.add_command_item(cmd_name=M_NEW, info=i18n.menu_file_new)
        self.add_command_item(cmd_name=M_OPEN, info=i18n.menu_file_open)
        self.add_command_item(cmd_name=M_SETTINGS, info=i18n.menu_file_settings)
        self.add_command_item(cmd_name=M_EXIT, info=i18n.menu_file_exit)
        # menu_edit items
        self.add_command_item(cmd_name=M_UNDO, info=i18n.menu_edit_undo)
        self.add_command_item(cmd_name=M_REDO, info=i18n.menu_edit_redo)
        self.add_command_item(cmd_name=M_CUT, info=i18n.menu_edit_cut)
        self.add_command_item(cmd_name=M_COPY, info=i18n.menu_edit_copy)
        self.add_command_item(cmd_name=M_PASTE, info=i18n.menu_edit_paste)
        self.add_command_item(cmd_name=M_DELETE, info=i18n.menu_edit_delete)
        # menu_help items
        self.add_cascade_item(menu_name=M_LANGUAGE, menu_to_add=self.menu_help_language, info=i18n.menu_help_language)
        # separator
        self.menu_help.add_separator()
        self.add_command_item(cmd_name=M_ABOUT, info=i18n.menu_help_about)
        self.add_command_item(cmd_name=M_LOGS, info=i18n.menu_help_logs)
        self.add_command_item(cmd_name=M_GUIDE, info=i18n.menu_help_guide)
        # menu_help_language
        self.add_command_item(cmd_name=M_IT, info=i18n.menu_help_language_it)
        self.add_command_item(cmd_name=M_EN, info=i18n.menu_help_language_en)

    def update_language(self):
        logger.debug(f"{self.winfo_name()} update language")
        self.update_command_or_cascade(name=M_FILE, info_updated=i18n.menu_file)
        self.update_command_or_cascade(name=M_EDIT, info_updated=i18n.menu_edit)
        self.update_command_or_cascade(name=M_HELP, info_updated=i18n.menu_help)
        self.update_command_or_cascade(name=M_SENSOR, info_updated=i18n.menu_sensor)
        # menu_file items
        self.update_command_or_cascade(name=M_NEW, info_updated=i18n.menu_file_new)
        self.update_command_or_cascade(name=M_OPEN, info_updated=i18n.menu_file_open)
        self.update_command_or_cascade(name=M_SETTINGS, info_updated=i18n.menu_file_settings)
        self.update_command_or_cascade(name=M_EXIT, info_updated=i18n.menu_file_exit)
        # menu_edit items
        self.update_command_or_cascade(name=M_UNDO, info_updated=i18n.menu_edit_undo)
        self.update_command_or_cascade(name=M_REDO, info_updated=i18n.menu_edit_redo)
        self.update_command_or_cascade(name=M_CUT, info_updated=i18n.menu_edit_cut)
        self.update_command_or_cascade(name=M_COPY, info_updated=i18n.menu_edit_copy)
        self.update_command_or_cascade(name=M_PASTE, info_updated=i18n.menu_edit_paste)
        self.update_command_or_cascade(name=M_DELETE, info_updated=i18n.menu_edit_delete)
        # menu_help items
        self.update_command_or_cascade(name=M_LANGUAGE, info_updated=i18n.menu_help_language)
        self.update_command_or_cascade(name=M_ABOUT, info_updated=i18n.menu_help_about)
        self.update_command_or_cascade(name=M_LOGS, info_updated=i18n.menu_help_logs)
        self.update_command_or_cascade(name=M_GUIDE, info_updated=i18n.menu_help_guide)
        # menu_help_language items
        self.update_command_or_cascade(name=M_IT, info_updated=i18n.menu_help_language_it)
        self.update_command_or_cascade(name=M_EN, info_updated=i18n.menu_help_language_en)
        # menu_sensor items
        self.update_command_or_cascade(name=M_CALIBRATE, info_updated=i18n.menu_sensor_calibrate)
        self.update_command_or_cascade(name=M_FPS, info_updated=i18n.menu_sensor_fps)
        # menu_sensor_fps items
        self.update_command_or_cascade(name=M_10FPS, info_updated=i18n.menu_sensor_fps_10)
        self.update_command_or_cascade(name=M_15FPS, info_updated=i18n.menu_sensor_fps_15)
        self.update_command_or_cascade(name=M_30FPS, info_updated=i18n.menu_sensor_fps_30)

    def add_cascade_item(self, menu_name, menu_to_add, info):
        logger.debug(f"add cascade item {menu_to_add} to {menu_name} with info {info}")
        self.__menu_names[menu_name][M_MASTER].add_cascade(menu=menu_to_add, label=info.get(M_LABEL, ""),
                                                           underline=info.get(M_UNDERLINE, -1),
                                                           state=info.get(M_DEFAULT_STATE, M_STATE_NORMAL))

    def add_command_item(self, cmd_name, info=None):
        if info:
            logger.debug(f"add command item {cmd_name} with info {info}")
            if self.__menu_names[cmd_name].get(M_RADIO, False):
                self.__menu_names[cmd_name][M_MASTER] \
                    .add_radiobutton(label=info.get(M_LABEL, ""), underline=info.get(M_UNDERLINE, -1),
                                     state=info.get(M_DEFAULT_STATE, M_STATE_NORMAL),
                                     variable=self.__menu_names[cmd_name][M_VARIABLE],
                                     value=self.__menu_names[cmd_name][M_VALUE],
                                     accelerator=info.get(M_ACCELERATOR, ""), command=...)
            else:
                self.__menu_names[cmd_name][M_MASTER] \
                    .add_command(label=info.get(M_LABEL, ""), underline=info.get(M_UNDERLINE, -1),
                                 state=info.get(M_DEFAULT_STATE, M_STATE_NORMAL),
                                 accelerator=info.get(M_ACCELERATOR, ""), command=...)
        else:
            self.__menu_names[cmd_name][M_MASTER] \
                .add_command(label=cmd_name, state=M_STATE_NORMAL, command=...)

    def add_sensors(self):
        logger.debug(f"add sensors to calibrate menu")
        for serial in self.master.devices:
            self.__menu_names[serial] = {M_MASTER: self.menu_sensor_calibrate,
                                         M_INDEX: 0 if self.menu_sensor_calibrate.index(tk.END) is None
                                         else self.menu_sensor_calibrate.index(tk.END) + 1}
            self.add_command_item(cmd_name=serial)

    def update_command_or_cascade(self, name, info_updated, update_state=False):
        logger.debug(f"update item {name} with info {info_updated}")
        master = self.__menu_names[name][M_MASTER]
        entry_to_update = self.__menu_names[name][M_INDEX]
        if M_LABEL in info_updated:
            master.entryconfigure(entry_to_update, label=info_updated[M_LABEL])
        if M_UNDERLINE in info_updated:
            master.entryconfigure(entry_to_update, underline=info_updated[M_UNDERLINE])
        if M_STATE in info_updated and update_state:
            master.entryconfigure(entry_to_update, state=info_updated[M_STATE])
        if M_ACCELERATOR in info_updated:
            master.entryconfigure(entry_to_update, accelerator=info_updated[M_ACCELERATOR])
        if M_COMMAND in info_updated:
            master.entryconfigure(entry_to_update, command=info_updated[M_COMMAND])


class ProjectTreeView(ttk.Treeview, View):
    def __init__(self, data, master=None):
        super().__init__(master)
        self.master = master
        self.data = data
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def create_view(self):
        logger.debug("create view in project tree view")

        self[T_COLUMNS] = (T_SIZE, T_MODIFIED)
        self.column(T_NAME, anchor=T_CENTER, minwidth=150, width=150)
        self.column(T_SIZE, anchor=T_CENTER, minwidth=150, width=150)
        self.column(T_MODIFIED, anchor=T_CENTER, minwidth=150, width=150)
        self.heading(T_NAME, text=i18n.tree_view[T_COLUMNS][T_NAME_HEADING])
        self.heading(T_SIZE, text=i18n.tree_view[T_COLUMNS][T_SIZE])
        self.heading(T_MODIFIED, text=i18n.tree_view[T_COLUMNS][T_MODIFIED])
        # select mode
        self["selectmode"] = "browse"
        # displayColumns
        self["displaycolumns"] = [T_SIZE, T_MODIFIED]
        # show
        self["show"] = "tree headings"
        # tree Display tree labels in column #0.

    def update_language(self):
        logger.debug("update language in project tree view")
        self.heading(T_NAME, text=i18n.tree_view[T_COLUMNS][T_NAME_HEADING])
        self.heading(T_SIZE, text=i18n.tree_view[T_COLUMNS][T_SIZE])
        self.heading(T_MODIFIED, text=i18n.tree_view[T_COLUMNS][T_MODIFIED])


class SensorListView(TabbedView):

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.master = master

    def update_language(self):
        logger.debug("update language in sensor list view")
        if self.current_frame:
            self.current_frame.update_language()

    def create_view(self):
        pass


class SensorView(View):

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.master = master
        self.sensor_list = SensorListView(self, style="SList.TFrame")
        self._buttons = {}
        self.button_frame = ttk.Frame(self, style="SButtons.TFrame")
        # buttons = list of
        self._time_sec_start = tk.StringVar()
        self._time_sec_stop = tk.StringVar()
        self._time_man_start = tk.StringVar()
        self._time_man_stop = tk.StringVar()

        self._sec_start: Optional[ttk.Button] = None
        self._sec_stop: Optional[ttk.Button] = None
        self._man_start: Optional[ttk.Button] = None
        self._man_stop: Optional[ttk.Button] = None

        '''self._buttons = {
            PAS_START: lambda: self._man_start,
            PAS_STOP: lambda: self._man_stop,
            PAS_SEC_START: lambda: self._sec_start,
            PAS_SEC_STOP: lambda: self._sec_stop
        }'''

    def set_mode(self, btn_name_list):
        self._buttons = {}
        for key, btn_name in btn_name_list:
            self._buttons[btn_name][S_TEXT] = tk.StringVar()
            self._buttons[btn_name][S_TEXT].set(i18n.sensor_buttons[btn_name])
            self._buttons[btn_name][S_BUTTON] = ttk.Button(self.button_frame,
                                                           textvariable=self._buttons[btn_name][S_TEXT],
                                                           command=...)
            self._buttons[btn_name][S_BUTTON].grid(column=key, row=0)
        self._update_grid_weight()

    def unset_mode(self):
        self._buttons = {}
        for widget in self.button_frame.winfo_children():
            widget.destroy()

    def set_command(self, btn_name, command):
        logger.debug(f"scan action view set command {command} for {btn_name}")
        if btn_name in self._buttons.keys():
            self._buttons[btn_name][S_BUTTON].configure(command=command)

    def update_language(self):
        logger.debug("update language in sensor view")
        self.sensor_list.update_language()
        for btn_name in self._buttons.keys():
            self._buttons[btn_name][S_TEXT].set(i18n.sensor_buttons[btn_name])

    def create_view(self):
        # self.sensor_list.grid(column=0, row=0, sticky='news')
        self.sensor_list.pack(fill=tk.BOTH, expand=False)
        self.sensor_list.create_view()
        # create buttons for photos
        self.button_frame.pack(side="top", fill=tk.X, expand=False)

    def _update_grid_weight(self):
        cols, _ = self.button_frame.grid_size()
        for col in range(cols):
            self.button_frame.columnconfigure(col, weight=1)


class DeviceView(TabbedView):

    def create_view(self):
        logger.debug("create view in device view")
        self.pack(side=tk.TOP, fill=tk.X, expand=False)
        # color = ImageView(self, lambda: self.get_image_color(), REFRESH_RATE_15FPS)
        color = ImageView(self, lambda: self.get_image_color(), style="Image.TFrame")
        self.add(i18n.device_view_frames[D_RGB], color, D_RGB)

        ir = ImageView(self, lambda: self.get_image_ir(), style="Image.TFrame")
        self.add(i18n.device_view_frames[D_IR], ir, D_IR)

        depth = ImageView(self, lambda: self.get_image_depth(), style="Image.TFrame")
        self.add(i18n.device_view_frames[D_DEPTH], depth, D_DEPTH)

        self.refresh()

    def update_language(self):
        logger.debug("update language in device view")
        self.i18n_frame_names = i18n.device_view_frames
        super().update_language()

    def __init__(self, master, free_nect, serial, **kw):
        super().__init__(master, **kw)

        self._free_nect = free_nect
        self._serial = serial

        self._device_index = self.__device_list_index()

        self._device = None
        self._listener = None

        self._opened = False
        self._playing = False

        # self._pers_rgb_ir = PERSP_IR_TO_RGB[None]
        # if serial in PERSP_IR_TO_RGB:
        #    self._pers_rgb_ir = PERSP_IR_TO_RGB[serial]

        self.frames = FrameMap()
        self.image_buffer = {IB_COLOR: (None, None, None), IB_IR: (None, None, None), IB_DEPTH: (None, None, None)}

    def open(self):
        logger.debug("open device, start listener")
        self._listener = SyncMultiFrameListener(FrameType.Color | FrameType.Ir | FrameType.Depth)
        self._device = self._free_nect.openDevice(self._serial.encode("utf-8"), pipeline=pipeline)
        device_index = self.__device_list_index()
        if self._device_index != device_index:  # keep track of changes in the device list
            self._device_index = device_index
            self._device.close()
            self._listener.release(self.frames)
            self.open()
            return
        self._device.setColorFrameListener(self._listener)
        self._device.setIrAndDepthFrameListener(self._listener)
        self._device.start()
        self._opened = True
        self._playing = False
        cp = self._device.getColorCameraParams()
        ip = self._device.getIrCameraParams()
        # logger.warning(str(cp.cx) + ", " + str(cp.cy) + ", " + str(cp.fx) + ", " + str(cp.fy))
        # logger.warning(str(ip.cx) + ", " + str(ip.cy) + ", " + str(ip.fx) + ", " + str(ip.fy))

    def opened(self):
        logger.debug("check if device is open in device view")
        return self._opened

    def play(self):
        logger.debug("play device")
        if not self._opened:
            return False
        self._playing = True
        return True

    def playing(self):
        logger.debug("check if device is playing in device view")
        return self._playing

    def stop(self):
        logger.debug("stop device")
        if not self._opened:
            return False
        self._playing = False
        return True

    def close(self):
        logger.debug("close device")
        if not self._opened:
            return
        self._device.close()
        self._opened = False
        self._playing = False

    def refresh(self):
        if self._playing:
            self._listener.release(self.frames)
            for key in self.image_buffer:
                self.image_buffer.update(
                    {key: (None, None, self.image_buffer[key][-1])})  # reset image buffer and keep depth map
            # get frames from sensor here
            self.frames = self._listener.waitForNewFrame()
        self.after(REFRESH_RATE_30FPS, self.refresh)

    def get_image_color(self):
        color, _, _ = self.image_buffer[IB_COLOR]
        if color is not None:
            return self.image_buffer[IB_COLOR]
        color = self.frames[IB_COLOR]
        color = color.asarray(dtype=np.uint8)
        color = np.flip(color, axis=(1,))
        color = open_cv.resize(color, (1920 // 2, 1080 // 2))
        color = open_cv.cvtColor(color, open_cv.COLOR_BGRA2RGBA)
        return self.__to_image(IB_COLOR, color)

    def get_image_ir(self):
        ir, _, _ = self.image_buffer[IB_IR]
        if ir is not None:
            return self.image_buffer[IB_IR]
        ir = self.frames[IB_IR]
        ir = ir.asarray(dtype=np.float32)
        ir = np.flip(ir, axis=(1,))
        d_size = (1920 // 2, 1080 // 2)
        ir = open_cv.resize(ir, d_size)
        # ir = open_cv.warpPerspective(ir, self._pers_rgb_ir, None,
        # borderMode=open_cv.BORDER_CONSTANT, borderValue=65535)
        ir = ir / 65535  # normalize
        return self.__to_image(IB_IR, ir)

    def get_image_depth(self, d_min=0, d_max=5000):
        depth, _, _ = self.image_buffer[IB_DEPTH]
        if depth is not None:
            return self.image_buffer[IB_DEPTH]
        depth = self.frames[IB_DEPTH]
        depth = depth.asarray(dtype=np.float32)
        depth = np.flip(depth, axis=(1,))
        depth = open_cv.resize(depth, (1920 // 2, 1080 // 2))
        # depth = open_cv.warpPerspective(depth, self._pers_rgb_ir, None,
        # borderMode=open_cv.BORDER_CONSTANT, borderValue=d_max)
        buffer = depth.astype(int)
        # logger.error(buffer == d_min)
        # logger.error(buffer[buffer == d_min])
        buffer[buffer == d_max], buffer[buffer == d_min] = -1, -1
        depth = depth / d_max  # normalize
        return self.__to_image(IB_DEPTH, depth, buffer)

    def __to_image(self, key, array, arg=None):
        if array.dtype == np.float32 and len(array.shape) == 2:  # ir or depth, range between 0 and 1
            array = np.asarray(array * np.iinfo(np.uint8).max, dtype=np.uint8)
        img = PIL.Image.fromarray(array)
        self.image_buffer[key] = (img, array, arg)
        return self.image_buffer[key]

    def __device_list_index(self):
        return self.master.master.master.devices.index(self._serial)


class PlotFrame(View):
    _RES = 6  # less is more expensive (more points to render)

    def __init__(self, parent, root, serial, source, xyz=(1, 1, (0, 1))):
        View.__init__(self, parent)

        self.master = root

        self.source = source[0]
        self.colors = source[1]

        self._pers_rgb_ir = PERSP_IR_TO_RGB[None]
        if serial in PERSP_IR_TO_RGB:
            self._pers_rgb_ir = PERSP_IR_TO_RGB[serial]

        crop = self._pers_rgb_ir[0][0]  # scaling by perspective projection
        xsize, ysize = IR_SCREEN_SIZE  # given
        xfov, yfov = IR_SCREEN_FOV  # given

        self.px_to_deg = (xfov / xsize + yfov / ysize) / 2 * np.sin(crop)

        self.xyz = xyz

        self._interrupt = False

        self.data = None
        self.colmap = None

        self.__refresh()

    def __refresh(self, draw=False, autoscale=True):

        r = PlotFrame._RES
        d = -75 * r + 500
        s = 0.5 * r
        if self.colors is None:
            r, s = r // 2, s / 16  # non-scatter

        if self.winfo_viewable() and self.master.playing():

            if not draw:

                _, _, depmap = self.source()

                self.colmap = depmap // 255  # gray
                if self.colors is not None:
                    _, self.colmap, _ = self.colors()
                    self.colmap = self.colmap / 255  # rgb

                a = len(depmap) // r
                b = len(depmap[0]) // r
                i = -1

                davg = 0
                result = []
                x, y, z, c = [None] * a * b, [None] * a * b, [None] * a * b, [None] * a * b
                for py in range(a):
                    for px in range(b):
                        i += 1
                        iy, ix = py * r, px * r
                        if depmap[iy][ix] < 0: continue  # value in valid range?
                        x[i] = ix - b * r // 2
                        y[i] = iy - a * r // 2
                        z[i] = depmap[iy][ix]
                        davg += z[i]
                        c[i] = self.colmap[iy][ix]

                        x[i] = np.tan(np.deg2rad(self.px_to_deg * x[i])) * z[i]
                        y[i] = np.tan(np.deg2rad(self.px_to_deg * y[i])) * z[i]

                        result.append((z[i], x[i], y[i], c[i]))

                if len(result) > 0:

                    dmax = davg / len(z) * 2

                    if autoscale:
                        xw = int(np.sin(np.deg2rad(IR_SCREEN_FOV[0] / 2)) * dmax * 2)
                        yw = int(np.sin(np.deg2rad(IR_SCREEN_FOV[1] / 2)) * dmax * 2)
                        if xw > 2 and yw > 2:
                            self.ax.set_ylim(((-xw // 2), (+xw // 2)))
                            self.ax.set_zlim(((+yw // 2), (-yw // 2)))

                    z, x, y, c = zip(*result)
                    result = sorted(zip(z, x, y, c), reverse=True)  # sort by color
                    self.data = list(zip(*result))  # z, x, y, c

            else:

                if self._interrupt:
                    self._interrupt = False
                    self.after(max(REFRESH_RATE, d // 2), self.__refresh)
                    return

                if len(self.data) > 0:

                    z, x, y, c = self.data

                    # x, y, z = np.broadcast_arrays(*[np.ravel(np.ma.filled(t, np.nan)) for t in [x, y, z]])
                    # points._offsets3d = (z, x, y)  # positions
                    # points._sizes = [s] * len(c)   # sizes set_sizes()
                    # points.set_array(np.array(c))  # colors setFacecolor(), set_edgecolor()

                    if self.colors is None:
                        for lines in self.ax.lines:
                            lines.remove()
                        self.ax.plot(xs=z, ys=x, zs=y, marker='.', linestyle='', c='black', markersize=s)
                    else:
                        for child in self.ax.get_children():
                            if isinstance(child, mpl3dart.Path3DCollection):
                                child.remove()
                        self.ax.scatter(xs=z, ys=x, zs=y, marker='.', cmap='jet', s=s, c=c)
                        mpl.colors._colors_full_map.cache.clear()  # avoid memory leak by clearing the cache

                    self.__draw()

            self.after(max(REFRESH_RATE, d), self.__refresh, not draw)
            return

        self.after(max(REFRESH_RATE, d), self.__refresh, False)


class ImageView(ttk.Frame):

    def __init__(self, master, source, max_refresh=REFRESH_RATE_30FPS, **kw):
        super().__init__(master, **kw)

        self.device = master
        self.canvas = tk.Canvas(self)
        self.canvas.tk_img = None
        # self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas.grid(column=0, row=0)
        self.source = source
        self.max_refresh = max_refresh
        self.refresh()

    def refresh(self):
        if self.winfo_viewable() and self.device.playing():
            img, arr, arg = self.source()
            if img is not None:
                self.canvas.img = img
                tk_img = PIL.ImageTk.PhotoImage(image=img)
                self.canvas.tk_img = tk_img
                self.canvas.config(width=tk_img.width(), height=tk_img.height())
                self.canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)
        self.after(max(int(nect_config[CONFIG][REFRESH_RATE]), int(self.max_refresh)) - 1, self.refresh)


class SelectedFileView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self._file_path = None
        self._path_label = tk.StringVar()
        self._path_label_info = tk.StringVar()
        self._no_file = tk.StringVar()
        self.update_language()

    def update_language(self):
        logger.debug("update language in selected file view")
        self._path_label_info.set(i18n.selected_file_view[FV_PATH])
        self._no_file.set(i18n.selected_file_view[FV_NO])

    def create_view(self):
        logger.debug("create view in selected file view")
        for widget in self.winfo_children():
            widget.destroy()
        if self._file_path:
            ttk.Label(self, textvariable=self._path_label_info).grid(column=0, row=0, sticky=(tk.W, tk.E))
            ttk.Label(self, textvariable=self._path_label).grid(column=1, row=0, sticky=(tk.W, tk.E))
        else:
            ttk.Label(self, textvariable=self._no_file).grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def update_selected_file(self, data: Path):
        logger.debug("update selected file in selected file view")
        self._file_path = data
        if data:
            self._path_label.set(str(self._file_path))
        self.create_view()


class ProjectInfoView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self._project_info: Optional[ConfigParser] = None
        self._project_name = None
        self._name_label_info = tk.StringVar()
        self._path_label_info = tk.StringVar()
        self._name_label = tk.StringVar()
        self._path_label = tk.StringVar()
        self._scan_label_info = tk.StringVar()
        self._reg_label_info = tk.StringVar()
        self._final_label_info = tk.StringVar()
        self._scan_label = tk.StringVar()
        self._reg_label = tk.StringVar()
        self._final_label = tk.StringVar()
        self._no_project = tk.StringVar()
        self.update_language()

    def update_language(self):
        logger.debug("update language in project info view")
        self._path_label_info.set(i18n.selected_project_view[PV_PATH])
        self._name_label_info.set(i18n.selected_project_view[PV_NAME])
        self._scan_label_info.set(i18n.selected_project_view[PV_SCAN])
        self._reg_label_info.set(i18n.selected_project_view[PV_REG])
        self._final_label_info.set(i18n.selected_project_view[PV_FINAL])
        self._no_project.set(i18n.selected_project_view[PV_NO])

    def create_view(self):
        logger.debug("create view in project info view")
        for widget in self.winfo_children():
            widget.destroy()
        if self._project_info:
            self.columnconfigure(0, weight=0)
            self.columnconfigure(1, weight=1)
            ttk.Label(self, textvariable=self._name_label_info).grid(column=0, row=0, sticky=tk.W)
            ttk.Label(self, textvariable=self._name_label).grid(column=1, row=0, sticky=(tk.W, tk.E))
            ttk.Label(self, textvariable=self._path_label_info).grid(column=0, row=1, sticky=tk.W)
            ttk.Label(self, textvariable=self._path_label).grid(column=1, row=1, sticky=(tk.W, tk.E))
            ttk.Label(self, textvariable=self._scan_label_info).grid(column=0, row=2, sticky=tk.W)
            ttk.Label(self, textvariable=self._scan_label).grid(column=1, row=2, sticky=(tk.W, tk.E))
            ttk.Label(self, textvariable=self._reg_label_info).grid(column=0, row=3, sticky=tk.W)
            ttk.Label(self, textvariable=self._reg_label).grid(column=1, row=3, sticky=(tk.W, tk.E))
            ttk.Label(self, textvariable=self._final_label_info).grid(column=0, row=4, sticky=tk.W)
            ttk.Label(self, textvariable=self._final_label).grid(column=1, row=4, sticky=(tk.W, tk.E))
        else:
            ttk.Label(self, textvariable=self._no_project).grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def __step_done_set_label(self, label, info_to_check):
        logger.debug(f"set {label} of {info_to_check} as done or not")
        if self._project_info.getboolean(info_to_check, P_DONE, fallback=False):
            label.set(i18n.selected_project_view[PV_DONE])
        else:
            label.set(i18n.selected_project_view[PV_NOT_DONE])

    def update_selected_project(self, data: ConfigParser):
        logger.debug("update selected project in project info view")
        self._project_info = data
        self._project_name = str(self._project_info.sections()[0])
        if data:
            self._path_label.set(str(self._project_info[self._project_name][P_PATH]))
            self._name_label.set(self._project_info[self._project_name][P_NAME])
            self.__step_done_set_label(self._scan_label, P_SCAN)
            self.__step_done_set_label(self._reg_label, P_REG)
            self.__step_done_set_label(self._final_label, P_FINAL)
        self.create_view()


class ScanView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.scrollFrame = ScrollFrame(self, debug=False)  # add a new scrollable frame.

        self._project_info: Optional[ConfigParser] = None
        self._exist_message_info = tk.StringVar()
        self._merge_scan_info = tk.StringVar()
        self._override_scan_info = tk.StringVar()
        self._exist_response = tk.StringVar()
        self._rot_label_info = tk.StringVar()
        self._rot_cam_info = tk.StringVar()
        self._rot_obj_info = tk.StringVar()
        self._rot_response = tk.StringVar()
        self._face_info = tk.StringVar()
        self._face_crop_info = tk.StringVar()
        self._face_detect_info = tk.StringVar()
        self._face_response = tk.StringVar()
        self._capture_info = tk.StringVar()
        self._capture_depth_info = tk.StringVar()
        self._capture_both_info = tk.StringVar()
        self._capture_response = tk.StringVar()
        self._fps_info = tk.StringVar()
        self._time_info = tk.StringVar()
        self._time_sec_info = tk.StringVar()
        self._time_man_info = tk.StringVar()
        self._sec_info = tk.StringVar()
        self._sec_response = tk.StringVar()
        self._time_response = tk.StringVar()
        self._time_sec_start = tk.StringVar()
        self._time_sec_stop = tk.StringVar()
        self._time_man_start = tk.StringVar()
        self._time_man_stop = tk.StringVar()
        self._fps_int = tk.IntVar()
        self._empty_row = []

        self._exist_message: Optional[tk.Message] = None
        self._merge_scan: Optional[ttk.Radiobutton] = None
        self._override_scan: Optional[ttk.Radiobutton] = None
        self._rot_message: Optional[tk.Message] = None
        self._rot_obj: Optional[ttk.Radiobutton] = None
        self._rot_cam: Optional[ttk.Radiobutton] = None
        self._face_message: Optional[tk.Message] = None
        self._face_detect: Optional[ttk.Radiobutton] = None
        self._face_crop: Optional[ttk.Radiobutton] = None
        self._capture_message: Optional[tk.Message] = None
        self._capture_depth: Optional[ttk.Radiobutton] = None
        self._capture_both: Optional[ttk.Radiobutton] = None
        self._time_message: Optional[tk.Message] = None
        self._time_sec: Optional[ttk.Radiobutton] = None
        self._time_man: Optional[ttk.Radiobutton] = None
        self._fps_message: Optional[tk.Message] = None
        self._sec_message: Optional[tk.Message] = None
        self._sec_start: Optional[ttk.Button] = None
        self._sec_stop: Optional[ttk.Button] = None
        self._man_start: Optional[ttk.Button] = None
        self._man_stop: Optional[ttk.Button] = None
        self._fps_scale: Optional[ttk.Scale] = None
        self._sec_entry: Optional[ttk.Entry] = None
        self._sec_progress: Optional[ttk.Progressbar] = None

        self._buttons = {
            PAS_START: lambda: self._man_start,
            PAS_STOP: lambda: self._man_stop,
            PAS_SEC_START: lambda: self._sec_start,
            PAS_SEC_STOP: lambda: self._sec_stop
        }

        self.update_language()

    def set_command(self, btn_name, command):
        logger.debug(f"scan action view set command {command} for {btn_name}")
        if btn_name in self._buttons.keys():
            button: ttk.Button = self._buttons.get(btn_name)()
            button.configure(command=command)

    def get_form(self):
        return {
            PAS_EXIST: self._exist_response.get(),
            PAS_ROT: self._rot_response.get(),
            PAS_FACE: self._face_response.get(),
            PAS_DATA: self._capture_response.get(),
            PAS_FPS: self._fps_int.get(),
            PAS_TIME: self._time_response.get(),
            PAS_SEC: self._sec_response.get()
        }

    def update_language(self):
        logger.debug("update language in scan view")
        self._exist_message_info.set(i18n.project_actions_scan[PAS_EXIST])
        self._merge_scan_info.set(i18n.project_actions_scan[PAS_MERGE])
        self._override_scan_info.set(i18n.project_actions_scan[PAS_OVERRIDE])
        self._rot_label_info.set(i18n.project_actions_scan[PAS_ROT])
        self._rot_cam_info.set(i18n.project_actions_scan[PAS_ROT_CAM])
        self._rot_obj_info.set(i18n.project_actions_scan[PAS_ROT_OBJ])
        self._face_detect_info.set(i18n.project_actions_scan[PAS_FACE_DETECT])
        self._face_crop_info.set(i18n.project_actions_scan[PAS_FACE_CROP])
        self._face_info.set(i18n.project_actions_scan[PAS_FACE])
        self._capture_info.set(i18n.project_actions_scan[PAS_DATA])
        self._capture_depth_info.set(i18n.project_actions_scan[PAS_DEPTH])
        self._capture_both_info.set(i18n.project_actions_scan[PAS_BOTH])
        self._fps_info.set(i18n.project_actions_scan[PAS_FPS])
        self._time_info.set(i18n.project_actions_scan[PAS_TIME])
        self._time_sec_info.set(i18n.project_actions_scan[PAS_SEC])
        self._sec_info.set(i18n.project_actions_scan[PAS_SEC_INFO])
        self._time_man_info.set(i18n.project_actions_scan[PAS_MANUAL])
        self._time_sec_start.set(i18n.project_actions_scan[PAS_START])
        self._time_sec_stop.set(i18n.project_actions_scan[PAS_STOP])
        self._time_man_start.set(i18n.project_actions_scan[PAS_START])
        self._time_man_stop.set(i18n.project_actions_scan[PAS_STOP])

    def create_view(self):
        logger.debug("create view in scan view")
        self._exist_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._exist_message_info,
                                              anchor="w")
        self._override_scan = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._override_scan_info,
                                              variable=self._exist_response, value=PAS_OVERRIDE)
        self._merge_scan = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._merge_scan_info,
                                           variable=self._exist_response,
                                           value=PAS_MERGE)
        self._rot_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._rot_label_info,
                                            anchor="w")
        self._rot_obj = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._rot_obj_info,
                                        variable=self._rot_response, value=PAS_ROT_OBJ)
        self._rot_cam = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._rot_cam_info,
                                        variable=self._rot_response,
                                        value=PAS_ROT_CAM)
        self._face_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._face_info, anchor="w")
        self._face_crop = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._face_crop_info,
                                          variable=self._face_response, value=PAS_FACE_CROP)
        self._face_detect = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._face_detect_info,
                                            variable=self._face_response,
                                            value=PAS_FACE_DETECT)

        self._capture_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._capture_info,
                                                anchor="w")
        self._capture_depth = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._capture_depth_info,
                                              variable=self._capture_response, value=PAS_DEPTH)
        self._capture_both = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._capture_both_info,
                                             variable=self._capture_response, value=PAS_BOTH)
        self._time_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._time_info, anchor="w")
        self._time_sec = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._time_sec_info,
                                         variable=self._time_response, value=PAS_SEC, command=self._show_sec)
        self._time_man = ttk.Radiobutton(self.scrollFrame.viewPort, textvariable=self._time_man_info,
                                         variable=self._time_response, value=PAS_MANUAL, command=self._show_man)
        self._fps_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._fps_info, anchor="w")
        self._sec_message = AutoWrapMessage(self.scrollFrame.viewPort, textvariable=self._sec_info, anchor="w")
        self._sec_start = ttk.Button(self.scrollFrame.viewPort, textvariable=self._time_sec_start, command=...)
        self._sec_stop = ttk.Button(self.scrollFrame.viewPort, textvariable=self._time_sec_stop, command=...)
        self._man_start = ttk.Button(self.scrollFrame.viewPort, textvariable=self._time_man_start, command=...)
        self._man_stop = ttk.Button(self.scrollFrame.viewPort, textvariable=self._time_man_stop, command=...)
        self._fps_scale = DiscreteStep(self.scrollFrame.viewPort, orient=tk.HORIZONTAL, showvalue=1, step=1,
                                       length=200,
                                       from_=1.0,
                                       to=30.0, variable=self._fps_int)
        self._sec_entry = ttk.Entry(self.scrollFrame.viewPort, textvariable=self._sec_response, validate='key',
                                    validatecommand=(self.master.register(check_num), '%P'))
        self._sec_progress = ttk.Progressbar(self.scrollFrame.viewPort, orient=tk.HORIZONTAL, length=200,
                                             mode='determinate')

    def _has_scan(self):
        logger.debug("check if scan has been done")
        return self._project_info.getboolean(P_SCAN, P_DONE)

    def __update_view(self):
        logger.debug("update view in scan view")
        if self._project_info:
            if self._has_scan():
                self._exist_message.grid(column=0, row=0, columnspan=5, sticky=(tk.W, tk.E))
                self._merge_scan.grid(column=1, row=1, sticky=(tk.W, tk.E))
                self._override_scan.grid(column=3, row=1, sticky=(tk.W, tk.E))
                self._exist_response.set(PAS_MERGE)
                self._empty_row.append(2)
            else:
                self._exist_message.grid_forget()
                self._merge_scan.grid_forget()
                self._override_scan.grid_forget()
                if 2 in self._empty_row:
                    self._empty_row.remove(2)

            self._rot_message.grid(column=0, row=3, columnspan=5, sticky=(tk.W, tk.E))
            self._rot_obj.grid(column=1, row=4)
            self._rot_cam.grid(column=3, row=4)
            self._rot_response.set(self._project_info.get(P_SCAN, P_SCAN_ROT, fallback=None))

            self._empty_row.append(5)

            self._face_message.grid(column=0, row=6, columnspan=5, sticky=(tk.W, tk.E))
            self._face_crop.grid(column=1, row=7)
            self._face_detect.grid(column=3, row=7)

            self._empty_row.append(8)

            self._capture_message.grid(column=0, row=9, columnspan=5, sticky=(tk.W, tk.E))
            self._capture_both.grid(column=1, row=10)
            self._capture_depth.grid(column=3, row=10)

            self._empty_row.append(11)

            self._fps_message.grid(column=0, row=12, columnspan=5, sticky=(tk.W, tk.E))
            self._fps_scale.grid(column=0, row=13, columnspan=5)

            self._empty_row.append(14)

            self._time_message.grid(column=0, row=15, columnspan=5, sticky=(tk.W, tk.E))
            self._time_sec.grid(column=1, row=16)
            self._time_man.grid(column=3, row=16)
            self._update_grid_weight()
        else:
            self._empty_row.clear()
            for widget in self.winfo_children():
                widget.destroy()
        # when packing the scrollframe, we pack scrollFrame itself (NOT the viewPort)
        self.scrollFrame.pack(side="top", fill="both", expand=True)

    def _show_man(self):
        self._sec_progress.grid_forget()
        self._sec_start.grid_forget()
        self._sec_entry.grid_forget()
        self._sec_stop.grid_forget()
        self._sec_message.grid_forget()
        if 17 not in self._empty_row:
            self._empty_row.append(17)
        self._man_start.grid(column=1, row=18)
        self._man_stop.grid(column=3, row=18)
        self._update_grid_weight()

    def _show_sec(self):
        self._sec_progress.grid_forget()
        self._man_start.grid_forget()
        self._man_stop.grid_forget()
        if 17 not in self._empty_row:
            self._empty_row.append(17)
        self._sec_entry.grid(column=2, row=18, columnspan=3)
        self._sec_message.grid(column=0, row=18, columnspan=2)
        self._sec_start.grid(column=1, row=19)
        self._sec_stop.grid(column=3, row=19)
        self._update_grid_weight()

    def _hide_sec_man(self):
        self._sec_progress.grid_forget()
        self._man_start.grid_forget()
        self._man_stop.grid_forget()
        self._sec_start.grid_forget()
        self._sec_entry.grid_forget()
        self._sec_stop.grid_forget()
        self._sec_message.grid_forget()
        if 17 in self._empty_row:
            self._empty_row.remove(17)

    def _update_grid_weight(self):
        cols, _ = self.scrollFrame.viewPort.grid_size()
        for col in range(cols):
            self.scrollFrame.viewPort.columnconfigure(col, weight=1)
        for row in self._empty_row:
            self.scrollFrame.viewPort.rowconfigure(row, minsize=20)

    def _clear_selection(self):
        self._rot_response.set("")
        self._exist_response.set("")
        self._time_response.set("")
        self._capture_response.set("")
        self._face_response.set("")
        self._sec_response.set("")

    def update_selected_project(self, data: Optional[ConfigParser] = None):
        logger.debug("update selected project in scan view")
        self._hide_sec_man()
        self._clear_selection()
        self._project_info = data
        self.__update_view()


class FinalView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self._project_info: Optional[ConfigParser] = None
        self.update_language()

    def create_view(self):
        logger.debug("update view in Final view")

    def update_language(self):
        logger.debug("update language in Final view")

    def update_selected_project(self, data=None):
        logger.debug("update selected project in Final view")
        self._project_info = data


class RegistrationView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self._project_info: Optional[ConfigParser] = None
        self._exist_label_info = tk.StringVar()
        self._exist_label: Optional[ttk.Label] = None
        self.update_language()

    def create_view(self):
        logger.debug("update view in Registration view")

    def update_language(self):
        logger.debug("update language in Registration view")

    def update_selected_project(self, data=None):
        logger.debug("update selected project in Registration view")
        self._project_info = data


class ProjectActionView(ttk.Notebook, View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self._project_info = None
        self._scan_frame = ScanView(self)
        self._registration_frame = RegistrationView(self)
        self._final_frame = FinalView(self)

    def update_language(self):
        logger.debug(f"update language in project action view")
        self.tab(self._scan_frame, text=i18n.project_actions_scan[PA_NAME])
        self.tab(self._registration_frame, text=i18n.project_actions_reg[PA_NAME])
        self.tab(self._final_frame, text=i18n.project_actions_final[PA_NAME])
        self._final_frame.update_language()
        self._scan_frame.update_language()
        self._registration_frame.update_language()

    def __tabs_change_state(self, new_state):
        logger.debug(f"set all action tabs in state: {new_state}")
        for i, item in enumerate(self.tabs()):
            self.tab(item, state=new_state)

    def create_view(self):
        logger.debug(f"create view in project action view")
        self.add(self._scan_frame, text=i18n.project_actions_scan[PA_NAME])
        self.add(self._registration_frame, text=i18n.project_actions_reg[PA_NAME])
        self.add(self._final_frame, text=i18n.project_actions_final[PA_NAME])
        self.__update_view()

    def __update_view(self):
        logger.debug(f"update view in project action view")
        if not self._project_info:
            self.__tabs_change_state(PA_DISABLED)
        else:
            self.__tabs_change_state(PA_NORMAL)
            self.select(self._scan_frame)

    def bind_controllers(self, scan_controller: Controller, registration_controller: Controller,
                         final_controller: Controller):
        logger.debug(f"bind controllers in project action view")
        self.__bind_controller(controller=scan_controller, view=self._scan_frame)
        self.__bind_controller(controller=registration_controller, view=self._registration_frame)
        self.__bind_controller(controller=final_controller, view=self._final_frame)

    @staticmethod
    def __bind_controller(controller: Controller, view: View):
        logger.debug(f"project action bind {controller.__class__} to {view.__class__}")
        controller.bind(view)

    def update_selected_project(self, data=None):
        logger.debug(f"update selected project in project action view")
        self._project_info = data
        self.__update_view()
