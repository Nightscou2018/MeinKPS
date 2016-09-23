#! /usr/bin/python



"""
================================================================================
Title:    lib

Author:   David Leclerc

Version:  0.1

Date:     24.05.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: This is a script that contains user-defined functions to make the
          communications with the CareLink stick easier.

Notes:    ...
================================================================================
"""



# LIBRARIES
import numpy as np



def derivate(x, dt):

        """
        ========================================================================
        DERIVATE
        ========================================================================
        """

        # Vectorize input
        x = np.array(x)

        # Make sure the derivative is a float at the end
        dt = float(dt)

        # Evaluate derivative
        dx_dt = (x[1:] - x[:-1]) / dt

        return dx_dt



def parseTime(x):

        """
        ========================================================================
        PARSETIME
        ========================================================================
        """

        second = x[0] & 63
        minute = x[1] & 63
        hour = x[2] & 31
        day = x[3] & 31
        month = ((x[0] & 192) >> 4) | ((x[1] & 192) >> 6)
        year = (x[4] & 127) + 2000

        return [year, month, day, hour, minute, second]



def encodeSerialNumber(x):

        """
        ========================================================================
        ENCODESERIALNUMBER
        ========================================================================
        """

        return [ord(i) for i in str(x).decode("HEX")]



def padHex(x):

        """
        ========================================================================
        PADHEX
        ========================================================================

        Pad an hexadecimal string with zeros.
        """

        return "0x" + x[2:].zfill(2)



def convertBytes(x):

        """
        ========================================================================
        CONVERTBYTES
        ========================================================================

        This is a function that converts a number expressed in an array of bytes
        to its decimal equivalent.
        """

        # Vectorize input
        x = np.array(x)

        return sum(x * 256 ** np.arange(len(x) - 1, -1, -1))



def getByte(x, N):

        """
        ========================================================================
        GETBYTE
        ========================================================================

        This is a function that extracts the Nth byte of a number x (1 byte =
        8 bits = 256 states).
        """

        return x / 256 ** N % 256



def computeCRC8(x):

        """
        ========================================================================
        COMPUTECRC8
        ========================================================================
        """

        # Define CRC8 lookup table
        lookup_table = [0, 155, 173, 54, 193, 90, 108, 247,
                        25, 130, 180, 47, 216, 67, 117, 238,
                        50, 169, 159, 4, 243, 104, 94, 197,
                        43, 176, 134, 29, 234, 113, 71, 220,
                        100, 255, 201, 82, 165, 62, 8, 147,
                        125, 230, 208, 75, 188, 39, 17, 138,
                        86, 205, 251, 96, 151, 12, 58, 161,
                        79, 212, 226, 121, 142, 21, 35, 184,
                        200, 83, 101, 254, 9, 146, 164, 63,
                        209, 74, 124, 231, 16, 139, 189, 38,
                        250, 97, 87, 204, 59, 160, 150, 13,
                        227, 120, 78, 213, 34, 185, 143, 20,
                        172, 55, 1, 154, 109, 246, 192, 91,
                        181, 46, 24, 131, 116, 239, 217, 66,
                        158, 5, 51, 168, 95, 196, 242, 105,
                        135, 28, 42, 177, 70, 221, 235, 112,
                        11, 144, 166, 61, 202, 81, 103, 252,
                        18, 137, 191, 36, 211, 72, 126, 229,
                        57, 162, 148, 15, 248, 99, 85, 206,
                        32, 187, 141, 22, 225, 122, 76, 215,
                        111, 244, 194, 89, 174, 53, 3, 152,
                        118, 237, 219, 64, 183, 44, 26, 129,
                        93, 198, 240, 107, 156, 7, 49, 170,
                        68, 223, 233, 114, 133, 30, 40, 179,
                        195, 88, 110, 245, 2, 153, 175, 52,
                        218, 65, 119, 236, 27, 128, 182, 45,
                        241, 106, 92, 199, 48, 171, 157, 6,
                        232, 115, 69, 222, 41, 178, 132, 31,
                        167, 60, 10, 145, 102, 253, 203, 80,
                        190, 37, 19, 136, 127, 228, 210, 73,
                        149, 14, 56, 163, 84, 207, 249, 98,
                        140, 23, 33, 186, 77, 214, 224, 123]

        # Initialize CRC
        crc = 0

        # Look for CRC in table
        for i in range(len(x)):
            crc = lookup_table[crc ^ getByte(x[i], 0)]

        # Return CRC
        return crc
