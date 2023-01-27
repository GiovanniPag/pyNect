import platform
import re
import tkinter as tk
import tkinter.ttk as ttk
from abc import abstractmethod
from enum import Enum, auto
from math import floor
from pathlib import Path

from core import logger, CONFIG, CALIBRATION_PATH, F_RGB, F_IR, F_RESULTS
from core.util import nect_config, check_if_folder_exist


class View(ttk.Frame):
    @abstractmethod
    def create_view(self):
        raise NotImplementedError

    @abstractmethod
    def update_language(self):
        raise NotImplementedError


def check_name(new_val):
    logger.debug(f"validate project name {new_val}")
    return re.match('^[a-zA-Z0-9-_]*$', new_val) is not None and len(new_val) <= 50


def check_num(new_val):
    logger.warning(f"validate only int {new_val}")
    return re.match('^[0-9]*$', new_val) is not None and len(new_val) <= 3


def sizeof_fmt(num, suffix="B"):
    logger.debug(f"format {num} in bytes")
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def check_if_sensor_calibrated(device_serial: str):
    calibration_folder = Path(nect_config[CONFIG][CALIBRATION_PATH]) / device_serial
    check = check_if_folder_exist(calibration_folder) and check_if_folder_exist(
        calibration_folder / F_RGB) and check_if_folder_exist(
        calibration_folder / F_IR) and check_if_folder_exist(calibration_folder / F_RESULTS)
    return check


class GeometryManager(Enum):
    GRID = auto()
    PACK = auto()


class AutoScrollbar(ttk.Scrollbar):
    def __init__(self, master, geometry: GeometryManager = GeometryManager.GRID, column_grid=1, row_grid=0,
                 **kwargs):
        super().__init__(master, **kwargs)
        self.geometry = geometry
        self.column = column_grid
        self.row = row_grid

    """Create a scrollbar that hides itself if it's not needed."""

    def set(self, lo, hi):
        logger.debug(f"hide scrollbar if not needed")
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            if self.geometry is GeometryManager.GRID:
                self.grid_forget()
            else:
                self.pack_forget()
        else:
            if self.cget("orient") == tk.HORIZONTAL:
                if self.geometry is GeometryManager.GRID:
                    self.grid(column=self.column, row=self.row, sticky=(tk.W, tk.E))
                else:
                    self.pack(fill=tk.X, side=tk.BOTTOM)
            else:
                if self.geometry is GeometryManager.GRID:
                    self.grid(column=self.column, row=self.row, sticky=(tk.N, tk.S))
                else:
                    self.pack(fill=tk.Y, side=tk.RIGHT)
        tk.Scrollbar.set(self, lo, hi)

    def place(self, **kw):
        raise tk.TclError("cannot use place with this widget")


class DiscreteStep(tk.Scale):
    def __init__(self, master=None, step=1, **kw):
        super().__init__(master, **kw)
        self.step = floor(step)
        self.variable: tk.IntVar = kw.get("variable")
        self.value_list = list(range(int(kw.get("from_")), int(kw.get("to") + 1), self.step))
        self.configure(command=self.value_check)

    def value_check(self, value):
        new_value = min(self.value_list, key=lambda x: abs(x - float(value)))
        self.variable.set(value=new_value)


class AutoWrapMessage(tk.Message):
    def __init__(self, master, margin=8, **kwargs):
        super().__init__(master, **kwargs)
        self.margin = margin
        self.bind("<Configure>", lambda event: event.widget.configure(width=event.width - self.margin))


class ScrollFrame(tk.Frame):
    def __init__(self, master, debug=False):
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, borderwidth=0)
        self.viewPort = tk.Frame(self.canvas)
        if debug:
            self.viewPort.configure(background="#bbaaee")
        self.vsb = AutoScrollbar(self, geometry=GeometryManager.GRID, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.viewPort, anchor="nw", tags="self.viewPort")

        self.viewPort.bind("<Configure>", self.on_frame_configure)
        # bind an event whenever the size of the viewPort frame changes.
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        # bind an event whenever the size of the canvas frame changes.
        self.viewPort.bind('<Enter>', self.on_enter)
        # bind wheel events when the cursor enters the control
        self.viewPort.bind('<Leave>', self.on_leave)
        # unbind wheel events when the cursor leaves the control
        self.on_frame_configure(None)
        # perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def on_frame_configure(self, _):
        """ Reset the scroll region to encompass the inner frame """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # whenever the size of the frame changes, alter the scroll region respectively.

    def on_canvas_configure(self, event):
        """ Reset the canvas window to encompass inner frame when required """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        # whenever the size of the canvas changes alter the window region respectively.

    def on_mouse_wheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def on_enter(self, event):
        # bind wheel events when the cursor enters the control
        if self.vsb.winfo_ismapped():
            if platform.system() == 'Linux':
                self.canvas.bind_all("<Button-4>", self.on_mouse_wheel)
                self.canvas.bind_all("<Button-5>", self.on_mouse_wheel)
            else:
                self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def on_leave(self, event):
        # unbind wheel events when the cursor leaves the control
        if platform.system() == 'Linux':
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")


class ToolTip:
    """
    create a tooltip for a given widget
    """

    def __init__(self, widget, bg='#FFFFEA', pad=(5, 3, 5, 3), text='widget info',
                 wait_time=400, wrap_length=250):
        self.wait_time = wait_time  # milliseconds
        self.wrap_length = wrap_length  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None

    def on_enter(self, _=None):
        self.schedule()

    def on_leave(self, _=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.wait_time, self.showtip)

    def unschedule(self):
        old_id = self.id
        self.id = None
        if old_id:
            self.widget.after_cancel(old_id)

    @staticmethod
    def __tip_pos_calculator(widget_, label_, tip_delta=(10, 5), pad_=(5, 3, 5, 3)):
        s_width, s_height = widget_.winfo_screenwidth(), widget_.winfo_screenheight()
        width, height = (pad_[0] + label_.winfo_reqwidth() + pad_[2],
                         pad_[1] + label_.winfo_reqheight() + pad_[3])
        mouse_x, mouse_y = widget_.winfo_pointerxy()
        x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
        x2, y2 = x1 + width, y1 + height
        x_delta = x2 - s_width
        if x_delta < 0:
            x_delta = 0
        y_delta = y2 - s_height
        if y_delta < 0:
            y_delta = 0
        if (x_delta, y_delta) != (0, 0):
            if x_delta:
                x1 = mouse_x - tip_delta[0] - width
            if y_delta:
                y1 = mouse_y - tip_delta[1] - height
        if y1 < 0:  # out on the top
            y1 = 0
        return x1, y1

    def showtip(self):
        # creates a top level window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        win = tk.Frame(self.tw, background=self.bg, borderwidth=0)
        label = ttk.Label(win, text=self.text, justify=tk.LEFT, background=self.bg,
                          relief=tk.SOLID, borderwidth=0, wraplength=self.wrap_length)
        label.grid(padx=(self.pad[0], self.pad[2]), pady=(self.pad[1], self.pad[3]), sticky=tk.NSEW)
        win.grid()
        x, y = self.__tip_pos_calculator(self.widget, label)
        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hidetip(self):
        old_tw = self.tw
        self.tw = None
        if old_tw:
            old_tw.destroy()
