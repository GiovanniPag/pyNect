from datetime import datetime, timezone
import cv2 as open_cv
from tkinter import filedialog

import numpy as np

from core import open_message_dialog, open_error_dialog
from core.controllers import Controller
from core.models import store_open_project, add_to_open_projects, create_project_folder, create_calibration_folder, \
    restore_calibration_backup, remove_calibration_backup
from core.util import open_guide, open_log_folder, check_if_folder_exist, check_if_is_project, is_int
from core.util.config import logger, nect_config, change_fps, RGB_IMAGE_SIZE_PARSED, IR_IMAGE_SIZE_PARSED
from core.util.constants import *
from core.util.language_resource import i18n
from core.views import sizeof_fmt, check_if_sensor_calibrated
from core.views.dialog import DialogProjectOptions, DialogTakePictureOptions, DialogAsk
from core.views.view import MenuBar, ProjectTreeView, SensorView, DeviceView, SelectedFileView, ProjectInfoView, \
    ProjectActionView, ScanView, FinalView, RegistrationView


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
            self.view.update_command_or_cascade(M_CALIBRATE, {M_STATE: "disabled"}, update_state=True)
            self.view.update_command_or_cascade(M_FPS, {M_STATE: "disabled"}, update_state=True)
        else:
            self.view.update_command_or_cascade(M_10FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_10FPS)})
            self.view.update_command_or_cascade(M_15FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_15FPS)})
            self.view.update_command_or_cascade(M_30FPS, {M_COMMAND: lambda: self.fps_change(REFRESH_RATE_30FPS)})
            self.view.add_sensors()
            for serial in self.master.devices:
                self.view.update_command_or_cascade(serial, {M_COMMAND: lambda: self.calibrate(serial)})
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
                        self.master.add_project(metadata, path.name)
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

    def calibrate(self, device_to_calibrate):
        logger.debug(f"calibrate sensor: {device_to_calibrate}")
        calibrate = I18N_YES_BUTTON
        if check_if_sensor_calibrated(device_to_calibrate):
            calibrate = self.ask_override_calibration()
        if calibrate == I18N_YES_BUTTON:
            configs = self.get_take_pictures_configs()
            if configs is not None:
                # unset mode, switch view
                self.master.switch_sensor(device_to_calibrate)
                # create folder and start taking pictures
                create_calibration_folder(device_to_calibrate, reset=True, backup=True)
                self.master.take_pictures(data=configs, calibration=True)
        elif calibrate == I18N_ONLY_CALIBRATION_BUTTON:
            # calibration()
            return

    def close_app(self):
        logger.debug("close app")
        self.master.destroy()

    def ask_override_calibration(self):
        logger.debug("ask to override calibration")
        tk_override = DialogAsk(master=self.master, title=i18n.tk_override_dialog[I18N_TITLE],
                                message=i18n.tk_override_dialog[I18N_MESSAGE],
                                detail=i18n.tk_override_dialog[I18N_DETAIL],
                                options=[I18N_ONLY_CALIBRATION_BUTTON, I18N_NO_BUTTON, I18N_YES_BUTTON],
                                dismiss_response=I18N_NO_BUTTON, icon=ERROR_ICON).show()
        return tk_override

    def ask_project_name(self):
        logger.debug("open p_options dialog, ask project name")
        p_name = DialogProjectOptions(master=self.master).show()
        return p_name

    def get_take_pictures_configs(self):
        logger.debug("choose take pictures configs")
        tk_options = DialogTakePictureOptions(master=self.master).show()
        return tk_options

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
        self.missing_calibration_frames = None
        self.current_state = S_STATE_NONE

    def bind(self, v: SensorView):
        logger.debug("bind in sensor controller")
        self.view = v
        logger.debug("sensor view bind switch function")
        self.view.sensor_list.switch_func = lambda old, new: self.switch(old, new)
        logger.debug("sensor view add all device views")
        self.view.create_view()
        for serial in self.master.devices:
            self._views.append(
                DeviceView(self.view.sensor_list, self.master.fn, serial=serial, borderwidth=5, relief="ridge",
                           style="Device.TFrame"))
            self._controllers.append(DeviceController(self.master))
            self._controllers[-1].bind(self._views[-1])
            self.view.sensor_list.add(serial, self._views[-1], serial)

    def take_calibration_pictures(self, calib_conf):
        modality = calib_conf[I18N_MODALITY]
        frames = calib_conf[I18N_FRAMES]
        if modality == TK_MANUAL:
            self.missing_calibration_frames = frames
            self.current_state = S_STATE_CALIBRATION
            self.view.set_mode(btn_name_list=[S_MANUAL_TAKE, S_STOP], title=S_CALIBRATION, frames=frames)
            self.view.set_command(btn_name=S_MANUAL_TAKE, command=lambda: self.take_manual_picture())
            self.view.set_command(btn_name=S_STOP, command=lambda: self.unset_mode(True))
        elif modality == TK_TIMED:
            self.view.set_mode(btn_name_list=[S_TIME_START, S_STOP], title=S_CALIBRATION, frames=frames)
            # self.view.set_command(btn_name=S_TIME_START, command=self.start_timed_capture())
            self.view.set_command(btn_name=S_STOP, command=lambda: self.unset_mode())

    def unset_mode(self, restore=False):
        if restore and self.current_state == S_STATE_CALIBRATION:
            restore_calibration_backup(self.view.sensor_list.selected_frame().serial())
        self.missing_calibration_frames = None
        self.current_state = S_STATE_NONE
        self.view.unset_mode()

    def take_picture(self, name="_", calibration=False):
        if calibration:
            # get frames asarray
            frame = self.view.selected_device().get_frame()
            # save
            calibration_path = Path(nect_config[CONFIG][CALIBRATION_PATH])
            rgb_file_path = calibration_path / self.view.selected_device_serial() / F_RGB / (str(name) + '.jpg')
            arr = open_cv.resize(np.flip(frame[IB_COLOR], axis=(1,)), RGB_IMAGE_SIZE_PARSED)
            open_cv.imwrite(str(rgb_file_path.resolve()), arr)
            ir_file_path = calibration_path / self.view.selected_device_serial() / F_IR / (str(name) + '.jpg')
            arr = np.asarray(
                open_cv.resize(np.flip(frame[IB_IR], axis=(1,)), IR_IMAGE_SIZE_PARSED) / IR_NORMALIZATOR * NP_UINT8_MAX,
                dtype=np.uint8)
            open_cv.imwrite(str(ir_file_path.resolve()), arr)
        else:
            print("foto")

    def take_manual_picture(self):
        if self.current_state == S_STATE_CALIBRATION:
            if isinstance(self.missing_calibration_frames, int):
                # reduce frames
                self.missing_calibration_frames = self.missing_calibration_frames - 1
                self.view.update_frame_count(self.missing_calibration_frames)
                # logic to take picture
                self.take_picture(name=str(self.missing_calibration_frames), calibration=True)

                # last picture?
                if self.missing_calibration_frames <= 0:
                    # yes start calibration, unset mode
                    self.unset_mode(restore=False)
                    remove_calibration_backup(self.view.sensor_list.selected_frame().serial())
                    self.calibration()
                # no wait for next
            else:
                self.unset_mode()
        elif self.current_state == S_STATE_CAPTURING:
            return
        else:
            self.unset_mode()

    def calibration(self):
        if isRGB:
            img_names = const.rgbFolder.glob('*.jpg')
            CAMERA_PATH = str(const.rgbCameraIntrinsic.resolve())
        else:
            img_names = const.irFolder.glob('*.jpg')
            CAMERA_PATH = str(const.irCameraIntrinsic.resolve())
        # create object points
        pattern_points = np.zeros((np.prod(const.pattern_size), 3), np.float32)
        pattern_points[:, :2] = np.indices(const.pattern_size).T.reshape(-1, 2)
        pattern_points *= const.square_size
        # print(pattern_points)

        obj_points = []
        img_points = []
        h, w = 0, 0
        for fn in img_names:
            print(f'processing {fn}...')
            img = cv2.imread(str(fn.resolve()), 0)
            if img is None:
                print("Failed to load", fn)
                continue

            h, w = img.shape[:2]
            found, corners = cv2.findChessboardCorners(img, const.pattern_size, flags=cv2.CALIB_CB_ADAPTIVE_THRESH)
            if found:
                cv2.cornerSubPix(img, corners, (5, 5), (-1, -1),
                                 (cv2.TERM_CRITERIA_EPS +
                                  cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                # Draw and display the corners
                cv2.drawChessboardCorners(img, (6, 8), corners, found)
                cv2.imshow('img', img)
                cv2.waitKey(500)
            if not found:
                print('chessboard not found')
                continue

            img_points.append(corners.reshape(-1, 2))
            obj_points.append(pattern_points)

            # save img_points for future stereo calibration
            img_file = shelve.open(os.path.splitext(fn)[0] + ".dat", 'n')
            img_file['img_points'] = corners.reshape(-1, 2)
            img_file.close()

            print('ok')

        rms, camera_matrix, dist_coefs, rvecs, tvecs = cv2.calibrateCamera(obj_points,
                                                                           img_points,
                                                                           (w, h),
                                                                           None,
                                                                           None,
                                                                           criteria=(
                                                                           cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                                                                           120, 0.001),
                                                                           flags=0)

        # save calibration results
        camera_file = shelve.open(CAMERA_PATH, 'n')
        camera_file['camera_matrix'] = camera_matrix
        camera_file['dist_coefs'] = dist_coefs
        camera_file.close()

        print("RMS:", rms)
        print("camera matrix:\n", camera_matrix)
        print("distortion coefficients: ", dist_coefs.ravel())

    def take_pictures_timed(self, frames_to_capture, time_between=1):
        logger.error("not implemented")

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
        logger.debug(f"return last selected project path")
        return self.__last_selected_project[P_PATH]

    def get_last_selected_file(self):
        logger.debug(f"return last selected file path")
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
            p_path = Path(project)
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
        logger.debug(f"bind in Selected file controller")
        self.view = v
        self.view.create_view()

    def update_view(self, data: Path):
        logger.debug(f"update view in Selected file controller")
        self.view.update_selected_file(data)


class SelectedProjectController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: ProjectInfoView):
        logger.debug(f"bind in Selected project controller")
        self.view = v
        self.view.create_view()

    def update_view(self, data):
        logger.debug(f"update view in Selected project controller")
        self.view.update_selected_project(data)


class ScanController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master
        self.data = None
        self.scanning = False

    def bind(self, v: ScanView):
        logger.debug(f"bind in Scan controller")
        self.view = v
        self.view.create_view()
        self.view.set_command(PAS_START, lambda: self.start())
        self.view.set_command(PAS_STOP, lambda: self.manual_stop())
        self.view.set_command(PAS_SEC_START, lambda: self.start())
        self.view.set_command(PAS_SEC_STOP, lambda: self.timed_cancel())

    def start(self):
        logger.debug(f"manual start of scan")
        data = self.view.get_form()
        valid, missing = self.validate_form_data(data)
        logger.debug(f"check is {valid}, missing: {missing}")
        if valid:
            self.scanning = True
            if data[PAS_TIME] == PAS_MANUAL:
                self.manual_start()
            else:
                self.timed_start()
        else:
            open_error_dialog(self.master, missing)

    def validate_form_data(self, data: dict):
        logger.debug(f"validate form data: {data}")
        missing = []
        valid = {PAS_EXIST, PAS_ROT, PAS_FACE, PAS_DATA, PAS_TIME, PAS_SEC}.issubset(data.keys())
        if valid:
            if self.data.getboolean(P_SCAN, P_DONE):
                if not data[PAS_EXIST] in {PAS_MERGE, PAS_OVERRIDE}:
                    missing.append(PAS_EXIST)
                    valid = False
            if not data[PAS_ROT] in {PAS_ROT_CAM, PAS_ROT_OBJ}:
                missing.append(PAS_ROT)
                valid = False
            if not data[PAS_FACE] in {PAS_FACE_CROP, PAS_FACE_DETECT}:
                missing.append(PAS_FACE)
                valid = False
            if not data[PAS_DATA] in {PAS_DEPTH, PAS_BOTH}:
                missing.append(PAS_DATA)
                valid = False
            if not isinstance(data[PAS_FPS], int):
                missing.append(PAS_FPS)
                valid = False
            if not data[PAS_TIME] in {PAS_SEC, PAS_MANUAL}:
                missing.append(PAS_TIME)
                valid = False
            if data[PAS_TIME] == PAS_SEC:
                if data[PAS_SEC] == "":
                    missing.append(PAS_SEC)
                    valid = False
                else:
                    check, data[PAS_SEC] = is_int(data[PAS_SEC])
                    if not check:
                        missing.append(PAS_SEC_NAN)
                        valid = False
                    elif data[PAS_SEC] <= 0:
                        missing.append(PAS_SEC_INCORRECT)
                        valid = False
        return valid, missing

    def manual_start(self):
        pass

    def manual_stop(self):
        pass

    def timed_start(self):
        pass

    def timed_cancel(self):
        pass

    def update_selected(self, data):
        logger.debug(f"update selected in Scan controller")
        if not self.data or (self.data and self.data != data):
            self.data = data
            self.view.update_selected_project(data)


class FinalController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: FinalView):
        logger.debug(f"bind in Final controller")
        self.view = v
        self.view.create_view()

    def update_selected(self, data):
        logger.debug(f"update selected in Final controller")
        self.view.update_selected_project(data)


class RegistrationController(Controller):
    def __init__(self, master=None) -> None:
        super().__init__()
        self.view = None
        self.master = master

    def bind(self, v: RegistrationView):
        logger.debug(f"bind in Registration controller")
        self.view = v
        self.view.create_view()

    def update_selected(self, data):
        logger.debug(f"update selected in Registration controller")
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
        logger.debug(f"bind in project action controller")
        self.view = v
        self.view.create_view()
        self.view.bind_controllers(scan_controller=self._scan_controller,
                                   registration_controller=self._registration_controller,
                                   final_controller=self._final_controller)

    def select_project(self, data):
        logger.debug(f"update selected project in project action controller")
        self.view.update_selected_project(data)
        if self.master.has_connected_device():
            self._scan_controller.update_selected(data)
        self._registration_controller.update_selected(data)
        self._final_controller.update_selected(data)
