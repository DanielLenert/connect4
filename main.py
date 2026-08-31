import cv2
import time
from game.board import check_win, is_draw
from game.ai import get_ai_move
from vision.detect import setup_camera, draw_overlay, compute_masks, digitize_board
from hardware.display import zeige_start, zeige_ki_denkt, zeige_spieler_dran, zeige_spieler_gewinnt, zeige_ki_gewinnt, clear_display
from hardware.servos import execute_move, reset_all_servos
import signal
import sys
import RPi.GPIO as GPIO

SHUTDOWN_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(SHUTDOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def check_shutdown_button():
    if GPIO.input(SHUTDOWN_PIN) == GPIO.LOW:
        print("Shutdown-Button gedrückt...")
        zeige_text("Wird", "beendet...")
        reset_all_servos()
        clear_display()
        import os
        os.system("sudo shutdown -h now")

def handle_exit(sig, frame):
    print("\nProgramm wird beendet...")
    reset_all_servos()
    picam2.stop()
    cv2.destroyAllWindows()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)   # Strg+C
signal.signal(signal.SIGTERM, handle_exit)  # systemd stop 

def capture_frame(picam2, matrix):
    """Captures a camera frame and warps it. Returns the warped image."""
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    warped = cv2.warpPerspective(frame, matrix, (700, 600))
    return warped


def detect_board_from_image(warped, cell_positions):
    """Computes the digitized matrix from an already warped image."""
    hsv = cv2.cvtColor(warped, cv2.COLOR_BGR2HSV)
    red_mask, yellow_mask = compute_masks(hsv)
    board = digitize_board(cell_positions, red_mask, yellow_mask)
    return board

def is_ai_move(old_board, new_board):
    for r in range(len(old_board)):
        for c in range(len(old_board[0])):
            if old_board[r][c] == 0 and new_board[r][c] == 2:
                return True
    return False

def wait_for_stable_state(picam2, matrix, cell_positions, stable_frames=10, interval=0.15):
    """Continuously shows the live image AND waits until the detected board
    stays unchanged for several frames in a row. Returns (board, warped)."""
    last_board = None
    counter = 0

    while True:
        check_shutdown_button()  # bei jedem Frame prüfen
        warped = capture_frame(picam2, matrix)
        board = detect_board_from_image(warped, cell_positions)

        # Always update the live view, even during the stability check
        overlay = draw_overlay(warped, cell_positions, board)
        cv2.imshow("Vier Gewinnt - Live", overlay)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return None, warped

        if board == last_board:
            counter += 1
        else:
            counter = 0
            last_board = board

        if counter >= stable_frames:
            return last_board, warped

        time.sleep(interval)


def is_player_move(old_board, new_board):
    for r in range(len(old_board)):
        for c in range(len(old_board[0])):
            if old_board[r][c] == 0 and new_board[r][c] == 1:
                return True
    return False


def print_board(board):
    for row in board:
        print(" ".join(str(cell) for cell in row))


def main():
    picam2, matrix, cell_positions = setup_camera()
    last_board = None

    zeige_start()  # Startanzeige beim Programmstart
    print("=== Vier Gewinnt ===")
    print("Bitte beginnen Sie mit einem roten Stein.\n")

    try:
        while True:
            board, warped = wait_for_stable_state(picam2, matrix, cell_positions)

            if board is None:
                break

            if last_board is None:
                last_board = board
                continue

            if board != last_board:
                print("\nNeuer stabiler Zustand erkannt:")
                print_board(board)

                if check_win(board, 1):
                    zeige_spieler_gewinnt()
                    print("Spieler gewinnt.")
                    break

                if check_win(board, 2):
                    zeige_ki_gewinnt()
                    print("Maschine gewinnt.")
                    break

                if is_draw(board):
                    print("Unentschieden.")
                    break

                if is_player_move(last_board, board):
                    col = get_ai_move(board, depth=5)
                    zeige_ki_denkt(col)
                    print(f"Spielerzug erkannt. Naechster KI-Zug: Spalte {col + 1}")
                    execute_move(col)  

                elif is_ai_move(last_board, board):
                    zeige_spieler_dran()
                    print("KI-Zug erkannt. Sie sind am Zug.")

                last_board = board

    finally:
        reset_all_servos()
        clear_display()
        picam2.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
