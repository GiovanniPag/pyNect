import re
import tkinter as tk
import tkinter.ttk as ttk
from abc import abstractmethod

from core import logger


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


def sizeof_fmt(num, suffix="B"):
    logger.debug(f"format {num} in bytes")
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


class AutoScrollbar(ttk.Scrollbar):
    def __init__(self, master, column_grid, row_grid, **kwargs):
        super().__init__(master, **kwargs)
        self.column = column_grid
        self.row = row_grid

    """Create a scrollbar that hides itself if it's not needed."""
    def set(self, lo, hi):
        logger.debug(f"hide scrollbar if not needed")
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_forget()
        else:
            if self.cget("orient") == tk.HORIZONTAL:
                self.grid(column=self.column, row=self.row, sticky=(tk.W, tk.E))
            else:
                self.grid(column=self.column, row=self.row, sticky=(tk.N, tk.S))
        tk.Scrollbar.set(self, lo, hi)


class ToolTip:
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, bg='#FFFFEA', pad=(5, 3, 5, 3), text='widget info',
                 wait_time=400, wrap_length=250):
        self.wait_time = wait_time     # milliseconds
        self.wrap_length = wrap_length   # pixels
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
