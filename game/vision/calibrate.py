import cv2
import numpy as np
import json
from picamera2 import Picamera2

PUNKTE = []
MAX_PUNKTE = 4

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(PUNKTE) < MAX_PUNKTE:
        PUNKTE.append([x, y])
        print(f"Punkt {len(PUNKTE)}: ({x}, {y})")


def calibrate():
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(
        main={"format": "BGR888", "size": (640, 480)}
    ))
    picam2.start()

    cv2.namedWindow("Kalibrierung")
    cv2.setMouseCallback("Kalibrierung", mouse_callback)

    print("Klicke die 4 Ecken des Spielfelds in dieser Reihenfolge:")
    print("1. oben links  2. oben rechts  3. unten rechts  4. unten links")
    print("Druecke 'r' um zuruckzusetzen, 's' um zu speichern, 'q' zum Beenden ohne Speichern")

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        anzeige = frame.copy()

        # Bereits gesetzte Punkte einzeichnen
        for i, p in enumerate(PUNKTE):
            cv2.circle(anzeige, tuple(p), 6, (0, 255, 0), -1)
            cv2.putText(anzeige, str(i + 1), (p[0] + 10, p[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Linien zwischen den Punkten zeichnen wenn schon mehrere gesetzt sind
        if len(PUNKTE) >= 2:
            for i in range(len(PUNKTE) - 1):
                cv2.line(anzeige, tuple(PUNKTE[i]), tuple(PUNKTE[i + 1]), (0, 255, 0), 2)
        if len(PUNKTE) == MAX_PUNKTE:
            cv2.line(anzeige, tuple(PUNKTE[3]), tuple(PUNKTE[0]), (0, 255, 0), 2)

        status = f"Punkte gesetzt: {len(PUNKTE)}/{MAX_PUNKTE}"
        cv2.putText(anzeige, status, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Kalibrierung", anzeige)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('r'):
            PUNKTE.clear()
            print("Zuruckgesetzt.")

        elif key == ord('s'):
            if len(PUNKTE) == MAX_PUNKTE:
                daten = {"punkte": PUNKTE}
                with open("calibration.json", "w") as f:
                    json.dump(daten, f, indent=2)
                print("Gespeichert in calibration.json:", PUNKTE)
                break
            else:
                print(f"Noch nicht genug Punkte ({len(PUNKTE)}/{MAX_PUNKTE})")

        elif key == ord('q'):
            print("Abgebrochen, nichts gespeichert.")
            break

    picam2.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    calibrate()