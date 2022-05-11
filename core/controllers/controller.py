from abc import ABC, abstractmethod
from datetime import datetime, timezone

from tkinter import filedialog

from core import open_message_dialog
from core.controllers import Controller
from core.models import store_open_project, add_to_open_projects, create_project_folder
from core.util import open_guide, open_log_folder, check_if_folder_exist, check_if_is_project
from core.util.config import logger, nect_config, change_fps
from core.util.constants import *
from core.util.language_resource import i18n
from core.views import sizeof_fmt
from core.views.dialog import DialogProjectOptions
from core.views.view import MenuBar, ProjectTreeView, SensorView, DeviceView, SelectedFileView, \
    ProjectInfoView, ProjectActionView, ScanView, FinalView, RegistrationView


class MenuController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.master = master
        self.view = None

    def bind(self, v: MenuBar):
        logger.debug("bind in menu controller")
        self.view = v
        self.view.create_view()
        self.view.refresh_rate.set(nect_config[CONFIG][REFRESH_RATE])
        self.view.language.set(nect_config[CONFIG][LANGUAGE])
        # bind command to menu items
        logger.debug("menu controller bind commands")
        # menu help
        self.view.update_command_or_cascade(M_ABOUT, {M_COMMAND: lambda: open_message_dialog(self.master, "about")})
        self.view.update_command_or_cascade(M_LOGS, {M_COMMAND: lambda: open_log_folder()})
        self.view.update_command_or_cascade(M_GUIDE, {M_COMMAND: lambda: open_guide()})
        # menu help language
        self.view.update_command_or_cascade(M_IT, {M_COMMAND: lambda: self.language_change(M_IT)})
        self.view.update_command_or_cascade(M_EN, {M_COMMAND: lambda: self.language_change(M_EN)})
        # menu fps
        if not self.master.has_connected_device():
            self.view.update_command_or_cascade(M_FPS, {M_STATE: "disabled"}, update_state=True)
        else:
            self.view.update_command_or_cascade(M_10FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_10FPS)})
            self.view.update_command_or_cascade(M_15FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_15FPS)})
            self.view.update_command_or_cascade(M_30FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_30FPS)})
            self.view.update_command_or_cascade(M_60FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_60FPS)})
        # menu file
        self.view.update_command_or_cascade(M_NEW, {M_COMMAND: lambda: self.create_new_project()})
        self.view.update_command_or_cascade(M_OPEN, {M_COMMAND: lambda: self.open_project()})
        self.view.update_command_or_cascade(M_EXIT, {M_COMMAND: lambda: self.close_app()})

    def open_project(self):
        logger.debug("open project")
        opening = True
        while opening:
            path = self.choose_folder()
            if path != "":
                logger.debug("chosen project path: " + str(path))
                is_project, metadata = check_if_is_project(path, path.name)
                if is_project:
                    if str(path) in self.master.open_projects:
                        logger.warning("project is already open")
                        open_message_dialog(self.master, "project_already_open", ERROR_ICON)
                    else:
                        logger.debug("project opened successfully")
                        self.master.add_project(metadata[path.name])
                        add_to_open_projects(path)
                        open_message_dialog(self.master, "project_open_success")
                        logger.debug("menu_bar <<UpdateTree>> event generation")
                        self.master.event_generate("<<UpdateTree>>")
                        opening = False
                else:
                    logger.warning("selected folder is not a project")
                    open_message_dialog(self.master, "not_project", ERROR_ICON)
            else:
                opening = False

    def create_new_project(self):
        logger.debug("create new project")
        creating = True
        while creating:
            path = self.choose_folder()
            if path != "":
                logger.debug("chosen project path: " + str(path))
                name = self.ask_project_name()
                if name != i18n.dialog_buttons[I18N_BACK_BUTTON]:
                    if name != "":
                        logger.debug("chosen project name: " + name)
                        exist = check_if_folder_exist(path, name)
                        if not exist:
                            create_project_folder(path / name)
                            metadata = store_open_project(path, name)
                            self.master.add_project(metadata[name])
                            logger.debug("menu_bar <<UpdateTree>> event generation")
                            self.master.event_generate("<<UpdateTree>>")
                            logger.debug("project created successfully")
                        else:
                            logger.debug("invalid name")
                            open_message_dialog(self.master, "project_exist", ERROR_ICON)
                    creating = False
                else:
                    logger.debug("go back to choose path")
            else:
                creating = False

    def close_app(self):
        logger.debug("close app")
        self.master.destroy()

    def ask_project_name(self):
        logger.debug("open p_options dialog, ask project name")
        p_name = DialogProjectOptions(master=self.master).show()
        return p_name

    def choose_folder(self):
        logger.debug("choose directory")
        dir_name = filedialog.askdirectory(initialdir=nect_config[CONFIG][PROJECTS_FOLDER], mustexist=True,
                                           parent=self.master, title=i18n.choose_folder_dialog[I18N_TITLE])
        if dir_name != ():
            dir_name = Path(dir_name)
            logger.debug("chosen path: " + str(dir_name))
            return dir_name
        else:
            logger.debug("abort choosing")
            return ""

    def language_change(self, language):
        changed = i18n.change_language(language)
        if changed:
            logger.debug("menu_bar <<LanguageChange>> event generation")
            self.master.event_generate("<<LanguageChange>>")

    def fps_change(self, fps):
        changed = change_fps(fps)
        if changed:
            logger.debug("menu_bar <<FPSChange>> event generation")
            self.master.event_generate("<<FPSChange>>")


class DeviceController(Controller):

    def __init__(self, master=None) -> None:
        super().__init__()
        self.master = master
        self.view = None

    def bind(self, v: DeviceView):
        logger.debug("bind in device controller")
        self.view = v
        logger.debug("sensor view add all device views")
        self.view.i18n_frame_names = i18n.device_view_frames
        self.view.create_view()


class SensorController(Controller):

    def __init__(self, master=None) -> None:
        super().__init__()
        self.master = master
        self._views = []
        self._controllers = []
        self.view = None

    def bind(self, v: SensorView):
        logger.debug("bind in sensor controller")
        self.view = v
        logger.debug("sensor view bind switch function")
        self.view.switch_func = lambda old, new: self.switch(old, new)
        logger.debug("sensor view add all device views")
        self.view.create_view()
        for serial in self.master.devices:
            self._views.append(DeviceView(self.view, self.master.fn, serial))
            self._controllers.append(DeviceController(self.master))
            self._controllers[-1].bind(self._views[-1])
            self.view.add(serial, self._views[-1], serial)

    @staticmethod
    def switch(old_dev, new_dev):
        logger.debug(f"switch {old_dev} with {new_dev}")
        if old_dev is not None and new_dev is not None:
            if type(old_dev) == DeviceView and type(new_dev) == DeviceView:
                if old_dev != new_dev:
                    old_dev.close()
                if not new_dev.opened():
                    new_dev.open()
                    new_dev.play()
                elif not new_dev.playing():
                    new_dev.play()
                else:
                    new_dev.stop()


class TreeController(Controller):

    def __init__(self, master=None) -> None:
        super().__init__()
        self.master = master
        self.view: ProjectTreeView or None = None
        self.__last_selected_project = None
        self.__last_selected_file = None
        self.__tree_nodes = {}

    def get_last_selected_project(self):

        return self.__last_selected_project[P_PATH]

    def get_last_selected_file(self):
        return self.__last_selected_file[P_PATH]

    def bind(self, v: ProjectTreeView):
        logger.debug("bind in tree view")
        self.view = v
        self.view.create_view()
        logger.debug("Tree_view controller bind commands")
        # self.view.bind("<ButtonPress>", self.schedule_update)
        self.view.bind('<<TreeviewSelect>>', self.select_file)
        self.view.bind('<Double-Button-1>', self.select_project)
        self.update_tree_view(populate_root=True)

    def select_project(self, _):
        logger.debug(f"tree view double click: {_}")
        selection = self.view.selection()
        if selection:
            selected_item_id = selection[0]
            selected_item = self.view.item(selected_item_id)
            logger.debug(f"selected project of item: {selected_item}")
            selected_file = [node for _, node in self.__tree_nodes.items() if node[P_INDEX] == selected_item_id][0]
            self.__last_selected_project = self.get_root_node(selected_file)
            self.master.event_generate("<<selected_project>>")
        else:
            logger.debug("tree view double click: no selected project")

    def get_root_node(self, start_node):
        root_node = start_node
        while root_node[T_PARENT] is not None:
            root_node = [node for _, node in self.__tree_nodes.items() if node[P_INDEX] == root_node[T_PARENT]][0]
        logger.debug(f"root node of {start_node} is: {root_node}")
        return root_node

    def select_file(self, _):
        selected_item_id = self.view.selection()[0]
        selected_item = self.view.item(selected_item_id)
        logger.debug(f"selected item {selected_item}")
        selected_file = [node for _, node in self.__tree_nodes.items() if node[P_INDEX] == selected_item_id][0]
        logger.debug(f"selected tree node {selected_file}")
        self.__last_selected_file = selected_file
        self.master.event_generate("<<selected_file>>")

    def schedule_update(self, _=None):
        logger.debug("Tree_view controller event to update view")
        self.update_tree_view()

    def add_or_update_node(self, path, parent=None, index=None):
        if path not in self.__tree_nodes:
            logger.debug(f"add node: {path}")
            self.__tree_nodes[path] = {
                P_INDEX: index,
                P_PATH: path,
                T_PARENT: parent,
                T_TEXT: path.name,
                T_FILE_TYPE: path.suffix,
                T_VALUES: {
                    T_NAME: path.name,
                    T_SIZE: sizeof_fmt(path.stat().st_size) if path.is_file() else "--",
                    T_MODIFIED: datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime(
                        '%Y-%m-%d %H:%M')
                }
            }
        else:
            logger.debug(f"update node: {path}: {self.__tree_nodes[path]}")
            if index is not None:
                self.__tree_nodes[path][P_INDEX] = index
            if parent is not None:
                self.__tree_nodes[path][T_PARENT] = parent
            self.__tree_nodes[path][T_VALUES] = {
                    T_NAME: path.name,
                    T_SIZE: sizeof_fmt(path.stat().st_size) if path.is_file() else "--",
                    T_MODIFIED: datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime(
                        '%Y-%m-%d %H:%M')
            }

    def populate_root_nodes(self):
        logger.debug("Tree_view controller populate root nodes: fetch open projects")
        data = self.master.open_projects
        for project in data:
            logger.debug(
                f"Tree_view controller populate root nodes: for each project add to tree_nodes and view : {project}")
            project_data = data[project]
            p_path = Path(project_data[P_PATH])
            self.add_or_update_node(path=p_path)
            self.add_or_update_tree_view_node(self.__tree_nodes[p_path])

    def update_tree_nodes(self):
        logger.debug("Tree_view controller update tree nodes: for each root node recursive update tree")
        for root_node in {k: v for k, v in self.__tree_nodes.items() if v[T_PARENT] is None}:
            self.__recursive_update_tree_nodes(self.__tree_nodes[root_node])

    def __recursive_update_tree_nodes(self, node_to_explore):
        for p in Path(node_to_explore[P_PATH]).glob('*'):
            self.add_or_update_node(path=p, parent=node_to_explore[P_INDEX])
            self.add_or_update_tree_view_node(self.__tree_nodes[p])
            if p.is_dir():
                self.__recursive_update_tree_nodes(self.__tree_nodes[p])

    def update_tree_view(self, populate_root=False):
        logger.debug(f"Tree_view controller update view, populate_root = {populate_root}")
        if populate_root:
            self.populate_root_nodes()
        self.update_tree_nodes()

    def add_or_update_tree_view_node(self, node_data, index=T_END):
        logger.debug(f"Tree_view controller add or update node: {node_data}, at index: {index}")
        data_values = node_data[T_VALUES]
        if node_data[P_INDEX] is None:
            node_data[P_INDEX] = self.view.insert(parent="" if node_data[T_PARENT] is None else node_data[T_PARENT],
                                                  index=index,
                                                  text=data_values[T_NAME],
                                                  values=[data_values[T_SIZE],
                                                          data_values[T_MODIFIED]])
        else:
            self.view.item(node_data[P_INDEX], text=data_values[T_NAME],
                           values=[data_values[T_SIZE],
                                   data_values[T_MODIFIED]])


class SelectedFileController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: SelectedFileView):
        self.view = v
        self.view.create_view()

    def update_view(self, data: Path):
        self.view.update_selected_file(data)


class SelectedProjectController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: ProjectInfoView):
        self.view = v
        self.view.create_view()

    def update_view(self, data):
        self.view.update_selected_project(data)


class ScanController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: ScanView):
        self.view = v
        self.view.create_view()

    def update_selected(self, data):
        self.view.update_selected_project(data)


class FinalController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: FinalView):
        self.view = v
        self.view.create_view()

    def update_selected(self, data):
        self.view.update_selected_project(data)


class RegistrationController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: RegistrationView):
        self.view = v
        self.view.create_view()

    def update_selected(self, data):
        self.view.update_selected_project(data)


class ProjectActionController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master
        self._scan_controller = ScanController(master)
        self._registration_controller = RegistrationController(master)
        self._final_controller = FinalController(master)

    def bind(self, v: ProjectActionView):
        self.view = v
        self.view.create_view()
        self.view.bind_controllers(scan_controller=self._scan_controller,
                                   registration_controller=self._registration_controller,
                                   final_controller=self._final_controller)

    def select_project(self, data):
        self.view.update_selected_project(data)
        self._scan_controller.update_selected(data)
        self._registration_controller.update_selected(data)
        self._final_controller.update_selected(data)
