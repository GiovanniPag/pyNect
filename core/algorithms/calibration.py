# single Kinect v2 camera calibration (RGB or IR)
from abc import ABC, abstractmethod

import numpy as np
import cv2
import shelve
import os
from glob import glob


class Calibrator(ABC):
    @abstractmethod
    def check(self):
        raise NotImplementedError


class RGBCameraCalibrator(Calibrator):

    def check(self):
        return

    def get_intrinsic_camera(self, serial):
        return


'''
isRGB = True

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
    img_file = shelve.open(os.path.splitext(fn)[0]+".dat", 'n')
    img_file['img_points'] = corners.reshape(-1, 2)
    img_file.close()

    print('ok')

rms, camera_matrix, dist_coefs, rvecs, tvecs = cv2.calibrateCamera(obj_points,
                                                                   img_points,
                                                                   (w, h),
                                                                   None,
                                                                   None,
                                                                   criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 120, 0.001),
                                                                   flags=0)

# save calibration results
camera_file = shelve.open(CAMERA_PATH, 'n')
camera_file['camera_matrix'] = camera_matrix
camera_file['dist_coefs'] = dist_coefs
camera_file.close()

print("RMS:", rms)
print("camera matrix:\n", camera_matrix)
print("distortion coefficients: ", dist_coefs.ravel())

'''
