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

    # Trackbars für Kreiserkennung auf dem Graubild
    cv2.createTrackbar("Min Radius",  "Vier Gewinnt Erkennung", 8,   100, lambda x: None)
    cv2.createTrackbar("Max Radius",  "Vier Gewinnt Erkennung", 25,  100, lambda x: None)
    cv2.createTrackbar("Min Dist",    "Vier Gewinnt Erkennung", 20,  100, lambda x: None)
    cv2.createTrackbar("Param1",      "Vier Gewinnt Erkennung", 50,  200, lambda x: None)
    cv2.createTrackbar("Param2",      "Vier Gewinnt Erkennung", 30,  100, lambda x: None)
    cv2.createTrackbar("Blur",        "Vier Gewinnt Erkennung", 4,   15,  lambda x: None)

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        h, w = frame.shape[:2]
        img_small = cv2.resize(frame, (w // 2, h // 2))
        th, tw = img_small.shape[:2]

        # Graubild für Kreiserkennung
        gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)

        min_radius = cv2.getTrackbarPos("Min Radius", "Vier Gewinnt Erkennung")
        max_radius = cv2.getTrackbarPos("Max Radius", "Vier Gewinnt Erkennung")
        min_dist   = cv2.getTrackbarPos("Min Dist",   "Vier Gewinnt Erkennung")
        param1_val = cv2.getTrackbarPos("Param1",     "Vier Gewinnt Erkennung")
        param2_val = cv2.getTrackbarPos("Param2",     "Vier Gewinnt Erkennung")
        blur_val   = cv2.getTrackbarPos("Blur",       "Vier Gewinnt Erkennung")

        # Blur muss ungerade sein für GaussianBlur
        blur_k = blur_val if blur_val % 2 == 1 else blur_val + 1
        blur_k = max(1, blur_k)
        geglaettet = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)

        # Sichere Mindestwerte
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

        kreis_bild = img_small.copy()

        if kreise is not None:
            kreise = np.uint16(np.around(kreise))
            for kreis in kreise[0, :]:
                cx, cy, r = int(kreis[0]), int(kreis[1]), int(kreis[2])
                cv2.circle(kreis_bild, (cx, cy), r, (0, 255, 0), 2)
                cv2.circle(kreis_bild, (cx, cy), 2, (255, 255, 255), 3)

        # Graubild in BGR für Anzeige nebeneinander
        gray_bgr = cv2.cvtColor(geglaettet, cv2.COLOR_GRAY2BGR)

        combined = np.hstack([img_small, gray_bgr, kreis_bild])
        cv2.imshow("Vier Gewinnt Erkennung", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    picam2.stop()
    cv2.destroyAllWindows()

detect_board()