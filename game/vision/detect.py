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

    pts_src = lade_kalibrierung()

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

    # Farb-Trackbars
    cv2.createTrackbar("R1 Hue Min",  "Vier Gewinnt Erkennung", 0,   179, lambda x: None)
    cv2.createTrackbar("R1 Hue Max",  "Vier Gewinnt Erkennung", 10,  179, lambda x: None)
    cv2.createTrackbar("R2 Hue Min",  "Vier Gewinnt Erkennung", 160, 179, lambda x: None)
    cv2.createTrackbar("R2 Hue Max",  "Vier Gewinnt Erkennung", 179, 179, lambda x: None)
    cv2.createTrackbar("R Sat Min",   "Vier Gewinnt Erkennung", 120, 255, lambda x: None)
    cv2.createTrackbar("R Val Min",   "Vier Gewinnt Erkennung", 70,  255, lambda x: None)
    cv2.createTrackbar("Y Hue Min",   "Vier Gewinnt Erkennung", 20,  179, lambda x: None)
    cv2.createTrackbar("Y Hue Max",   "Vier Gewinnt Erkennung", 35,  179, lambda x: None)
    cv2.createTrackbar("Y Sat Min",   "Vier Gewinnt Erkennung", 120, 255, lambda x: None)
    cv2.createTrackbar("Y Val Min",   "Vier Gewinnt Erkennung", 70,  255, lambda x: None)

    # Kreiserkennungs-Trackbars (grosszuegigere Startwerte)
    cv2.createTrackbar("Min Radius",  "Vier Gewinnt Erkennung", 15,  100, lambda x: None)
    cv2.createTrackbar("Max Radius",  "Vier Gewinnt Erkennung", 45,  150, lambda x: None)
    cv2.createTrackbar("Min Dist",    "Vier Gewinnt Erkennung", 40,  150, lambda x: None)
    cv2.createTrackbar("Param1",      "Vier Gewinnt Erkennung", 60,  200, lambda x: None)
    cv2.createTrackbar("Param2",      "Vier Gewinnt Erkennung", 20,  100, lambda x: None)
    cv2.createTrackbar("Blur",        "Vier Gewinnt Erkennung", 6,   15,  lambda x: None)

    # Glaettung der Erkennung ueber mehrere Frames (gegen Flackern)
    letzte_kreise = []
    GLAETTUNGS_FENSTER = 5

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        entzerrt = cv2.warpPerspective(frame, matrix, (ZIEL_BREITE, ZIEL_HOEHE))
        hsv = cv2.cvtColor(entzerrt, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(entzerrt, cv2.COLOR_BGR2GRAY)

        # Werte auslesen
        r1_min = cv2.getTrackbarPos("R1 Hue Min", "Vier Gewinnt Erkennung")
        r1_max = cv2.getTrackbarPos("R1 Hue Max", "Vier Gewinnt Erkennung")
        r2_min = cv2.getTrackbarPos("R2 Hue Min", "Vier Gewinnt Erkennung")
        r2_max = cv2.getTrackbarPos("R2 Hue Max", "Vier Gewinnt Erkennung")
        r_sat  = cv2.getTrackbarPos("R Sat Min",  "Vier Gewinnt Erkennung")
        r_val  = cv2.getTrackbarPos("R Val Min",  "Vier Gewinnt Erkennung")
        g_min  = cv2.getTrackbarPos("Y Hue Min",  "Vier Gewinnt Erkennung")
        g_max  = cv2.getTrackbarPos("Y Hue Max",  "Vier Gewinnt Erkennung")
        g_sat  = cv2.getTrackbarPos("Y Sat Min",  "Vier Gewinnt Erkennung")
        g_val  = cv2.getTrackbarPos("Y Val Min",  "Vier Gewinnt Erkennung")

        min_radius = cv2.getTrackbarPos("Min Radius", "Vier Gewinnt Erkennung")
        max_radius = cv2.getTrackbarPos("Max Radius", "Vier Gewinnt Erkennung")
        min_dist   = cv2.getTrackbarPos("Min Dist",   "Vier Gewinnt Erkennung")
        param1_val = cv2.getTrackbarPos("Param1",     "Vier Gewinnt Erkennung")
        param2_val = cv2.getTrackbarPos("Param2",     "Vier Gewinnt Erkennung")
        blur_val   = cv2.getTrackbarPos("Blur",       "Vier Gewinnt Erkennung")

        # Farbmasken
        rot_maske1 = cv2.inRange(hsv, (r1_min, r_sat, r_val), (r1_max, 255, 255))
        rot_maske2 = cv2.inRange(hsv, (r2_min, r_sat, r_val), (r2_max, 255, 255))
        rot_maske  = cv2.bitwise_or(rot_maske1, rot_maske2)
        gelb_maske = cv2.inRange(hsv, (g_min, g_sat, g_val), (g_max, 255, 255))

        # Kleine Aufraeumung der Masken (entfernt Einzelpixel-Rauschen)
        kernel = np.ones((5, 5), np.uint8)
        rot_maske  = cv2.morphologyEx(rot_maske,  cv2.MORPH_OPEN, kernel)
        gelb_maske = cv2.morphologyEx(gelb_maske, cv2.MORPH_OPEN, kernel)
        rot_maske  = cv2.morphologyEx(rot_maske,  cv2.MORPH_CLOSE, kernel)
        gelb_maske = cv2.morphologyEx(gelb_maske, cv2.MORPH_CLOSE, kernel)

        # Graubild glaetten fuer Kreiserkennung
        blur_k = blur_val if blur_val % 2 == 1 else blur_val + 1
        blur_k = max(1, blur_k)
        geglaettet = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)
        # Kontrast leicht anheben hilft HoughCircles bei gleichmaessigen Flaechen
        geglaettet = cv2.equalizeHist(geglaettet)

        param1_safe = max(1, param1_val)
        param2_safe = max(1, param2_val)
        min_dist_safe = max(1, min_dist)
        max_radius_safe = max(min_radius + 1, max_radius)

        kreise = cv2.HoughCircles(
            geglaettet,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dist_safe,
            param1=param1_safe,
            param2=param2_safe,
            minRadius=min_radius,
            maxRadius=max_radius_safe
        )

        aktuelle_kreise = []
        if kreise is not None:
            for kreis in kreise[0, :]:
                aktuelle_kreise.append((float(kreis[0]), float(kreis[1]), float(kreis[2])))

        # Ueber mehrere Frames sammeln und nur Kreise zeigen, die oft genug auftauchen
        letzte_kreise.append(aktuelle_kreise)
        if len(letzte_kreise) > GLAETTUNGS_FENSTER:
            letzte_kreise.pop(0)

        # Einfache Stabilisierung: alle Kreise aus dem letzten Frame anzeigen,
        # aber nur wenn in mind. der Haelfte der letzten Frames an aehnlicher Position etwas war
        kreis_bild = entzerrt.copy()
        bestaetigte_kreise = []

        for (cx, cy, r) in aktuelle_kreise:
            treffer = 0
            for frame_kreise in letzte_kreise:
                for (ox, oy, orad) in frame_kreise:
                    if abs(ox - cx) < 20 and abs(oy - cy) < 20:
                        treffer += 1
                        break
            if treffer >= max(2, GLAETTUNGS_FENSTER // 2):
                bestaetigte_kreise.append((cx, cy, r))

        for (cx, cy, r) in bestaetigte_kreise:
            cx_i, cy_i, r_i = int(cx), int(cy), int(r)

            ist_rot  = rot_maske[cy_i, cx_i]  > 0 if 0 <= cy_i < ZIEL_HOEHE and 0 <= cx_i < ZIEL_BREITE else False
            ist_gelb = gelb_maske[cy_i, cx_i] > 0 if 0 <= cy_i < ZIEL_HOEHE and 0 <= cx_i < ZIEL_BREITE else False

            if ist_rot:
                farbe = (0, 0, 255)
            elif ist_gelb:
                farbe = (0, 255, 255)
            else:
                farbe = (0, 255, 0)

            cv2.circle(kreis_bild, (cx_i, cy_i), r_i, farbe, 2)
            cv2.circle(kreis_bild, (cx_i, cy_i), 2, (255, 255, 255), 3)

        rot_bgr  = cv2.cvtColor(rot_maske,  cv2.COLOR_GRAY2BGR)
        gelb_bgr = cv2.cvtColor(gelb_maske, cv2.COLOR_GRAY2BGR)

        # 2x2 Layout: Original | Entzerrt+Kreise // Rot | Gelb
        frame_small = cv2.resize(frame, (ZIEL_BREITE, ZIEL_HOEHE))
        oben  = np.hstack([frame_small, kreis_bild])
        unten = np.hstack([rot_bgr, gelb_bgr])
        combined = np.vstack([oben, unten])

        # Fuer die Anzeige insgesamt verkleinern, damit es auf den Bildschirm passt
        combined_small = cv2.resize(combined, (combined.shape[1] // 2, combined.shape[0] // 2))

        cv2.imshow("Vier Gewinnt Erkennung", combined_small)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_board()