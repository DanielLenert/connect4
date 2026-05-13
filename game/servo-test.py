import RPi.GPIO as GPIO
import time
import sys
import tty
import termios

SERVO_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_angle(angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.3)
    pwm.ChangeDutyCycle(0)
    return angle

def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

print("Steuerung:")
print("  a = links (-20)")
print("  d = rechts (+20)")
print("  s = Spielzug-Sequenz")
print("  q = beenden")

current_angle = 90
set_angle(current_angle)

try:
    while True:
        key = get_key()

        if key == 'a':
            current_angle -= 20
            current_angle = set_angle(current_angle)
            print(f"Winkel: {current_angle}°")

        elif key == 'd':
            current_angle += 20
            current_angle = set_angle(current_angle)
            print(f"Winkel: {current_angle}°")

        elif key == 's':
            print("Spielzug...")
            set_angle(0)
            time.sleep(0.5)
            set_angle(90)
            print("Fertig")

        elif key == 'q':
            break

finally:
    pwm.stop()
    GPIO.cleanup()