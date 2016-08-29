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
    except Exception as e:
        logging.warning("Message >%s< sent as >%a< FAILED" % (message, send))
        logging.error("Failed Response: %s" % e)
        ans = 0
    return ans

def ReadData(fd, length=-1, pos_reply='OK00'):
    # Read the data from the serial port of known length
    # If length is not known, assume all data
    # returns a list containing 2 entries
    #   The success / failure
    #   The string back or an empty string if no response
    # An additonal optional parameter to determine the expected response, default OK00.

    success = False
    try:
        reply = fd.readall()
    except:
        logging.warning("Reading of data on the serial port FAILED")
        reply = b''
#BUG: If nothing received, the program may fail after this point

    logging.debug("Data Read back from the serial port :%s" % reply)

    # The command below removes the characters from within the message, and I only need to remove the one at the end
    reply = reply.rstrip(b'>')

#BUG: this could easily happen in the main payload. I should consider splitting based on length.
#       What is not clear is if the length from the module is the message length>

    # Populate the first part of the data (ans) with the data
    # Using the given length, strip out the reply. If no length is given, take all except 5 bytes
    if length < 0:
        # Not given a length, so split on the control codes
        ans = reply.split(b'\r\n')
    else:
        # Spit on the length variable (Use -1 as it is positions 0 to ...)
        ans[0] = reply[0:length-1]

    logging.debug("The reply is now split into >%s< and >%s<" % (ans[0], ans[1]))

    # Populate the second part of the data (ans) with the reply, the length is determined by the length of pos_reply
    ans[1] = reply[len(reply) - len(pos_reply):]

    #ans_pos = len(ans) - 1
    #logging.debug("Checking for positive (%s) reply" % pos_reply.encode('utf-8'))
    #logging.debug("Checking in reply packet %d" % ans_pos)
    logging.debug("Read the data and got data:%s and reply:%s" % (ans[0], ans[1]))
    if ans[1] == pos_reply.encode('utf-8'):
        logging.info("Positive response received : %s" % ans[1])
        success = True
    else:
        logging.warning("Negative response received : %s" % ans[1])
        ans=[]
        success = False

    logging.debug("Data of length %s read from the Serial port: %a" % (length, ans))
    return {'success':success, 'reply':ans}

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

#TODO: May need to add in a success response so I can determine if the data has been sent.

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
            time.sleep(SRDELAY)
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
        if ans['success'] == True:
            data_length = int(ans['reply'][0], 16)
        logging.info("Check for Radio Data (AT+r) returned %d bytes" % data_length)
    return data_length

def GetRadioData(fd, length=-1):
    # get the data from the radio, if no length, get all
    # use geta / AT+A
    reply = WriteData(fd, 'AT+A')
    if reply > 0:
        message = ReadData(fd, length)
        # Don't need to check for a successful reply as it will just pass empty data back
        logging.info("Radio Data (AT+r) returned >%s<" % message['reply'][0])
    return message['reply'][0]

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
    received_len = 0
    while received_len < 1:
        received_len = RadioDataAvailable(fd)
        if received_len > 0:
            received = GetRadioData(fd)
            print("Data Received:%s" % received)

            data = [i for i in received]
            logging.debug("Data being passed back to the main program: %s" % data)
#        else:
#            data = []
    return data

def RadioDataTransmission(fd, dataaslist):
    # This function takes the given data and changes the format to match required
    # Then gets it sent and returns the response
    # Only called by an external program
    message = ""
    message = message.join(dataaslist)
    logging.debug("Data being passed into SendRadioData is:%s" % message)
    SendRadioData(fd, message)
    return

def ReturnRadioDataTimed(fd, waittime):
    # This function returns the radio data that has been received as a list
    # It is to be called by the external program.
    # It will wait for data packet for the supplied time, then return empty if there is nothing
    # Waittime is to be provided in seconds

# TODO: Add a check around the waittime

    timeout = time.time() + waittime
    received_len = 0
    while received_len < 1:
        received_len = RadioDataAvailable(fd)
        if received_len > 0:
            received = GetRadioData(fd)
            print("Data Received:%s" % received)

            data = [i for i in received]
            logging.debug("Data being passed back to the main program: %s" % data)
        if time.time() > timeout:
            data = ''
            logging.debug("No data received within %s seconds, returning empty string" % waittime)
            break
    return data

def main():
    """
    This is the main entry point for the program when it is being run independently.

    """
    logging.basicConfig(filename="LoRaCommsReceiver.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

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





# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":

    main()

