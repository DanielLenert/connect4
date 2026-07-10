import time
import threading

# Servo configuration
NEUTRAL_ANGLE = 90
MOVE_ANGLE = 0       
RELEASE_SERVO = 6      # FS90R channel
FS90R_STOP = 0.1       # Calibrated stop value for FS90R

try:
    from adafruit_servokit import ServoKit
    kit = ServoKit(channels=16)
    
    # Set full pulse width range for column servos (0-5)
    # Standard: 1000-2000µs, extended: 500-2500µs for full range
    for i in range(6):
        kit.servo[i].set_pulse_width_range(500, 2500)
    
    kit.continuous_servo[RELEASE_SERVO].throttle = FS90R_STOP
    SERVOS_AVAILABLE = True
    print("Servo-Hardware erkannt.")
except Exception:
    kit = None
    SERVOS_AVAILABLE = False
    print("Keine Servo-Hardware gefunden – Programm laeuft ohne Servos.")


def _run_release_servo():
    """Runs the FS90R release servo counter-clockwise for one stone."""
    kit.continuous_servo[RELEASE_SERVO].throttle = -1.0
    time.sleep(0.275)
    kit.continuous_servo[RELEASE_SERVO].throttle = FS90R_STOP


def execute_move(col):
    """Executes a physical move:
    - Moves the column servo 60 degrees to the right, waits 3 seconds, returns
    - Simultaneously runs the release servo (FS90R) for the stone
    """
    if not SERVOS_AVAILABLE:
        print(f"[Servo simulation] Zug in Spalte {col + 1}")
        return

    try:
        # Start release servo in a separate thread so it runs simultaneously
        release_thread = threading.Thread(target=_run_release_servo)
        release_thread.start()

        # Move column servo 60 degrees to the right
        kit.servo[col].angle = MOVE_ANGLE
        time.sleep(3)
        kit.servo[col].angle = NEUTRAL_ANGLE

        # Wait for release servo to finish
        release_thread.join()

    except Exception as e:
        print(f"Servo-Fehler: {e}")


def reset_all_servos():
    """Resets all column servos to neutral and stops release servo."""
    if not SERVOS_AVAILABLE:
        return
    try:
        for i in range(6):
            kit.servo[i].angle = NEUTRAL_ANGLE
        kit.continuous_servo[RELEASE_SERVO].throttle = FS90R_STOP
    except Exception as e:
        print(f"Fehler beim Zuruecksetzen: {e}")