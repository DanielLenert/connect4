import cv2
import numpy as np
import json
from picamera2 import Picamera2


def lade_kalibrierung(pfad="calibration.json"):
    with open(pfad, "r") as f:
        daten = json.load(f)
    return np.array(daten["punkte"], dtype=np.float32)


def detect_board():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (640, 480)}
    ))
    picam2.start()

    # Kalibrierungspunkte laden (einmalig per calibrate.py erstellt)
    pts_src = lade_kalibrierung()

    # Zielgroesse des entzerrten Spielfelds (frei waehlbar, Seitenverhaeltnis 7:6 sinnvoll)
    ZIEL_BREITE = 700
    ZIEL_HOEHE = 600

    pts_dst = np.array([
        [0, 0],
        [ZIEL_BREITE, 0],
        [ZIEL_BREITE, ZIEL_HOEHE],
        [0, ZIEL_HOEHE],
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)

    cv2.namedWindow("Vier Gewinnt Erkennung")

    cv2.createTrackbar("Min Radius",  "Vier Gewinnt Erkennung", 8,   100, lambda x: None)
    cv2.createTrackbar("Max Radius",  "Vier Gewinnt Erkennung", 25,  100, lambda x: None)
    cv2.createTrackbar("Min Dist",    "Vier Gewinnt Erkennung", 20,  100, lambda x: None)
    cv2.createTrackbar("Param1",      "Vier Gewinnt Erkennung", 50,  200, lambda x: None)
    cv2.createTrackbar("Param2",      "Vier Gewinnt Erkennung", 30,  100, lambda x: None)
    cv2.createTrackbar("Blur",        "Vier Gewinnt Erkennung", 4,   15,  lambda x: None)

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Perspektivische Entzerrung VOR der Kreiserkennung
        entzerrt = cv2.warpPerspective(frame, matrix, (ZIEL_BREITE, ZIEL_HOEHE))

        gray = cv2.cvtColor(entzerrt, cv2.COLOR_BGR2GRAY)

        min_radius = cv2.getTrackbarPos("Min Radius", "Vier Gewinnt Erkennung")
        max_radius = cv2.getTrackbarPos("Max Radius", "Vier Gewinnt Erkennung")
        min_dist   = cv2.getTrackbarPos("Min Dist",   "Vier Gewinnt Erkennung")
        param1_val = cv2.getTrackbarPos("Param1",     "Vier Gewinnt Erkennung")
        param2_val = cv2.getTrackbarPos("Param2",     "Vier Gewinnt Erkennung")
        blur_val   = cv2.getTrackbarPos("Blur",       "Vier Gewinnt Erkennung")

        blur_k = blur_val if blur_val % 2 == 1 else blur_val + 1
        blur_k = max(1, blur_k)
        geglaettet = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)

        param1_safe = max(1, param1_val)
        param2_safe = max(1, param2_val)
        min_dist_safe = max(1, min_dist)
        max_radius_safe = max(min_radius + 1, max_radius)

        kreise = cv2.HoughCircles(
            geglaettet,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_dist_safe,
            param1=param1_safe,
            param2=param2_safe,
            minRadius=min_radius,
            maxRadius=max_radius_safe
        )

        kreis_bild = entzerrt.copy()

        if kreise is not None:
            kreise = np.uint16(np.around(kreise))
            for kreis in kreise[0, :]:
                cx, cy, r = int(kreis[0]), int(kreis[1]), int(kreis[2])
                cv2.circle(kreis_bild, (cx, cy), r, (0, 255, 0), 2)
                cv2.circle(kreis_bild, (cx, cy), 2, (255, 255, 255), 3)

        gray_bgr = cv2.cvtColor(geglaettet, cv2.COLOR_GRAY2BGR)

        # Originalbild klein als Referenz, dann entzerrtes Graubild, dann Ergebnis
        frame_small = cv2.resize(frame, (ZIEL_BREITE, ZIEL_HOEHE))
        combined = np.hstack([frame_small, gray_bgr, kreis_bild])
        cv2.imshow("Vier Gewinnt Erkennung", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_board()