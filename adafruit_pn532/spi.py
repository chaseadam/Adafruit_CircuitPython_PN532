# SPDX-FileCopyrightText: 2015-2018 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
``adafruit_pn532.spi``
====================================================

This module will let you communicate with a PN532 RFID/NFC shield or breakout
using SPI.

* Author(s): Original Raspberry Pi code by Tony DiCola, CircuitPython by ladyada,
             refactor by Carter Nelson

"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PN532.git"

import time
from micropython import const
from adafruit_pn532.adafruit_pn532 import PN532

from machine import SPI, Pin

_SPI_STATREAD = const(0x02)
_SPI_DATAWRITE = const(0x01)
_SPI_DATAREAD = const(0x03)
_SPI_READY = const(0x01)


def reverse_bit(num):
    """Turn an LSB byte to an MSB byte, and vice versa. Used for SPI as
    it is LSB for the PN532, but 99% of SPI implementations are MSB only!"""
    result = 0
    for _ in range(8):
        result <<= 1
        result += num & 1
        num >>= 1
    return result


class PN532_SPI(PN532):
    """Driver for the PN532 connected over SPI. Pass in a hardware or bitbang
    SPI device & chip select digitalInOut pin. Optional IRQ pin (not used),
    reset pin and debugging output."""

    def __init__(self, spi, cs_pin, *, irq=None, reset=None, debug=False):
        """Create an instance of the PN532 class using SPI"""
        self.debug = debug
        self._cs_pin = cs_pin
        # https://docs.micropython.org/en/latest/esp32/quickref.html#hardware-spi-bus
        #vspi = SPI(2, baudrate=100000, polarity=0, phase=0, bits=8, firstbit=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
        self._spi = spi
        super().__init__(debug=debug, irq=irq, reset=reset)

    def _wakeup(self):
        """Send any special commands/data to wake up PN532"""
        if self._reset_pin:
            self._reset_pin(1)
            time.sleep(0.01)
        spi = self._spi
        self._cs_pin(0)
        spi.write(bytearray([0x00]))  # pylint: disable=no-member
        self._cs_pin(1)
        time.sleep(0.01)
        self.low_power = False
        self.SAM_configuration()  # Put the PN532 back in normal mode

    def _wait_ready(self, timeout=1):
        """Poll PN532 if status byte is ready, up to `timeout` seconds"""
        status_cmd = bytearray([reverse_bit(_SPI_STATREAD), 0x00])
        status_response = bytearray([0x00, 0x00])
        timestamp = time.ticks_ms()
        spi = self._spi
        while (time.ticks_diff(time.ticks_ms(), timestamp)) < timeout*1000:
            self._cs_pin(0)
            spi.write_readinto(
                status_cmd, status_response
            )  # pylint: disable=no-member
            self._cs_pin(1)
            if reverse_bit(status_response[1]) == 0x01:  # LSB data is read in MSB
                return True  # Not busy anymore!
            time.sleep_ms(10)  # pause a bit till we ask again
        # We timed out!
        return False

    def _read_data(self, count):
        """Read a specified count of bytes from the PN532."""
        # Build a read request frame.
        frame = bytearray(count + 1)
        # Add the SPI data read signal byte, but LSB'ify it
        frame[0] = reverse_bit(_SPI_DATAREAD)

        spi = self._spi
        self._cs_pin(0)
        spi.write_readinto(frame, frame)  # pylint: disable=no-member
        self._cs_pin(1)
        for i, val in enumerate(frame):
            frame[i] = reverse_bit(val)  # turn LSB data to MSB
        if self.debug:
            print("Reading: ", [hex(i) for i in frame[1:]])
        return frame[1:]

    def _write_data(self, framebytes):
        """Write a specified count of bytes to the PN532"""
        # start by making a frame with data write in front,
        # then rest of bytes, and LSBify it
        rev_frame = [reverse_bit(x) for x in bytes([_SPI_DATAWRITE]) + framebytes]
        if self.debug:
            print("Writing: ", [hex(i) for i in rev_frame])
        spi = self._spi
        self._cs_pin(0)
        spi.write(bytes(rev_frame))  # pylint: disable=no-member
        self._cs_pin(1)
