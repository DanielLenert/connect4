import cv2
import numpy as np
import json
from picamera2 import Picamera2


def lade_kalibrierung(pfad="calibration.json"):
    with open(pfad, "r") as f:
        daten = json.load(f)
    return np.array(daten["punkte"], dtype=np.float32)


def erkenne_farbe_an_position(rot_maske, gelb_maske, cx, cy, radius=15):
    h, w = rot_maske.shape[:2]
    y1, y2 = max(0, cy - radius), min(h, cy + radius)
    x1, x2 = max(0, cx - radius), min(w, cx + radius)

    rot_anteil  = np.mean(rot_maske[y1:y2, x1:x2]) / 255
    gelb_anteil = np.mean(gelb_maske[y1:y2, x1:x2]) / 255

    if rot_anteil > 0.3:
        return 1  # Spieler
    elif gelb_anteil > 0.3:
        return 2  # KI
    else:
        return 0  # leer


def berechne_zellpositionen(breite, hoehe, cols=7, rows=6):
    zell_breite = breite / cols
    zell_hoehe = hoehe / rows
    positionen = []
    for row in range(rows):
        zeile = []
        for col in range(cols):
            cx = int((col + 0.5) * zell_breite)
            cy = int((row + 0.5) * zell_hoehe)
            zeile.append((cx, cy))
        positionen.append(zeile)
    return positionen


def digitalisiere_spielfeld(positionen, rot_maske, gelb_maske):
    board = []
    for zeile in positionen:
        board_zeile = []
        for (cx, cy) in zeile:
            wert = erkenne_farbe_an_position(rot_maske, gelb_maske, cx, cy)
            board_zeile.append(wert)
        board.append(board_zeile)
    return board


def detect_board():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (320, 240)}
    ))
    picam2.start()

    pts_src = lade_kalibrierung()

    ZIEL_BREITE = 700
    ZIEL_HOEHE = 600
    COLS, ROWS = 7, 6

    pts_dst = np.array([
        [0, 0],
        [ZIEL_BREITE, 0],
        [ZIEL_BREITE, ZIEL_HOEHE],
        [0, ZIEL_HOEHE],
    ], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)

    # Zellpositionen einmalig berechnen, nicht jeden Frame neu
    zellpositionen = berechne_zellpositionen(ZIEL_BREITE, ZIEL_HOEHE, COLS, ROWS)

    cv2.namedWindow("Vier Gewinnt Erkennung")
    cv2.createTrackbar("R1 Hue Min",  "Vier Gewinnt Erkennung", 0,   179, lambda x: None)
    cv2.createTrackbar("R1 Hue Max",  "Vier Gewinnt Erkennung", 10,  179, lambda x: None)
    cv2.createTrackbar("R2 Hue Min",  "Vier Gewinnt Erkennung", 160, 179, lambda x: None)
    cv2.createTrackbar("R2 Hue Max",  "Vier Gewinnt Erkennung", 179, 179, lambda x: None)
    cv2.createTrackbar("R Sat Min",   "Vier Gewinnt Erkennung", 120, 255, lambda x: None)
    cv2.createTrackbar("R Val Min",   "Vier Gewinnt Erkennung", 70,  255, lambda x: None)
    cv2.createTrackbar("R Val Max",   "Vier Gewinnt Erkennung", 255, 255, lambda x: None)
    cv2.createTrackbar("Y Hue Min",   "Vier Gewinnt Erkennung", 20,  179, lambda x: None)
    cv2.createTrackbar("Y Hue Max",   "Vier Gewinnt Erkennung", 35,  179, lambda x: None)
    cv2.createTrackbar("Y Sat Min",   "Vier Gewinnt Erkennung", 120, 255, lambda x: None)
    cv2.createTrackbar("Y Val Min",   "Vier Gewinnt Erkennung", 70,  255, lambda x: None)
    cv2.createTrackbar("Y Val Max",   "Vier Gewinnt Erkennung", 255, 255, lambda x: None)
    cv2.createTrackbar("Erosion",     "Vier Gewinnt Erkennung", 1,   10,  lambda x: None)
    cv2.createTrackbar("Dilation",    "Vier Gewinnt Erkennung", 0,   10,  lambda x: None)

    frame_counter = 0
    letztes_board = None

    try:
        while True:
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            entzerrt = cv2.warpPerspective(frame, matrix, (ZIEL_BREITE, ZIEL_HOEHE))

            frame_counter += 1
            # Nur jeden 2. Frame komplett verarbeiten, spart Rechenleistung
            if frame_counter % 2 != 0 and letztes_board is not None:
                anzeige = zeichne_anzeige(entzerrt, zellpositionen, letztes_board)
                cv2.imshow("Vier Gewinnt Erkennung", anzeige)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            hsv = cv2.cvtColor(entzerrt, cv2.COLOR_BGR2HSV)

            r1_min    = cv2.getTrackbarPos("R1 Hue Min", "Vier Gewinnt Erkennung")
            r1_max    = cv2.getTrackbarPos("R1 Hue Max", "Vier Gewinnt Erkennung")
            r2_min    = cv2.getTrackbarPos("R2 Hue Min", "Vier Gewinnt Erkennung")
            r2_max    = cv2.getTrackbarPos("R2 Hue Max", "Vier Gewinnt Erkennung")
            r_sat     = cv2.getTrackbarPos("R Sat Min",  "Vier Gewinnt Erkennung")
            r_val_min = cv2.getTrackbarPos("R Val Min",  "Vier Gewinnt Erkennung")
            r_val_max = cv2.getTrackbarPos("R Val Max",  "Vier Gewinnt Erkennung")
            g_min     = cv2.getTrackbarPos("Y Hue Min",  "Vier Gewinnt Erkennung")
            g_max     = cv2.getTrackbarPos("Y Hue Max",  "Vier Gewinnt Erkennung")
            g_sat     = cv2.getTrackbarPos("Y Sat Min",  "Vier Gewinnt Erkennung")
            g_val_min = cv2.getTrackbarPos("Y Val Min",  "Vier Gewinnt Erkennung")
            g_val_max = cv2.getTrackbarPos("Y Val Max",  "Vier Gewinnt Erkennung")
            erosion_val  = cv2.getTrackbarPos("Erosion",  "Vier Gewinnt Erkennung")
            dilation_val = cv2.getTrackbarPos("Dilation", "Vier Gewinnt Erkennung")

            rot_maske1 = cv2.inRange(hsv, (r1_min, r_sat, r_val_min), (r1_max, 255, r_val_max))
            rot_maske2 = cv2.inRange(hsv, (r2_min, r_sat, r_val_min), (r2_max, 255, r_val_max))
            rot_maske  = cv2.bitwise_or(rot_maske1, rot_maske2)
            gelb_maske = cv2.inRange(hsv, (g_min, g_sat, g_val_min), (g_max, 255, g_val_max))

            kernel = np.ones((5, 5), np.uint8)
            if erosion_val > 0:
                rot_maske  = cv2.erode(rot_maske,  kernel, iterations=erosion_val)
                gelb_maske = cv2.erode(gelb_maske, kernel, iterations=erosion_val)
            if dilation_val > 0:
                rot_maske  = cv2.dilate(rot_maske,  kernel, iterations=dilation_val)
                gelb_maske = cv2.dilate(gelb_maske, kernel, iterations=dilation_val)

            board = digitalisiere_spielfeld(zellpositionen, rot_maske, gelb_maske)
            letztes_board = board

            anzeige = zeichne_anzeige(entzerrt, zellpositionen, board)
            cv2.imshow("Vier Gewinnt Erkennung", anzeige)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        picam2.stop()
        cv2.destroyAllWindows()


def zeichne_anzeige(entzerrt, zellpositionen, board):
    anzeige = entzerrt.copy()
    for row_idx, zeile in enumerate(zellpositionen):
        for col_idx, (cx, cy) in enumerate(zeile):
            wert = board[row_idx][col_idx]
            if wert == 1:
                farbe = (0, 0, 255)
            elif wert == 2:
                farbe = (0, 255, 255)
            else:
                farbe = (180, 180, 180)
            cv2.circle(anzeige, (cx, cy), 18, farbe, 2)
    return anzeige


if __name__ == "__main__":
    detect_board()