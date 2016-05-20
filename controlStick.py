#! /usr/bin/python



"""
================================================================================
TITLE:    controlStick

AUTHOR:   David Leclerc

VERSION:  0.1

DATE:     19.05.2016

LICENSE:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

OVERVIEW: This is a script that allows to retrieve informations from a MiniMed
          insulin pump, using the CareLink USB stick of Medtronic. It is based
          on the PySerial library and is a work of reverse-engineering the USB
          communication protocols of said USB stick.

NOTES:    ...
================================================================================
"""



# LIBRARIES
import serial
import os
import sys
import time
import datetime
import numpy as np



# USER-DEFINED LIBRARIES
import lib



# DEFINITIONS
LOGS_ADDRESS = "/home/david/Documents/MeinKPS/stickLogs.txt"
NOW          = datetime.datetime.now()



class stick:

    # STICK CHARACTERISTICS
    VENDOR                  = 0x0a21
    PRODUCT                 = 0x8001

    # INITIALIZATION RESPONSE INDICES
    ACK_INDEX               = 0
    NAK_INDEX               = 33
    STATUS_INDEX            = 1
    SERIAL_INDEX            = range(3, 6)
    FREQUENCY_INDEX    = 8
    DESCRIPTION_INDEX       = range(9, 19)
    VERSION_INDEX           = range(19, 21)
    INTERFACES_INDEX        = range(22, 64)

    # STATUS RESPONSE INDICES
    SIGNAL_INDEX            = 3

    # STICK CONSTANTS
    SIGNAL_THRESHOLD        = 150
    N_WRITE_ATTEMPTS        = 3
    N_READ_ATTEMPTS         = 3
    N_READ_BYTES            = 64
    SLEEP_TIME              = 0.1
    RADIOFREQUENCIES        = {0: 916.5, 1: 868.35, 255: 916.5}
    INTERFACES              = {1: "Paradigm RF", 3: "USB"}



    def getHandle(self):

        """
        ========================================================================
        GETHANDLE
        ========================================================================

        ...
        """

        # Generate serial port
        os.system("sudo modprobe --first-time usbserial"
            + " vendor=" + str(self.VENDOR)
            + " product=" + str(self.PRODUCT))

        # Generate serial port handle
        self.handle = serial.Serial()
        self.handle.port = "/dev/ttyUSB0"
        self.handle.baudrate = 9600
        self.handle.xonxoff = False
        self.handle.rtscts = True
        self.handle.dsrdtr = True
        self.handle.timeout = 0.5

        # Open serial port
        self.handle.open()
        self.handle.flushInput()
        self.handle.flushOutput()



    def start(self):

        """
        ========================================================================
        START
        ========================================================================

        ...
        """

        # Generate handle for the stick
        self.getHandle()

        # Ask for stick infos
        self.getInfos()

        # Ask for signal strength
        self.getSignalStrength()



    def stop(self):

        """
        ========================================================================
        STOP
        ========================================================================

        ...
        """    

        # Close serial port
        self.handle.close()

        # Remove serial port
        os.system("sudo modprobe -r usbserial")



    def getRawResponse(self):

        """
        ========================================================================
        GETRAWRESPONSE
        ========================================================================

        ...
        """

        # Read command to send to stick
        print "Request to send: " + str(self.request)

        # Initialize stick response
        self.raw_response = ""

        # Ask for response from stick until we get one
        for i in range(self.N_WRITE_ATTEMPTS):

            # Send stick command
            self.handle.write(bytearray(self.request))

            for j in range(self.N_READ_ATTEMPTS):
                if len(self.raw_response) == 0:

                    # Keep track of number of reading trials
                    print "Write: " + \
                          str(i + 1) + "/" + str(self.N_WRITE_ATTEMPTS) + \
                          "\t" + \
                          "Read: " + \
                          str(j + 1) + "/" + str(self.N_READ_ATTEMPTS)

                    # Wait for response
                    time.sleep(self.SLEEP_TIME)

                    # Read stick response
                    self.raw_response = self.handle.read(self.N_READ_BYTES)

                else:
                    break

        # If no response at all was received, quit
        if len(self.raw_response) == 0:
            sys.exit("Unable to read from stick. :-(")



    def parseRawResponse(self):

        """
        ========================================================================
        PARSERAWRESPONSE
        ========================================================================

        ...
        """

        # Vectorize raw response
        self.raw_response = [x for x in self.raw_response]

        # Convert stick response to various formats for more convenience
        self.response = np.vectorize(ord)(self.raw_response)
        self.response_hex = np.vectorize(hex)(self.response)
        self.response_str = np.vectorize(chr)(self.response)

        # Pad hexadecimal formatted response
        self.response_hex = np.vectorize(lib.padHexadecimal)(self.response_hex)

        # Correct unreadable characters in string stick response
        self.response_str[self.response < 32] = "."
        self.response_str[self.response > 126] = "."



    def sendRequest(self, request):

        """
        ========================================================================
        SENDREQUEST
        ========================================================================

        ...
        """

        # Save request in stick instance
        self.request = request

        # Send command to stick and wait for response
        self.getRawResponse()

        # Parse response of stick
        self.parseRawResponse()

        # Print stick response in readable formats
        for i in range(8):
            print " ".join(self.response_hex[i * 8 : (i + 1) * 8]) + \
                  "\t" + \
                  "".join(self.response_str[i * 8 : (i + 1) * 8])

        #print self.response



    def getInfos(self):

        """
        ========================================================================
        GETINFOS
        ========================================================================

        ...
        """

        # Ask stick for its infos
        self.sendRequest([4, 0, 0])

        # Get NAK
        self.nak         = self.response[self.NAK_INDEX]

        # Make sure there was no error
        if self.nak == 1:
            print "There was an error during initialization! Retrying..."
            self.getInfos()



        # Get ACK
        self.ack         = self.response[self.ACK_INDEX]

        # Get status
        self.status      = self.response_str[self.STATUS_INDEX]

        # Get serial number
        self.serial      = self.response_hex[self.SERIAL_INDEX]
        self.serial      = "".join(x[2:] for x in self.serial)

        # Get radiofrequency
        self.frequency   = self.response[self.FREQUENCY_INDEX]
        self.frequency   = self.RADIOFREQUENCIES[self.frequency]

        # Get description of communication protocol
        self.description = self.response_str[self.DESCRIPTION_INDEX]
        self.description = "".join(self.description)

        # Get software version
        self.version     = self.response[self.VERSION_INDEX]
        self.version     = self.version[0] + 0.01 * self.version[1]

        # Get interfaces
        self.interfaces  = self.response[self.INTERFACES_INDEX]
        self.interfaces  = np.trim_zeros(self.interfaces, "b")
        self.interfaces  = list(self.interfaces)

        # Loop over all found interfaces
        for i in range(len(self.interfaces) / 2):
            self.interfaces[2 * i + 1] = self.INTERFACES[self.interfaces[2 * i + 1]]

        # Print infos
        print "ACK: " + str(self.ack)
        print "Status: " + self.status
        print "Serial: " + self.serial
        print "Radiofrequency: " + str(self.frequency) + " MHz"
        print "Description: " + self.description
        print "Version: " + str(self.version)
        print "Interfaces: " + str(self.interfaces)
        print



    def getSignalStrength(self):

        """
        ========================================================================
        GETSIGNALSTRENGTH
        ========================================================================

        ...
        """

        self.signal = 0
        self.n_signal_read_attempts = 0

        # Loop until signal found is sufficiently strong
        while self.signal < self.SIGNAL_THRESHOLD:
            self.sendRequest([6, 0, 0])
            self.signal = self.response[self.SIGNAL_INDEX]
            self.n_signal_read_attempts += 1

            print "Signal read: " + str(self.n_signal_read_attempts) + "/-"
            print "Signal strength: " + str(self.signal)

        print



    def getUSBState(self):

        """
        ========================================================================
        GETUSBSTATE
        ========================================================================

        ...
        """

        # Ask stick for its USB state
        self.sendRequest([5, 1, 0])

        # Get errors
        self.errors_crc = self.response[3]
        self.errors_seq = self.response[4]
        self.errors_nak = self.response[5]
        self.errors_timeout = self.response[6]
        self.packets_received = self.response[7:11]
        self.packets_sent = self.response[11:15]

        self.packets_received = (
                                    self.packets_received[0] << 24 |
                                    self.packets_received[1] << 16 |
                                    self.packets_received[2] << 8 |
                                    self.packets_received[3]
                                )
        self.packets_sent =     (
                                    self.packets_received[0] << 24 |
                                    self.packets_received[1] << 16 |
                                    self.packets_received[2] << 8 |
                                    self.packets_received[3]
                                )

        print self.errors_crc
        print self.errors_seq
        print self.errors_nak
        print self.errors_timeout
        print self.packets_received
        print self.packets_sent
        print



    def getRFState(self):

        """
        ========================================================================
        GETRFSTATE
        ========================================================================

        ...
        """

        # Ask stick for its USB state
        self.sendRequest([5, 0, 0])

        # Get errors
        self.errors_crc = self.response[3]
        self.errors_seq = self.response[4]
        self.errors_nak = self.response[5]
        self.errors_timeout = self.response[6]
        self.packets_received = self.response[7:11]
        self.packets_sent = self.response[11:15]

        self.packets_received = (
                                    self.packets_received[0] << 24 |
                                    self.packets_received[1] << 16 |
                                    self.packets_received[2] << 8 |
                                    self.packets_received[3]
                                )
        self.packets_sent =     (
                                    self.packets_received[0] << 24 |
                                    self.packets_received[1] << 16 |
                                    self.packets_received[2] << 8 |
                                    self.packets_received[3]
                                )

        print self.errors_crc
        print self.errors_seq
        print self.errors_nak
        print self.errors_timeout
        print self.packets_received
        print self.packets_sent
        print



    def getRFBufferState(self):

        """
        ========================================================================
        GETRFBUFFERSTATE
        ========================================================================

        ...
        """

        # Ask stick its general status
        self.sendRequest([3, 0, 0])

        print



def main():

    """
    ============================================================================
    MAIN
    ============================================================================

    This is the main loop to be executed by the script.
    """

    # Instanciate a stick for me
    my_stick = stick()

    # Start my stick
    my_stick.start()
    
    # Count packets on USB side of stick
    my_stick.getUSBState()

    # Count packets on RF transmitter side of stick
    my_stick.getRFState()

    # Get stick RF buffer status (waiting to download)
    #my_stick.getRFBufferState()

    # Stop my stick
    my_stick.stop()

    # End of script
    print "Done!"



# Run script when called from terminal
if __name__ == "__main__":
    main()
