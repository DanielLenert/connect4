import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

i2c = busio.I2C(board.SCL, board.SDA)
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)

font = ImageFont.load_default()


def show_text(line1, line2=""):
    image = Image.new("1", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
    draw.text((5, 15), line1, font=font, fill=255)
    if line2:
        draw.text((5, 35), line2, font=font, fill=255)
    display.image(image)
    display.show()


def clear_display():
    display.fill(0)
    display.show()


def zeige_start():
    show_text("Bitte beginnen", "mit rotem Stein.")


def zeige_ki_denkt(col):
    show_text("KI denkt...", f"Naechster Zug: Spalte {col + 1}")


def zeige_spieler_dran():
    show_text("Sie sind", "am Zug.")


def zeige_spieler_gewinnt():
    show_text("Spieler gewinnt.")


def zeige_ki_gewinnt():
    show_text("Maschine gewinnt.")
