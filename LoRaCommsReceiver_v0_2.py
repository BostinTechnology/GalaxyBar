#!/usr/bin/env python3
"""
This program is used to listen to the LoRa transmissions

It is intended to be used as part of the LoRa Monitor, but it can be run independently.

V0_2 : Comms improved by reducing time delays in the code
"""

import serial
import logging
import time
import math
import sys
import random

#BUG: Even though ReadData failed, the sending program still printed the data string on screen
#       Also appears the same happens when we get a negative LoRa code, eg EREF
#BUG: The data received still has a \r in it, which may be affecting it

#BUG: When I strip off the characters, I can't strip them off from the middle, only the start and end.

#TODO: Need to check for negative LoRa codes, like EREF etc.

# The delay between send and receive
SRDELAY = 0.1

# The delay between receiving one message and sending the next
INTERDELAY = 0.2

def SetupUART():
    """
    Setup the UART for communications and return an object referencing it. Does:-
    -Initiates serial software
    -Opens the serial port
    -Checks all is ok and returns the object
    """

#TODO: Need to cater for Pi 3 as it uses /dev/serial0

    ser = serial.Serial('/dev/ttyAMA0', baudrate=57600, parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0.1)

    time.sleep(INTERDELAY)

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

def ReadData(fd, length=-1, pos_reply='OK00'):
    # Read the data from the serial port of known length
    # If length is not known, assume all data
    # returns a list containing
    #   The success / failure
    #   The string back or an empty string if no response
    # An additonal optional parameter to determine the expected response, default OK00.

    success = False
    if length != -1:
        try:
            ans = fd.read(length)
            time.sleep(SRDELAY)
            # Clear out any remaining characters
            ser.flushInput()
        except:
            logging.warning("Reading of data on the serial port FAILED")
            ans = b''
    else:
        try:
            length = 'unknown'
            ans = fd.readall()
        except:
            logging.warning("Reading of data on the serial port FAILED")
            ans = b''

    logging.debug("Data Read back from the serial port :%s" % ans)
    # Strip out the control codes
    ans = ans.replace(b'\r\n',b'')
    ans = ans.replace(b'>',b'')

    # Check the reply for either the default (OK00 - set above) or given positive response
    # find the last n bytes where n is the length of the expected positive response
    pos_length = len(pos_reply)
    ans_length = len(ans)
    logging.debug("Checking for positive (%s) reply" % pos_reply.encode('utf-8'))
    logging.debug("Checking from position %d to position %d" % (ans_length - pos_length,ans_length))
    if ans[ans_length - pos_length : ans_length] == pos_reply.encode('utf-8'):
        logging.info("Positive response received : %s" % ans[ans_length - pos_length : ans_length])
        success = True
    else:
        logging.warning("Negative response received : %s" % ans[ans_length - pos_length : ans_length])
        ans=""

    logging.debug("Data of length %s read from the Serial port: %a" % (length, ans))
    return (success, ans)

def SendConfigCommand(fd, command):
    # This function sends data and gets the reply for the various configuration commands.

    ans = WriteData(fd, command)
    if ans >0:
        time.sleep(SRDELAY)
        # No need to check the reply as it has already been validated
        ReadData(fd)
    else:
        logging.warning("Failed to Send Config Command %s" % command)

    return

def SetupLoRa(fd):
    # send the right commands to setup the LoRa module
    logging.info("Setting up the LoRA module with the various commands")

    # This one is removed as it keeps failing and I'm not sure we need it
    #SendConfigComamnd(fd, "AT!!")

    SendConfigCommand(fd, "AT*v")
    time.sleep(INTERDELAY)
    SendConfigCommand(fd, "glora")
    time.sleep(INTERDELAY)
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
        # Only need to check for a positive response, which is $, not the standard OK00
        ReadData(fd,pos_reply="$")

        time.sleep(SRDELAY)

        reply = WriteData(fd, message)
        if reply > 0:
            # No need to check response, only looking for positive reply
            ReadData(fd)
        else:
            logging.warning("Sending of the Radio data message >%s< FAILED" % reply)

    else:
        logging.warning("Sending of the Radio data length message >%s< FAILED" % send)
    logging.info("Radio Message >%s< successfully sent" % message)
    return

def RadioDataAvailable(fd):
    # checks to see if there is radio data available to be read using AT+r / checkr.
    # returns zero if no data
    data_length = 0
    reply = WriteData(fd, 'AT+r')
    if reply > 0:
        # Request for data length written successfully
        ans = ReadData(fd)
        if ans[0] == True:
            data_length = int(ans[1][0:2], 16)
        logging.info("Check for Radio Data (AT+r) returned %d bytes" % data_length)
    return data_length

def GetRadioData(fd, length=-1):
    # get the data from the radio, if no length, get all
    # use geta / AT+A
    reply = WriteData(fd, 'AT+A')
    if reply > 0:
        message = ReadData(fd, length)
        logging.info("Radio Data (AT+r) returned >%s<" % message[1])

    return message[1]

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

def ReturnRadioData(fd):
    # This function returns the radio data that has been received as a list
    # It is to be called by the external program.
    received_len = RadioDataAvailable(fd)
    if received_len > 0:
        received = GetRadioData(fd)
        print("Data Received:%s" % received)
        data = [ord(i) for i in received]
        logging.debug("Data being passed back to the main program: %s" % data)
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
            #time.sleep(INTERDELAY)
    else:
        print("Unknown Option")



logging.basicConfig(filename="LoRaCommsReceiver.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":

    main()

