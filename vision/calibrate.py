import cv2
import numpy as np
import json
from picamera2 import Picamera2

PUNKTE = []
MAX_PUNKTE = 4
MODUS = "kalibrierung"  # "kalibrierung" oder "farben"

# HSV Standardwerte
hsv_params = {
    "r1_min": 0,   "r1_max": 10,
    "r2_min": 160, "r2_max": 179,
    "r_sat": 120,  "r_val_min": 70,  "r_val_max": 255,
    "g_min": 20,   "g_max": 35,
    "g_sat": 120,  "g_val_min": 70,  "g_val_max": 255,
    "erosion": 1,  "dilation": 0,
}

def mouse_callback(event, x, y, flags, param):
    if MODUS == "kalibrierung":
        if event == cv2.EVENT_LBUTTONDOWN and len(PUNKTE) < MAX_PUNKTE:
            PUNKTE.append([x, y])
            print(f"Punkt {len(PUNKTE)}: ({x}, {y})")


def speichere_kalibrierung():
    daten = {"punkte": PUNKTE}
    with open("/home/lenert-da/bclr/connect4/calibration.json", "w") as f:
        json.dump(daten, f, indent=2)
    print("Kalibrierung gespeichert.")


def speichere_farben():
    with open("/home/lenert-da/bclr/connect4/hsv_params.json", "w") as f:
        json.dump(hsv_params, f, indent=2)
    print("Farbwerte gespeichert.")


def lade_kalibrierung():
    try:
        with open("/home/lenert-da/bclr/connect4/calibration.json", "r") as f:
            daten = json.load(f)
        return np.array(daten["punkte"], dtype=np.float32)
    except Exception:
        return None


def berechne_matrix(punkte):
    pts_src = punkte
    pts_dst = np.array([
        [0, 0], [700, 0], [700, 600], [0, 600]
    ], dtype=np.float32)
    return cv2.getPerspectiveTransform(pts_src, pts_dst)


def erstelle_trackbars(fenster):
    cv2.createTrackbar("R1 Hue Min", fenster, hsv_params["r1_min"], 179, lambda x: None)
    cv2.createTrackbar("R1 Hue Max", fenster, hsv_params["r1_max"], 179, lambda x: None)
    cv2.createTrackbar("R2 Hue Min", fenster, hsv_params["r2_min"], 179, lambda x: None)
    cv2.createTrackbar("R2 Hue Max", fenster, hsv_params["r2_max"], 179, lambda x: None)
    cv2.createTrackbar("R Sat Min",  fenster, hsv_params["r_sat"],  255, lambda x: None)
    cv2.createTrackbar("R Val Min",  fenster, hsv_params["r_val_min"], 255, lambda x: None)
    cv2.createTrackbar("R Val Max",  fenster, hsv_params["r_val_max"], 255, lambda x: None)
    cv2.createTrackbar("Y Hue Min",  fenster, hsv_params["g_min"],  179, lambda x: None)
    cv2.createTrackbar("Y Hue Max",  fenster, hsv_params["g_max"],  179, lambda x: None)
    cv2.createTrackbar("Y Sat Min",  fenster, hsv_params["g_sat"],  255, lambda x: None)
    cv2.createTrackbar("Y Val Min",  fenster, hsv_params["g_val_min"], 255, lambda x: None)
    cv2.createTrackbar("Y Val Max",  fenster, hsv_params["g_val_max"], 255, lambda x: None)
    cv2.createTrackbar("Erosion",    fenster, hsv_params["erosion"], 10, lambda x: None)
    cv2.createTrackbar("Dilation",   fenster, hsv_params["dilation"], 10, lambda x: None)


def lese_trackbars(fenster):
    hsv_params["r1_min"]    = cv2.getTrackbarPos("R1 Hue Min", fenster)
    hsv_params["r1_max"]    = cv2.getTrackbarPos("R1 Hue Max", fenster)
    hsv_params["r2_min"]    = cv2.getTrackbarPos("R2 Hue Min", fenster)
    hsv_params["r2_max"]    = cv2.getTrackbarPos("R2 Hue Max", fenster)
    hsv_params["r_sat"]     = cv2.getTrackbarPos("R Sat Min",  fenster)
    hsv_params["r_val_min"] = cv2.getTrackbarPos("R Val Min",  fenster)
    hsv_params["r_val_max"] = cv2.getTrackbarPos("R Val Max",  fenster)
    hsv_params["g_min"]     = cv2.getTrackbarPos("Y Hue Min",  fenster)
    hsv_params["g_max"]     = cv2.getTrackbarPos("Y Hue Max",  fenster)
    hsv_params["g_sat"]     = cv2.getTrackbarPos("Y Sat Min",  fenster)
    hsv_params["g_val_min"] = cv2.getTrackbarPos("Y Val Min",  fenster)
    hsv_params["g_val_max"] = cv2.getTrackbarPos("Y Val Max",  fenster)
    hsv_params["erosion"]   = cv2.getTrackbarPos("Erosion",    fenster)
    hsv_params["dilation"]  = cv2.getTrackbarPos("Dilation",   fenster)


def main():
    global MODUS

    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (640, 480)}
    ))
    picam2.start()

    # Kalibrierungsfenster
    cv2.namedWindow("Kalibrierung")
    cv2.setMouseCallback("Kalibrierung", mouse_callback)

    # Farbfenster mit Trackbars
    cv2.namedWindow("Farberkennung")
    erstelle_trackbars("Farberkennung")

    print("=== Kalibrierung ===")
    print("1. Klicke 4 Ecken: oben-links, oben-rechts, unten-rechts, unten-links")
    print("'s' = Kalibrierung speichern")
    print("'r' = Punkte zurücksetzen")
    print("'f' = Farbwerte speichern")
    print("'q' = Beenden")

    matrix = None
    pts = lade_kalibrierung()
    if pts is not None:
        matrix = berechne_matrix(pts)
        print("Vorherige Kalibrierung geladen.")

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # ── Kalibrierungsfenster ──
        anzeige = frame.copy()
        for i, p in enumerate(PUNKTE):
            cv2.circle(anzeige, tuple(p), 6, (0, 255, 0), -1)
            cv2.putText(anzeige, str(i + 1), (p[0] + 10, p[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        if len(PUNKTE) >= 2:
            for i in range(len(PUNKTE) - 1):
                cv2.line(anzeige, tuple(PUNKTE[i]), tuple(PUNKTE[i + 1]), (0, 255, 0), 2)
        if len(PUNKTE) == MAX_PUNKTE:
            cv2.line(anzeige, tuple(PUNKTE[3]), tuple(PUNKTE[0]), (0, 255, 0), 2)

        cv2.putText(anzeige, f"Punkte: {len(PUNKTE)}/4  |  s=speichern  r=reset  f=farben  q=ende",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("Kalibrierung", anzeige)

        # ── Farberkennung ──
        lese_trackbars("Farberkennung")

        # Entzerrtes Bild falls Kalibrierung vorhanden
        if matrix is not None:
            bild = cv2.warpPerspective(frame, matrix, (700, 600))
        else:
            bild = cv2.resize(frame, (700, 600))

        h, w = bild.shape[:2]
        bild_klein = cv2.resize(bild, (w // 2, h // 2))
        th, tw = bild_klein.shape[:2]

        hsv = cv2.cvtColor(bild_klein, cv2.COLOR_BGR2HSV)

        p = hsv_params
        rot1 = cv2.inRange(hsv, (p["r1_min"], p["r_sat"], p["r_val_min"]),
                                 (p["r1_max"], 255, p["r_val_max"]))
        rot2 = cv2.inRange(hsv, (p["r2_min"], p["r_sat"], p["r_val_min"]),
                                 (p["r2_max"], 255, p["r_val_max"]))
        rot  = cv2.bitwise_or(rot1, rot2)
        gelb = cv2.inRange(hsv, (p["g_min"], p["g_sat"], p["g_val_min"]),
                                 (p["g_max"], 255, p["g_val_max"]))

        kernel = np.ones((5, 5), np.uint8)
        if p["erosion"] > 0:
            rot  = cv2.erode(rot,  kernel, iterations=p["erosion"])
            gelb = cv2.erode(gelb, kernel, iterations=p["erosion"])
        if p["dilation"] > 0:
            rot  = cv2.dilate(rot,  kernel, iterations=p["dilation"])
            gelb = cv2.dilate(gelb, kernel, iterations=p["dilation"])

        rot_bgr  = cv2.cvtColor(rot,  cv2.COLOR_GRAY2BGR)
        gelb_bgr = cv2.cvtColor(gelb, cv2.COLOR_GRAY2BGR)

        legende = np.full((th, tw, 3), 40, dtype=np.uint8)
        zeilen = [
            ("TASTEN:",          (200, 200, 200)),
            ("s = Kalibrierung speichern", (100, 255, 100)),
            ("r = Punkte zuruecksetzen",   (100, 255, 100)),
            ("f = Farbwerte speichern",    (100, 255, 100)),
            ("q = Beenden",                (100, 255, 100)),
            ("",                           (0, 0, 0)),
            ("MASKEN:",          (200, 200, 200)),
            ("unten links = Rot",          (80, 80, 255)),
            ("unten rechts = Gelb",        (0, 220, 220)),
            ("",                           (0, 0, 0)),
            ("TRACKBARS:",       (200, 200, 200)),
            ("R1/R2 = Rot Hue-Bereiche",   (150, 150, 255)),
            ("Y = Gelb Hue-Bereich",       (0, 200, 200)),
            ("Sat/Val = Saettigung/Helligkeit", (180, 180, 180)),
            ("Erosion = Rauschen entfernen",   (180, 180, 180)),
            ("Dilation = Flaechen fuellen",    (180, 180, 180)),
        ]
        for i, (text, farbe) in enumerate(zeilen):
            y = 20 + i * 20
            if y > th - 10:
                break
            cv2.putText(legende, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, farbe, 1)

        oben = np.hstack([bild_klein, legende])
        unten = np.hstack([rot_bgr, gelb_bgr])
        combined = np.vstack([oben, unten])
        cv2.imshow("Farberkennung", combined)

        # ── Tastatur ──
        key = cv2.waitKey(1) & 0xFF

        if key == ord('r'):
            PUNKTE.clear()
            matrix = None
            print("Zurückgesetzt.")

        elif key == ord('s'):
            if len(PUNKTE) == MAX_PUNKTE:
                speichere_kalibrierung()
                matrix = berechne_matrix(
                    np.array(PUNKTE, dtype=np.float32)
                )
            else:
                print(f"Noch nicht genug Punkte ({len(PUNKTE)}/4)")

        elif key == ord('f'):
            speichere_farben()

        elif key == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()