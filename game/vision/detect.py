import cv2
import numpy as np
from picamera2 import Picamera2

def detect_board():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (640, 480)}
    ))
    picam2.start()

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

    # Neue Trackbars für die Kreiserkennung
    cv2.createTrackbar("Min Radius",  "Vier Gewinnt Erkennung", 8,   100, lambda x: None)
    cv2.createTrackbar("Max Radius",  "Vier Gewinnt Erkennung", 25,  100, lambda x: None)
    cv2.createTrackbar("Min Dist",    "Vier Gewinnt Erkennung", 20,  100, lambda x: None)
    cv2.createTrackbar("Param2",      "Vier Gewinnt Erkennung", 15,  100, lambda x: None)

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        h, w = frame.shape[:2]
        img_small = cv2.resize(frame, (w // 3, h // 3))
        th, tw = img_small.shape[:2]

        hsv = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)

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

        min_radius = cv2.getTrackbarPos("Min Radius", "Vier Gewinnt Erkennung")
        max_radius = cv2.getTrackbarPos("Max Radius", "Vier Gewinnt Erkennung")
        min_dist   = cv2.getTrackbarPos("Min Dist",   "Vier Gewinnt Erkennung")
        param2_val = cv2.getTrackbarPos("Param2",     "Vier Gewinnt Erkennung")

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

        # Kombinierte Maske (rot + gelb) für die Kreiserkennung
        kombiniert_maske = cv2.bitwise_or(rot_maske, gelb_maske)
        # Leicht weichzeichnen hilft HoughCircles
        geglaettet = cv2.GaussianBlur(kombiniert_maske, (9, 9), 2)

        # Sicherstellen, dass Parameter gültig sind (Param2 und minDist > 0)
        param2_safe = max(1, param2_val)
        min_dist_safe = max(1, min_dist)
        max_radius_safe = max(min_radius + 1, max_radius)

        kreise = cv2.HoughCircles(
            geglaettet,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_dist_safe,
            param1=50,
            param2=param2_safe,
            minRadius=min_radius,
            maxRadius=max_radius_safe
        )

        # Ausgabebild für die Kreis-Visualisierung (Kopie des Originalbilds)
        kreis_bild = img_small.copy()

        if kreise is not None:
            kreise = np.uint16(np.around(kreise))
            for kreis in kreise[0, :]:
                cx, cy, r = int(kreis[0]), int(kreis[1]), int(kreis[2])

                # Farbe an der Kreismitte bestimmen: rot oder gelb?
                ist_rot  = rot_maske[cy, cx]  > 0 if 0 <= cy < th and 0 <= cx < tw else 0
                ist_gelb = gelb_maske[cy, cx] > 0 if 0 <= cy < th and 0 <= cx < tw else 0

                if ist_rot:
                    farbe = (0, 0, 255)      # Rot in BGR
                elif ist_gelb:
                    farbe = (0, 255, 255)    # Gelb in BGR
                else:
                    farbe = (0, 255, 0)      # Grün = unklare Zuordnung

                cv2.circle(kreis_bild, (cx, cy), r, farbe, 2)
                cv2.circle(kreis_bild, (cx, cy), 2, (255, 255, 255), 3)

        rot_bgr  = cv2.cvtColor(rot_maske,  cv2.COLOR_GRAY2BGR)
        gelb_bgr = cv2.cvtColor(gelb_maske, cv2.COLOR_GRAY2BGR)

        # Oben: Original links, Kreiserkennung rechts (ersetzt den Platzhalter)
        oben     = np.hstack([img_small, kreis_bild])
        unten    = np.hstack([rot_bgr,   gelb_bgr])
        combined = np.vstack([oben, unten])

        cv2.imshow("Vier Gewinnt Erkennung", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()

detect_board()