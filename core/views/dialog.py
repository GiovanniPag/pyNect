import tkinter as tk
from tkinter import ttk
from abc import abstractmethod
from core.util.config import logger
from core.util.constants import *
from core.util.language_resource import i18n
from core.views import check_name


class Dialog(tk.Toplevel):
    def show(self):
        logger.debug(f"show dialog")
        self.create_view()
        self.protocol("WM_DELETE_WINDOW", self.dismiss)  # intercept close button
        self.transient(self.master)  # dialog window is related to main
        self.wait_visibility()  # can't grab until window appears, so we wait
        self.grab_set()  # ensure all input goes to our window
        self.master.wait_window(self)  # block until window is destroyed
        return self.ask_value()

    @abstractmethod
    def ask_value(self):
        raise NotImplementedError

    @abstractmethod
    def dismiss_method(self):
        raise NotImplementedError

    @abstractmethod
    def create_view(self):
        raise NotImplementedError

    def close(self):
        logger.debug("Close Dialog")
        self.grab_release()
        self.destroy()

    def dismiss(self):
        logger.debug("Dismiss Dialog")
        self.dismiss_method()
        self.close()


class DialogProjectOptions(Dialog):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.t = i18n.p_options_dialog[I18N_TITLE]
        self.name_var = tk.StringVar()
        self.name_var.set("")
        self.back = False
        self.name_label = i18n.p_options_dialog[I18N_NAME]
        self.name_tip = i18n.p_options_dialog[I18N_NAME_TIP]

    def ask_value(self):
        logger.debug("Project Options Dialog ask value: " + self.name_var.get())
        if self.back:
            value = i18n.dialog_buttons[I18N_BACK_BUTTON]
        else:
            value = self.name_var.get()
        return value

    def dismiss_method(self):
        logger.debug("Project Options Dialog dismiss method")
        self.name_var.set("")

    def go_back(self):
        logger.debug("Project Options Dialog Back method")
        self.back = True
        self.close()

    def create_view(self):
        logger.debug("Project Options Dialog create view method")
        self.title(self.t)
        self.resizable(False, False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        tk.Label(self, image=FULL_QUESTION_ICON) \
            .grid(row=0, column=0, rowspan=2, pady=(7, 0), padx=(7, 7), sticky="e")
        ttk.Label(self, text=self.name_label, font="bold") \
            .grid(row=0, column=1, columnspan=1, pady=(7, 7), padx=(7, 7), sticky="w")
        # entry
        entry = ttk.Entry(self, textvariable=self.name_var, validate='key',
                          validatecommand=(self.master.register(check_name), '%P'))
        entry.bind("<Return>", lambda event: self.close())
        entry.grid(row=0, column=2, columnspan=3, pady=(7, 7), padx=(7, 7), sticky="we")
        ttk.Label(self, text=self.name_tip, background="red", wraplength=400) \
            .grid(row=1, column=1, columnspan=4, padx=(7, 7), sticky="we")
        ttk.Button(self, text=i18n.dialog_buttons[I18N_CONFIRM_BUTTON], command=self.close) \
            .grid(row=2, column=2, pady=(7, 7), padx=(7, 7), sticky="e")
        ttk.Button(self, text=i18n.dialog_buttons[I18N_BACK_BUTTON], command=self.go_back) \
            .grid(row=2, column=3, pady=(7, 7), padx=(7, 7), sticky="e")
        ttk.Button(self, text=i18n.dialog_buttons[I18N_CANCEL_BUTTON], command=self.dismiss) \
            .grid(row=2, column=4, pady=(7, 7), padx=(7, 7), sticky="e")
        entry.focus_set()


class DialogMessage(Dialog):
    def __init__(self, master, title, message, detail, icon=INFORMATION_ICON):
        super().__init__(master)
        self.master = master
        self.icon = icon
        self.t = title
        self.message = message
        self.detail = detail

    def ask_value(self):
        pass

    def dismiss_method(self):
        pass

    def create_view(self):
        logger.debug("Message Dialog create view method")
        self.title(self.t)
        self.resizable(False, False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        tk.Label(self, image=BASENAME_ICON+self.icon) \
            .grid(row=0, column=0, rowspan=2, pady=(7, 0), padx=(7, 7), sticky="e")
        ttk.Label(self, text=self.message, font="bold") \
            .grid(row=0, column=1, columnspan=2, pady=(7, 7), padx=(7, 7), sticky="w")
        ttk.Label(self, text=self.detail).grid(row=1, column=1, columnspan=2, pady=(7, 7), padx=(7, 7), sticky="w")
        ttk.Button(self, text=i18n.dialog_buttons[I18N_BACK_BUTTON], command=self.dismiss) \
            .grid(row=2, column=2, pady=(7, 7), padx=(7, 7), sticky="e")
