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

print("Waiting for RFID/NFC card to read from!")
while True:
    # Check if a card is available to read
    uid = pn532.read_passive_target(timeout=0.5)
    print(".", end="")
    # Try again if no card is available.
    if uid is not None:
        break

print("")
print("Found card with UID:", [hex(i) for i in uid])

# Read blocks
uri_blocks = []
# noticed spotify uri just happens to start at block 7
for i in range(7,16):
    ntag2xx_block = pn532.ntag2xx_read_block(i)
    if ntag2xx_block is not None:
        # test if empty tag
        if not ntag2xx_block == bytearray([0,0,0,0]):
            print(
                    "read block ", i,
                [hex(x) for x in ntag2xx_block],
            )
            # TODO should probably try to do the decode here
            uri_blocks += ntag2xx_block
    else:
        print("Read failed - did you remove the card?")

uri_bytes = bytearray(uri_blocks)
# very crude NDEF parsing
# if it starts with "en" then subtract 2 bytes, otherwise, subtrack 4 bytes
if uri_bytes[:2] == bytearray(b'en'):
    uri_string = uri_bytes[2:-2].decode()
else:
    uri_string = uri_bytes[:-4].decode()
print(uri_string)
