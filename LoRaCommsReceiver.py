#!/usr/bin/env python3
"""
This program is used to listen to the LoRa transmissions

It is intended to be used as part of the LoRa Monitor, but it can be run independently.
"""

import serial
import logging
import time
import math
import sys


def SetupUART():
    """
    Setup the UART for communications and return an object referencing it. Does:-
    -Initiates serial software
    -Opens the serial port
    -Checks all is ok and returns the object
    """

    ser = serial.Serial('/dev/ttyAMA0', baudrate=230400, parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=3)

    # clear the serial buffer of any left over data
    ser.flushInput()

    if ser.isOpen():
        # if serial comms are setup and the channel is opened
        logging.info ("PI setup complete on channel %d" %ser.fd)
    else:
        logging.critical("Unable to Setup communications")
        sys.exit()

    return ser

def ReadData(fd):
    # read the data back from the serial line and return it as a string to the calling function
    qtydata = wiringpi.serialDataAvail(fd)
    logging.info("Amount of data: %d bytes" % qtydata)
    response = []
    while qtydata > 0:
        # while there is data to be read, read it back
        logging.debug("Reading data back byte:%d" % qtydata)
        # This used to have hex to convert the data to a hex string
        response.append(wiringpi.serialGetchar(fd))
        qtydata = qtydata - 1
    logging.info("Data Packet received: %s" % response)
    logging.debug("Size of data packet received %d" % len(response))
    return response

def ReadChar(fd):
    # read a single character back from the serial line
    qtydata = wiringpi.serialDataAvail(fd)
    logging.info("Amount of data: %s bytes" % qtydata)
    response = 0
    if qtydata > 0:
        logging.debug("Reading data back %d" % qtydata)
        response = wiringpi.serialGetchar(fd)
    return response


def SetupLoRa(fd):
    # send the right commands to setup the LoRa module
    logging.info("Setting up the LoRA module with the various commands")
    # The commands are not yet confirmed, so this is to be added
    ans = fd.write(b"AT!!")
    logging.debug("LoRa AT command AT!! sent:%s" % ans)
    time.sleep(0.1)
    ans = fd.readall()
    logging.debug("LoRa module AT!! response: %s" % list(ans))
    time.sleep(0.1)

    ans = fd.write(b"AT*v")
    logging.debug("LoRa AT command Version(AT*v) sent:%s" % ans)
    time.sleep(0.1)
    ans = fd.readall()
    logging.debug("LoRa module Version(AT*v) response: %s" % list(ans))

    ans = fd.write(b"glora")
    logging.debug("LoRa command glora sent:%s" % ans)
    time.sleep(0.1)
    ans = fd.readall()
    logging.debug("LoRa module glora response: %s" % list(ans))

    ans = fd.write(b"sloramode 1")
    logging.debug("LoRa AT command sloramode 1 sent:%s" % ans)
    time.sleep(0.1)
    ans = fd.readall()
    logging.debug("LoRa module sloramode 1 response: %s" % list(ans))
    return

def Setup():
    """
    Sets up the comms and returns the object that is the connection.
    """
    sp = SetupUART()
    SetupLoRa(sp)
    return sp

def main():
    """
    This is the main entry point for the program when it is being run independently.

    """
    sp = SetupUART()
    SetupLoRa(sp)
    print("Sending messages")
    while(True):
        reply = sp.write(b"AT+X 09")
        logging.debug("Sent length data packet (AT+X) with this length:%s" % reply)
        time.sleep(0.1)
        reply = sp.write(b"Data Sent")
        logging.debug("Sent data packet (Data Sent) with this length:%s" % reply)
        print(".", end="", flush=True)
        time.sleep(0.5)


logging.basicConfig(filename="LoRaCommsReceiver.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":

    main()

