import time
import threading
import board
import busio

# Servo configuration
NEUTRAL_ANGLE = 90
MOVE_ANGLE = 0
RELEASE_SERVO = 6
FS90R_STOP_US = 1560  # Calibrated stop pulse width in microseconds

try:
    from adafruit_servokit import ServoKit
    from adafruit_pca9685 import PCA9685

    # Initialize ServoKit for column servos (0-5)
    kit = ServoKit(channels=16)
    for i in range(6):
        kit.servo[i].set_pulse_width_range(500, 2500)
        kit.servo[i].angle = None  # no signal on startup

    # Initialize PCA9685 directly for FS90R on channel 6
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50

    # Stop FS90R on startup
    ticks = int(FS90R_STOP_US / (1_000_000 / 50 / 4096))
    pca.channels[RELEASE_SERVO].duty_cycle = ticks << 4

    SERVOS_AVAILABLE = True
    print("Servo-Hardware erkannt.")

except Exception as e:
    kit = None
    pca = None
    SERVOS_AVAILABLE = False
    print(f"Keine Servo-Hardware gefunden – Programm laeuft ohne Servos. ({e})")


def _set_fs90r_us(pulse_us):
    """Controls FS90R via direct pulse width in microseconds."""
    ticks = int(pulse_us / (1_000_000 / 50 / 4096))
    pca.channels[RELEASE_SERVO].duty_cycle = ticks << 4


def _set_fs90r(speed):
    """speed: -1.0 = full counter-clockwise, 0 = stop, 1.0 = full clockwise"""
    pulse_us = 1500 + (speed * 500)
    _set_fs90r_us(pulse_us)


def stop_fs90r():
    """Stops FS90R at calibrated stop point."""
    _set_fs90r_us(FS90R_STOP_US)


def _run_release_servo():
    """Runs FS90R counter-clockwise for one stone release."""
    _set_fs90r(1.0)
    time.sleep(0.275)
    stop_fs90r()


def execute_move(col):
    """
    Executes a physical move:
    - Moves the column servo, waits 3 seconds, returns to neutral
    - Simultaneously runs the FS90R release servo
    - Column 7 (col=6) has no servo – stone falls through by default
    """
    if not SERVOS_AVAILABLE:
        print(f"[Servo simulation] Zug in Spalte {col + 1}")
        return

    try:
        release_thread = threading.Thread(target=_run_release_servo)
        release_thread.start()

        if col < 6:
            kit.servo[col].angle = MOVE_ANGLE
            time.sleep(3)
            kit.servo[col].angle = NEUTRAL_ANGLE

        else:
            # Column 7 – no servo needed, stone falls through
            time.sleep(3)

        release_thread.join()

    except Exception as e:
        print(f"Servo-Fehler: {e}")


def reset_all_servos():
    """Resets all column servos and stops FS90R."""
    if not SERVOS_AVAILABLE:
        return
    try:
        for i in range(6):
            kit.servo[i].angle = None
        stop_fs90r()
        print("Alle Servos gestoppt.")
    except Exception as e:
        print(f"Fehler beim Zuruecksetzen: {e}")