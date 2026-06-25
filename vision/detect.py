import cv2
import numpy as np
import json
from picamera2 import Picamera2

TARGET_WIDTH = 700
TARGET_HEIGHT = 600
COLS, ROWS = 7, 6

# Calibrated HSV values – enter your actual tested values here
HSV_PARAMS = {
    "r1_min": 0,   "r1_max": 10,
    "r2_min": 160, "r2_max": 179,
    "r_sat": 120,  "r_val_min": 70,  "r_val_max": 255,
    "g_min": 20,   "g_max": 35,
    "g_sat": 120,  "g_val_min": 70,  "g_val_max": 255,
    "erosion": 1,  "dilation": 0,
}


def load_calibration(path="calibration.json"):
    with open(path, "r") as f:
        data = json.load(f)
    return np.array(data["punkte"], dtype=np.float32)


def compute_cell_positions(width, height, cols=COLS, rows=ROWS):
    cell_width = width / cols
    cell_height = height / rows
    positions = []
    for row in range(rows):
        row_positions = []
        for col in range(cols):
            cx = int((col + 0.5) * cell_width)
            cy = int((row + 0.5) * cell_height)
            row_positions.append((cx, cy))
        positions.append(row_positions)
    return positions


def detect_color_at_position(red_mask, yellow_mask, cx, cy, radius=15):
    h, w = red_mask.shape[:2]
    y1, y2 = max(0, cy - radius), min(h, cy + radius)
    x1, x2 = max(0, cx - radius), min(w, cx + radius)

    red_ratio    = np.mean(red_mask[y1:y2, x1:x2]) / 255
    yellow_ratio = np.mean(yellow_mask[y1:y2, x1:x2]) / 255

    if red_ratio > 0.3:
        return 1  # Player
    elif yellow_ratio > 0.3:
        return 2  # AI
    else:
        return 0  # Empty


def digitize_board(positions, red_mask, yellow_mask):
    board = []
    for row_positions in positions:
        board_row = []
        for (cx, cy) in row_positions:
            value = detect_color_at_position(red_mask, yellow_mask, cx, cy)
            board_row.append(value)
        board.append(board_row)
    return board


def compute_masks(hsv, params=HSV_PARAMS):
    red_mask1 = cv2.inRange(
        hsv,
        (params["r1_min"], params["r_sat"], params["r_val_min"]),
        (params["r1_max"], 255, params["r_val_max"]),
    )
    red_mask2 = cv2.inRange(
        hsv,
        (params["r2_min"], params["r_sat"], params["r_val_min"]),
        (params["r2_max"], 255, params["r_val_max"]),
    )
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    yellow_mask = cv2.inRange(
        hsv,
        (params["g_min"], params["g_sat"], params["g_val_min"]),
        (params["g_max"], 255, params["g_val_max"]),
    )

    kernel = np.ones((5, 5), np.uint8)
    if params["erosion"] > 0:
        red_mask    = cv2.erode(red_mask,    kernel, iterations=params["erosion"])
        yellow_mask = cv2.erode(yellow_mask, kernel, iterations=params["erosion"])
    if params["dilation"] > 0:
        red_mask    = cv2.dilate(red_mask,    kernel, iterations=params["dilation"])
        yellow_mask = cv2.dilate(yellow_mask, kernel, iterations=params["dilation"])

    return red_mask, yellow_mask


def setup_camera(calibration_path="calibration.json"):
    """Initializes the camera, loads calibration, computes the perspective
    transform matrix and cell positions. Call this once at program start."""
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (640, 480)}
    ))
    picam2.start()

    src_points = load_calibration(calibration_path)
    dst_points = np.array([
        [0, 0],
        [TARGET_WIDTH, 0],
        [TARGET_WIDTH, TARGET_HEIGHT],
        [0, TARGET_HEIGHT],
    ], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    cell_positions = compute_cell_positions(TARGET_WIDTH, TARGET_HEIGHT)

    return picam2, matrix, cell_positions


def get_current_board(picam2, matrix, cell_positions):
    """Captures a camera frame and returns the digitized 6x7 board matrix."""
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    warped = cv2.warpPerspective(frame, matrix, (TARGET_WIDTH, TARGET_HEIGHT))
    hsv = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)

    red_mask, yellow_mask = compute_masks(hsv)
    board = digitize_board(cell_positions, red_mask, yellow_mask)

    return board


def draw_overlay(warped, cell_positions, board):
    """Optional: draws the detected cells for visual verification."""
    overlay = warped.copy()
    for row_idx, row_positions in enumerate(cell_positions):
        for col_idx, (cx, cy) in enumerate(row_positions):
            value = board[row_idx][col_idx]
            if value == 1:
                color = (0, 0, 255)
            elif value == 2:
                color = (0, 255, 255)
            else:
                color = (180, 180, 180)
            cv2.circle(overlay, (cx, cy), 18, color, 2)
    return overlay