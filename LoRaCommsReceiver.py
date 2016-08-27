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
import random

# The delay between send and receive
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

#TODO: Need to cater for Pi 3 as it uses /dev/serial0

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

def ExitProgram(sport):
    # Close stuff and exit
    sport.close()
    sys.exit()

def WriteData(fd,message):
    # This routine will take the given data and write it to the serial port
    # returns the data length or 0 indicating fail
    # add the control characters
    send = message + '\r\n'
    try:
        ans = fd.write(send.encode('utf-8'))
        logging.info("Message >%s< sent as >%a< and got this reply:%s" % (message, send, ans))
    except:
        logging.warning("Message >%s< sent as >%a< FAILED" % (message, send))
        ans = 0
    return ans

def ReadData(fd, length=-1):
    # Read the data from the serial port of known length
    # If length is not known, assume all data
    # returns the string back or an empty string if no response

#TODO: add an additonal optional parameter to determine the expected response, default OK00.

#TODO: Add Try loop in case of failure
    if length != -1:
        ans = fd.read(length)
    else:
        ans = fd.readall()
        length = 'unknown'
    # Strip out the control codes
    ans.replace(b'\r\n',b'')
#TODO: Validate the response as having OK00 at the end
#TODO: Need to check the reply to see if it is ok, should be \r\nOK00> - remembering the \r\n is being stripped off

    logging.debug("Data of length %s read from the Serial port: %a" % (length, ans))
    return ans

def SendConfigCommand(fd, command):
    # This function sends data and gets the reply for the various configuration commands.

    ans = WriteData(fd, command)
    if ans >0:
        time.sleep(SRDELAY)
#TODO: Handle a zero length response
        ans = ReadData(fd)

        time.sleep(INTERDELAY)
    else:
        logging.warning("Failed to Send Config Command %s" % command)

    return

def SetupLoRa(fd):
    # send the right commands to setup the LoRa module
    logging.info("Setting up the LoRA module with the various commands")

    # This one is removed as it keeps failing and I'm not sure we need it
    #SendConfigComamnd(fd, "AT!!")

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
    if length > 255:
        # Length is greater than 255, abort.
        logging.critical("Radio Message length is greater than 255 limit, aborting: %s" % message)
        ExitProgram()

    send = 'AT+X ' + format(length, '02X')
    reply = WriteData(fd, send)
    if reply >0:
        # reply is not empty, so successful
        time.sleep(SRDELAY)
#TODO: Handle a zero length response
        ReadData(fd)
#TODO: Check the response, it should be $ indicating it is ready for the data e.g. b'\r\n$'
#       Note, ReadData will need to know it is expecting a $, as it will look for OK00!!

        time.sleep(SRDELAY)
#TODO: CHeck if reply is zero and act accordingly
        reply = WriteData(fd, message)
    else:
        logging.warning("Sending of the Radio data length message >%s< FAILED" % send)
#TODO: Handle a zero length response
    ReadData(fd)
    return

def RadioDataAvailable(fd):
    # checks to see if there is radio data available to be read using AT+r / checkr.
    # returns zero if no data
    data_length = 0
#TODO: CHeck if WriteData returns a zero and act accordingly
    WriteData(fd, 'AT+r')
#TODO: Handle a zero length response
    ans = ReadData(fd)
#TODO: Add in check for invalid / incorrect data, format of data returned is 00\r\nOK00>
    data_length = int(ans[0:2], 16)
    logging.info("Check for Radio Data (AT+r) returned %i bytes" % data_length)
    return data_length

def GetRadioData(fd, length=-1):
    # get the data from the radio, if no length, get all
    # use geta / AT+A
#TODO: CHeck if WriteData returns zero and act accordingly
    WriteData(fd, 'AT+A')
#TODO: Handle a zero length response
    message = ReadData(fd, length)
    logging.info("Radio Data (AT+r) returned >%s<" % message)

    return message

def ReadRadioData(fd):
    # Routine to read and return data from the LoRa unit.
    # Currently sits in a loop waiting to read data

#TODO: Modify routine to have a form of exit

    while(True):
        received_len = RadioDataAvailable(fd)
        if received_len > 0:
            received = GetRadioData(fd)
            print("Data Received:%s" % received)
        else:
            print(".", end="", flush=True)
    return


def main():
    """
    This is the main entry point for the program when it is being run independently.

    """

    print("Bostin Technology\n")
    print("Please choose functionality")
    print(" - (S)ending")
    print(" - (R)eceiving")

    choice = input ("Select Menu Option:")

    sp = SetupUART()
    SetupLoRa(sp)

    if choice.upper() == "S":
        print("Sending Messages")
        while(True):
            length_to_send = random.randint(5,36)
            data_to_send = ""
            data_to_send = ''.join(random.choice('0123456789ABCDEF') for i in range(length_to_send))
            print("Data To Send:%s" % data_to_send)
            SendRadioData(sp, data_to_send)

            print(".", end="", flush=True)
            time.sleep(INTERDELAY)
    elif choice.upper() == "R":
        print("Receiving Messages")
        while(True):
            ReadRadioData(sp)

            print(".", end="", flush=True)
            time.sleep(INTERDELAY)
    else:
        print("Unknwon Option")



logging.basicConfig(filename="LoRaCommsReceiver.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":

    main()

