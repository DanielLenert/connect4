import RPi.GPIO as GPIO
import time
import sys
import tty
import termios

SERVO_PIN = 17
STOP = 6.95  # etwas unter 7.5 probieren

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_continuous(speed):
    # speed: -1.0 = volle Kraft links, 0 = stop, 1.0 = volle Kraft rechts
    if speed == 0:
        duty = STOP
    else:
        duty = 7.5 + (speed * 2.5)
    pwm.ChangeDutyCycle(duty)

def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

print("Steuerung:")
print("  a = links")
print("  d = rechts")
print("  s = Spielzug-Sequenz")
print("  q = beenden")

try:
    while True:
        key = get_key()

        if key == 'a':
            set_continuous(-1.0)
            time.sleep(0.3)
            set_continuous(0)

        elif key == 'd':
            set_continuous(1.0)
            time.sleep(0.3)
            set_continuous(0)

        elif key == 's':
            print("Spielzug...")
            set_continuous(1.0)
            time.sleep(0.5)
            set_continuous(0)
            time.sleep(0.3)
            set_continuous(-1.0)
            time.sleep(0.5)
            set_continuous(0)
            print("Fertig")

        elif key == 'q':
            break

finally:
    pwm.stop()
    GPIO.cleanup()
