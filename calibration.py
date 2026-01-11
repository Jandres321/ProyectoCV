from typing import List
import numpy as np
import imageio
import cv2
import copy
import glob
import os
from os.path import dirname, join


def load_images(filenames: List) -> List:
    return [imageio.imread(filename) for filename in filenames]

def show_image(img, name: str = "Image"):
    cv2.imshow(name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
def write_image(img: np.array, path: str):
    cv2.imwrite(path, img)
    
def get_chessboard_points(chessboard_shape, dx, dy):
    # Get number of corners in each dimension
    rows, cols = chessboard_shape
    
    # Create a list to store 3D coordinates
    object_points = []
    
    # Generate 3D coordinates for each corner
    for i in range(cols):
        for j in range(rows):
            # X corresponds to column (j), Y corresponds to row (i), Z is always 0
            object_points.append([j * dx, i * dy, 0.0])
    
    # Convert to numpy array with float32 dtype
    return np.array(object_points, dtype=np.float32)


def main():
    path = join(os.getcwd(), "data", "calibration", "chessboards")

    imgs_path = [join(path, f"{img_path}") for img_path in os.listdir(path)]
    imgs = load_images(imgs_path)

    corners = [cv2.findChessboardCorners(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (8,6)) for img in imgs]

    corners_copy = copy.deepcopy(corners)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)

    # TODO To refine corner detections with cv2.cornerSubPix() you need to input grayscale images. Build a list containing grayscale images.
    imgs_gray = [cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) for img in imgs]
    # [show_image(img) for img in imgs_gray]
    corners_refined = [cv2.cornerSubPix(i, cor[1], (8, 6), (-1, -1), criteria) if cor[0] else [] for i, cor in zip(imgs_gray, corners_copy)]

    output_folder = "data/calibration/outputs/"

    imgs_copy = copy.deepcopy(imgs)
    imgs_with_points = [cv2.drawChessboardCorners(img, (8,6), corner, True) for img, corner in zip(imgs_copy, corners_refined)]
    # Check the folder exists
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    # Show and save
    for i, img in enumerate(imgs_with_points):
        show_image(img)
        output_img_path = join(output_folder, f"detection_{i}.png")
        write_image(img, output_img_path)

    chessboard_points = np.array([get_chessboard_points((8, 6), 29, 29) for corner_data in corners_refined])
    
    # Filter data and get only those with adequate detections
    valid_corners = [cor[1] for cor in corners if cor[0]]
    # Convert list to numpy array
    valid_corners = np.asarray(valid_corners, dtype=np.float32)
    
    # Calibrate camera using cv2.calibrateCamera()
    rms, intrinsics, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        chessboard_points,
        valid_corners,
        [imgs_gray[0].shape[1], imgs_gray[0].shape[0]],  # Image size (width, height)
        None,
        None
    )

    print("RMS:", rms)
    print("Intrinsics:\n", intrinsics)
    print("Distortion Coefficients:\n", dist_coeffs)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_calibration_parameters(intrinsics, dist_coeffs, join(script_dir, "calibration_parameters.npz"))

def save_calibration_parameters(intrinsics: np.array, dist_coeffs: np.array, path: str):
    np.savez(path, intr=intrinsics, dist=dist_coeffs)

if __name__ == "__main__":
    main()