from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

# Servo 0 testen
kit.servo[0].angle = 0
time.sleep(1)
kit.servo[0].angle = 90
time.sleep(1)
kit.servo[0].angle = 180
time.sleep(1)