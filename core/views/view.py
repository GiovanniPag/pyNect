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
from core.views import View, AutoScrollbar

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

    def __init__(self, master, switch_func=None):
        super().__init__(master)
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
        new_fr.pack(fill=tk.BOTH, expand=True)
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
            },
            M_60FPS: {
                M_MASTER: self.menu_sensor_fps,
                M_RADIO: True,
                M_VARIABLE: self.refresh_rate,
                M_VALUE: REFRESH_RATE_60FPS,
                M_INDEX: 3
            },
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
        self.add_cascade_item(menu_name=M_FPS, menu_to_add=self.menu_sensor_fps, info=i18n.menu_sensor_fps)
        # menu_sensor_fps items
        self.add_command_item(cmd_name=M_10FPS, info=i18n.menu_sensor_fps_10)
        self.add_command_item(cmd_name=M_15FPS, info=i18n.menu_sensor_fps_15)
        self.add_command_item(cmd_name=M_30FPS, info=i18n.menu_sensor_fps_30)
        self.add_command_item(cmd_name=M_60FPS, info=i18n.menu_sensor_fps_60)
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
        self.update_command_or_cascade(name=M_FPS, info_updated=i18n.menu_sensor_fps)
        # menu_sensor_fps items
        self.update_command_or_cascade(name=M_10FPS, info_updated=i18n.menu_sensor_fps_10)
        self.update_command_or_cascade(name=M_15FPS, info_updated=i18n.menu_sensor_fps_15)
        self.update_command_or_cascade(name=M_30FPS, info_updated=i18n.menu_sensor_fps_30)
        self.update_command_or_cascade(name=M_60FPS, info_updated=i18n.menu_sensor_fps_60)

    def add_cascade_item(self, menu_name, menu_to_add, info):
        logger.debug(f"add cascade item {menu_to_add} to {menu_name} with info {info}")
        self.__menu_names[menu_name][M_MASTER].add_cascade(menu=menu_to_add, label=info.get(M_LABEL, ""),
                                                           underline=info.get(M_UNDERLINE, -1),
                                                           state=info.get(M_DEFAULT_STATE, M_STATE_NORMAL))

    def add_command_item(self, cmd_name, info):
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


class SensorView(TabbedView):

    def __init__(self, master):
        super().__init__(master)
        self.master = master

    def update_language(self):
        logger.debug("update language in sensor view")
        if self.current_frame:
            self.current_frame.update_language()

    def create_view(self):
        pass


class DeviceView(TabbedView):

    def create_view(self):
        logger.debug("create view in device view")
        self.pack(fill=tk.BOTH, expand=True)
        # color = ImageView(self, lambda: self.get_image_color(), REFRESH_RATE_15FPS)
        color = ImageView(self, lambda: self.get_image_color())
        self.add(i18n.device_view_frames[D_RGB], color, D_RGB)

        ir = ImageView(self, lambda: self.get_image_ir())
        self.add(i18n.device_view_frames[D_IR], ir, D_IR)

        depth = ImageView(self, lambda: self.get_image_depth())
        self.add(i18n.device_view_frames[D_DEPTH], depth, D_DEPTH)

        self.refresh()

    def update_language(self):
        logger.debug("update language in device view")
        self.i18n_frame_names = i18n.device_view_frames
        super().update_language()

    def __init__(self, master, free_nect, serial):
        super().__init__(master)

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
            self.frames = self._listener.waitForNewFrame()
        self.after(int(nect_config[CONFIG][REFRESH_RATE]), self.refresh)

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
        return self.master.master.devices.index(self._serial)


class ImageView(ttk.Frame):

    def __init__(self, master, source, max_refresh=REFRESH_RATE_60FPS):
        super().__init__(master)

        self.device = master
        self.canvas = tk.Canvas(self)
        self.canvas.tk_img = None
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
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
        self.after(min(int(nect_config[CONFIG][REFRESH_RATE]), int(self.max_refresh)) - 1, self.refresh)


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
        if self._project_info.getboolean(info_to_check, P_DONE, False):
            label.set(i18n.selected_project_view[PV_DONE])
        else:
            label.set(i18n.selected_project_view[PV_NOT_DONE])

    def update_selected_project(self, data):
        logger.debug("update selected project in project info view")
        self._project_info = data
        if data:
            self._path_label.set(str(self._project_info[P_PATH]))
            self._name_label.set(self._project_info[P_NAME])
            self.__step_done_set_label(self._scan_label, P_SCAN)
            self.__step_done_set_label(self._reg_label, P_REG)
            self.__step_done_set_label(self._final_label, P_FINAL)
        self.create_view()


class ScanView(View):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self._project_info: Optional[ConfigParser] = None
        self._exist_label_info = tk.StringVar()
        self._exist_label: Optional[ttk.Label] = None
        self.update_language()

    def update_language(self):
        logger.debug("update language in scan view")
        self._exist_label_info.set(i18n.project_actions_scan[PAS_EXIST])

    def create_view(self):
        logger.debug("create view in scan view")
        self._exist_label = ttk.Label(self, textvariable=self._exist_label_info)

    def _has_scan(self):
        logger.debug("check if scan has been done")
        return self._project_info.getboolean(P_SCAN, P_DONE)

    def __update_view(self):
        logger.debug("update view in scan view")
        if self._has_scan():
            self._exist_label.grid(column=0, row=0, sticky=(tk.W, tk.E))
        else:
            self._exist_label.grid_forget()

    def update_selected_project(self, data=None):
        logger.debug("update selected project in scan view")
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
