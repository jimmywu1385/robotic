import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

original_img_path = os.path.join('Assignment3', '/PartA/checkerboard.png')
ori_img = cv2.cvtColor(cv2.imread('Assignment3/PartA/checkerboard.png'), cv2.COLOR_BGR2RGB)

fig, ax = plt.subplots(1, 1, figsize=(12, 6))
ax.set_title('The size of the checkerboard: {} x {}'.format(ori_img.shape[1], ori_img.shape[0]))
ax.imshow(ori_img)

# Find the corners in the checkboard

img_path = 'Assignment3/PartA/checkboard'

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 35, 0.01)

obj_point = np.zeros((8 * 6, 3), np.float32)
obj_point[:, :2] = np.mgrid[0: 6, 0: 8].T.reshape(-1, 2)

obj_points_total = list() # 3d points in real world
img_points_total = list() # 2d points in real world

for img_name in sorted(os.listdir(img_path)):
    img = cv2.imread(os.path.join(img_path, img_name))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(img_gray, (6, 8), None) # Finds the positions of internal corners of the chessboard.
     
    if ret == True:
        obj_points_total.append(obj_point)
        img_points_total.append(corners)

        sub_corners = cv2.cornerSubPix(img_gray, corners, (16, 16), (-1, -1), criteria)

        cv2.drawChessboardCorners(img, (6, 8), sub_corners, ret)
        cv2.imwrite('Assignment3/PartA/checkboard_corners/' + os.path.splitext(img_name)[0] + '_corners.png', img)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points_total, img_points_total, img_gray.shape[::-1], None, None)
print('Intrinsic matrix:\n', mtx)

# Undistortion

img_path = 'Assignment3/PartA/checkboard/'

for img_name in sorted(os.listdir(img_path)):
    img = cv2.imread(os.path.join(img_path, img_name))
    h, w = img.shape[:2]

    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

    undistort = cv2.undistort(img, mtx, dist, None, newcameramtx)

    # 因為 undistort 結束會使得照片的邊邊稍微扭曲，所以要把這些扭曲的部分移除
    x, y, w, h = roi
    undistort = undistort[y: y+h, x: x+w]
    cv2.imwrite('Assignment3/PartA/undistort/' + os.path.splitext(img_name)[0] + '_undistort.jpg', undistort)

img = cv2.imread('Assignment3/PartA/2021-12-10_14-01-25.jpeg')
h, w = img.shape[:2]

newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

undistort = cv2.undistort(img, mtx, dist, None, newcameramtx)

x, y, w, h = roi
undistort = undistort[y: y+h, x: x+w]
cv2.imwrite('Assignment3/PartA/undistort/object_undistort.jpg', undistort)

fig, ax = plt.subplots(1, 1, figsize=(12, 6))
ax.imshow(cv2.cvtColor(undistort, cv2.COLOR_BGR2RGB))