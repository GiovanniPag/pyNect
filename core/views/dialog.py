import tkinter as tk
from tkinter import ttk
from abc import abstractmethod
from core.util.config import logger
from core.util.constants import *
from core.util.language_resource import i18n
from core.views import check_name, ScrollFrame, ToolTip, DiscreteStep




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


class DialogYesNo(Dialog):
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


class DialogTakePictureOptions(Dialog):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.t = i18n.tk_options_dialog[I18N_TITLE]

        self.modality_label = i18n.tk_options_dialog[I18N_MODALITY]
        self.manual_radio = i18n.tk_options_dialog[I18N_MANUAL]
        self.manual_tip = i18n.tk_options_dialog[I18N_MANUAL_TIP]
        self.automatic_radio = i18n.tk_options_dialog[I18N_AUTOMATIC]
        self.automatic_tip = i18n.tk_options_dialog[I18N_AUTOMATIC_TIP]
        self.frames_label = i18n.tk_options_dialog[I18N_FRAMES]
        self.response_value = None
        self.mode_var = tk.StringVar()
        self.mode_var.set(I18N_MANUAL)
        self.frames_var = tk.IntVar()
        self.frames_var.set(20)

    def ask_value(self):
        logger.debug(f"Calibrate sensor Dialog ask value: {self.mode_var.get()}, {self.frames_var.get()}")
        self.response_value = {I18N_MODALITY: self.mode_var.get(), I18N_FRAMES: self.frames_var.get()}
        return self.response_value

    def dismiss_method(self):
        logger.debug("Calibrate sensor Dialog dismiss method")
        self.response_value = None

    def create_view(self):
        logger.debug("Calibrate sensor Dialog create view method")
        self.title(self.t)
        self.resizable(False, False)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        tk.Label(self, image=FULL_QUESTION_ICON) \
            .grid(row=0, column=0, rowspan=2, pady=(7, 0), padx=(7, 7), sticky="e")
        ttk.Label(self, text=self.modality_label, font="bold") \
            .grid(row=0, column=1, columnspan=2, pady=(7, 7), padx=(7, 7), sticky="w")
        # radio buttons modality
        r_manual = ttk.Radiobutton(self, text=self.manual_radio, variable=self.mode_var, value=I18N_MANUAL)
        r_manual.grid(row=1, column=1, columnspan=1, pady=(7, 7), padx=(7, 7), sticky="we")
        r_auto = ttk.Radiobutton(self, text=self.automatic_radio, variable=self.mode_var, value=I18N_AUTOMATIC)
        r_auto.grid(row=1, column=2, columnspan=1, pady=(7, 7), padx=(7, 7), sticky="we")
        # radio buttons tip
        ToolTip(r_manual, text=self.manual_tip)
        ToolTip(r_auto, text=self.automatic_tip)
        # frame slider
        ttk.Label(self, text=self.frames_label, font="bold") \
            .grid(row=2, column=1, columnspan=2, pady=(7, 7), padx=(7, 7), sticky="we")
        DiscreteStep(self, orient=tk.HORIZONTAL, showvalue=1, step=1,
                     length=200, from_=15.0, to=60.0, variable=self.frames_var)\
            .grid(row=3, column=1, columnspan=3, padx=(7, 7), sticky="we")

        # buttons
        ttk.Button(self, text=i18n.dialog_buttons[I18N_CONFIRM_BUTTON], command=self.close) \
            .grid(row=4, column=3, pady=(7, 7), padx=(7, 7), sticky="e")

        ttk.Button(self, text=i18n.dialog_buttons[I18N_CANCEL_BUTTON], command=self.dismiss) \
            .grid(row=4, column=2, pady=(7, 7), padx=(7, 7), sticky="e")


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
