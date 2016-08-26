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

# The dealy between send and receive
SRDELAY = 0.1

# The delay between receiving one message and sending the next
INTERDELAY = 0.5

def SetupUART():
    """
    Setup the UART for communications and return an object referencing it. Does:-
    -Initiates serial software
    -Opens the serial port
    -Checks all is ok and returns the object
    """

    ser = serial.Serial('/dev/ttyAMA0', baudrate=57600, parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)

    time.sleep(1)

    # clear the serial buffer of any left over data
    ser.flushInput()

    if ser.isOpen():
        # if serial comms are setup and the channel is opened
        logging.info ("PI setup complete on channel %d as : %s" % (ser.fd, ser.getSettingsDict))
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

def WriteData(fd,message):
    # This routine will take the given data and write it to the serial port
    # returns the data length or fail
#TODO: Need to put a try loop around this
    # add the control characters
    send = message + '\r\n'
    ans = fd.write(send.encode('utf-8'))
    logging.info("Message >%s< sent as >%a< and got this reply:%s" % (message, send, ans))
    return ans

def ReadData(fd, length=-1):
    # Read the data from the serial port of known length
    # If length is not known, assume all data

    if length != -1:
        ans = fd.read(length)
    else:
        ans = fd.readall()
        length = 'unknown'
#TODO: Strip off returned characters
    logging.debug("Read data of length %s from the Serial port: %a" % (length, ans))
    return ans

def SendConfigCommand(fd, command):
    # This function sends data and gets the reply for the various configuration commands.

    ans = WriteData(fd, command)
    time.sleep(SRDELAY)
    ans = ReadData(fd)

    time.sleep(INTERDELAY)
    return

def SetupLoRa(fd):
    # send the right commands to setup the LoRa module
    logging.info("Setting up the LoRA module with the various commands")
    # The commands are not yet confirmed, so this is to be added
    #ans = fd.write(b"AT!!\r\n")
    #logging.debug("LoRa AT command AT!! sent:%s" % ans)
    #time.sleep(1)
    #ans = fd.readall()
    #logging.debug("LoRa module AT!! response: %s" % ans)
    #time.sleep(1)

    #fd.flushInput()
    #time.sleep(1)

    SendConfigCommand(fd, "AT*v")
    SendConfigCommand(fd, "glora")
    SendConfigCommand(fd, "sloramode 1")
    return

def Setup():
    """
    Sets up the comms and returns the object that is the connection.
    """
    sp = SetupUART()
    SetupLoRa(sp)
    return sp

def SendRadioData(fd, message):
    # Takes the given data and sends it over the radio network

    # First determine the size of the data, adding 1 for the control character at the end
    length = len(message) + 1
#TODO: If length is greater than 255, abort
    send = 'AT+X ' + format(length, '02X')
    reply = WriteData(fd, send)
    time.sleep(SRDELAY)
#TODO: Check the response, it should be $ indicating it is ready for the data
    ReadData(fd)

    time.sleep(SRDELAY)
    reply = WriteData(fd, message)

#TODO: Need to check the reply to see if it is ok, should be \r\nOK00> - remembering the \r\n is being stripped off
    ReadData(fd)
    return

def RadioDataAvailable(fd):
    # checks to see if there is radio data available to be read.
    # returns zero if no data
    data_length = 0
    # use checkr / AT+r

    return data_length

def GetRadioData(fd, length=-1):
    # get the data from the radio, if no length, get all

    # use geta / AT+A

    return message


def main():
    """
    This is the main entry point for the program when it is being run independently.

    """
    sp = SetupUART()
    SetupLoRa(sp)

    print("Sending messages")
    while(True):
        SendRadioData(sp, "Data Sent")

        print(".", end="", flush=True)
        time.sleep(INTERDELAY)


logging.basicConfig(filename="LoRaCommsReceiver.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":

    main()
