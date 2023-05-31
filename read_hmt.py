import re
import calibration
from machine import UART, Pin

# Sensor corrections
corr50 = float(calibration.CORRECTIONS['CORR+50'])
corr40 = float(calibration.CORRECTIONS['CORR+40'])
corr30 = float(calibration.CORRECTIONS['CORR+30'])
corr20 = float(calibration.CORRECTIONS['CORR+20'])
corr10 = float(calibration.CORRECTIONS['CORR+10'])
corr0 = float(calibration.CORRECTIONS['CORR+0'])
corrM10 = float(calibration.CORRECTIONS['CORR-10'])
corrM20 = float(calibration.CORRECTIONS['CORR-20'])
corrM30 = float(calibration.CORRECTIONS['CORR-30'])

# HMT sensor UART port setup
# noinspection PyArgumentList
uart = UART(0, 4800, parity=None, stop=1, bits=8, rx=Pin(1), tx=Pin(0),
            timeout=5000)

# Regular expression pattern to match a float or integer number: T= 19.5 'C
pattern = r"[-+]?\d*\.\d+|\d+"


def get_hmt_temp():
    """Request the latest HMT temperature reading from the instrument by
    writing 'send' to the connected UART port. HMT responds with the following
    format: T= 19.5 'C. Note that the HMT must be in 'STOP' mode and 'echo off'
    as well as Serial Interface parameters set to match those above or the
    radio unit to which it is connected."""
    try:
        temp = None
        uart.write(bytearray(b'send\r\n'))
        dataline = uart.readline()
        # dataline = 'T= 19.5 C'
        if dataline is not None:
            match = re.search(pattern, dataline)
            if match:
                raw_temp = round(float(match.group(0)), 1)
                temp = apply_calibration(raw_temp)
        else:
            temp = None
            print('retrying get HMT temp...')
            get_hmt_temp()

        return temp

    except OSError:
        print('error reading from HMT - retrying...')
        get_hmt_temp()
        pass


def apply_calibration(temp):
    """
    Apply the correct instrument calibration adjustment to the
    as read temperature. Calibration coefficients are provided for on the
    instrument calibration certificate for temperatures of -30/-20/-10/0
    /10/20/30/40/50 deg C.
    :param temp: The 'as read' temperature in degrees C from the HMT333
    :return: The 'as read' temperature plus the most appropriate
    instrument calibration coefficient (degrees C).
    """
    if temp >= 45:
        temp = temp + corr50
    elif temp >= 35:
        temp = temp + corr40
    elif temp >= 25:
        temp = temp + corr30
    elif temp >= 15:
        temp = temp + corr20
    elif temp >= 5:
        temp = temp + corr10
    elif temp >= -5:
        temp = temp + corr0
    elif temp >= -15:
        temp = temp + corrM10
    elif temp >= -25:
        temp = temp + corrM20
    else:
        temp = temp + corrM30
    return temp
