# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This example shows connecting to the PN532 with I2C (requires clock
stretching support), SPI, or UART. SPI is best, it uses the most pins but
is the most reliable and universally supported.
After initialization, try waving various 13.56MHz RFID cards over it!
"""

from adafruit_pn532.spi import PN532_SPI
from machine import SPI, Pin
from micropython import const

vspi = SPI(2, baudrate=100000, polarity=0, phase=0, bits=8, firstbit=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
cs_pin = Pin(5, mode=Pin.OUT, value=1)
pn532 = PN532_SPI(vspi, cs_pin, debug=False)

ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()

print("Waiting for RFID/NFC card to write to!")
while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=0.5)
    print(".", end="")
    # Try again if no card is available.
    if uid is not None:
        break

print("")
print("Found card with UID:", [hex(i) for i in uid])

# Set 4 bytes of block to 0xFEEDBEEF
data = bytearray(4)
data[0:4] = b"\xFE\xED\xBE\xEF"
# Write 4 byte block.
pn532.ntag2xx_write_block(6, data)
# Read block #6
ntag2xx_block = pn532.ntag2xx_read_block(6)
if ntag2xx_block is not None:
    print(
        "Wrote to block 6, now trying to read that data:",
        [hex(x) for x in ntag2xx_block],
    )
else:
    print("Read failed - did you remove the card?")
