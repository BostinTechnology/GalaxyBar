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
import RPi.GPIO as GPIO

from Settings import *

'''
These bits have been moved into a settings file
# The delay between send and receive
SRDELAY = 0.01

# The delay between receiving one message and sending the next
INTERDELAY = 0.02

FAILDELAY = 0.03

# The connected GPIO pin
INPUT_PIN = 17

# The minimum length of a valid packet
MIN_LENGTH = 11
'''

def SetupUART():
    """
    Setup the UART for communications and return an object referencing it. Does:-
    -Initiates serial software
    -Opens the serial port
    -Checks all is ok and returns the object
    """

    ser = serial.Serial('/dev/ttyAMA0', baudrate=57600, parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0.1)

    time.sleep(INTERDELAY)

    # clear the serial buffer of any left over data
    ser.flushInput()

    if ser.isOpen():
        # if serial comms are setup and the channel is opened
        logging.info ("[LCR]: PI UART setup complete on channel %d as : %s" % (ser.fd, ser.getSettingsDict))
    else:
        logging.critical("[LCR]: Unable to Setup communications")
        sys.exit()

    return ser

def SetupGPIO():
    # Setup the GPIO for the reading of the incoming data
    GPIO.setmode(GPIO.BCM)
    time.sleep(0.2)
    GPIO.setup(INPUT_PIN, GPIO.IN)
    GPIO.setup(LED_PIN, GPIO.OUT)
    logging.debug("[LCR]: GPIO Setup Complete")
    return


def ExitProgram(sport):
    # Close stuff and exit
    GPIO.cleanup()
    sport.close()
    sys.exit()

def LEDControl(state, timeout=0):
    # Control the LED
    # state can be either 1 for ON or 0 for OFF
    if state !=0 and state != 1:
        # If state is not the expected input state, set to default of zero
        state = 0
    starttime = time.time()
    GPIO.output(LED_PIN, state)
    while (starttime + timeout) > time.time():
        time.sleep(0.001)
    return

def LEDFastFlash(flashtime):
    # Flash the LED for the period flashtime (in seconds)
    startflash = time.time()
    while (startflash + flashtime) > time.time():
        LEDControl(1, 0.05)
        LEDControl(0, 0.05)
    LEDControl(0)
    return



def WriteData(fd,message):
    # This routine will take the given data and write it to the serial port
    # returns the data length or 0 indicating fail
    # add the control characters
    send = message + '\r\n'
    try:
        ans = fd.write(send.encode('utf-8'))
        logging.info("[LCR]: Message >%s< written to LoRa module with response :%s" % (send, ans))
    except Exception as e:
        logging.warning("[LCR]: Message >%s< sent as >%a< FAILED" % (message, send))
        ans = 0
    return ans

def WriteDataBinary(fd,message):
    # This routine will take the given data and write it to the serial port
    # returns the data length or 0 indicating fail
    # add the control characters
    send = message + b'\r\n'
    try:
        ans = fd.write(send)
        logging.info("[LCR]: Message >%s< written to LoRa module with response :%s" % (send, ans))
    except Exception as e:
        logging.warning("[LCR]: Message >%s< sent as >%a< FAILED" % (message, send))
        LEDFastFlash(0.25)
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
    ans = [b'', b'']
    try:
        reply = fd.readall()
    except:
        logging.warning("[LCR]: Reading of data on the serial port FAILED")
        reply = b''
        LEDFastFlash(0.25)

    logging.debug("[LCR]: Data read back from the serial port :%s" % reply)

    # The command below removes the characters from around the message, and I only need to remove the one at each end
    reply = reply.rstrip(b'>')
    reply = reply.strip(b'\n')

    if len(reply) < 1:
        # Data received from the LoRa module is empty, return failure
        logging.warning("[LCR]: No reply from the LoRa module, waiting before retrying")
        time.sleep(FAILDELAY)
        return {'success':success, 'reply':ans}
    elif len(reply) < length:
        # The data returned is shorter than expected, return failed
        logging.warning("[LCR]: Reply shorter than expected from the LoRa module")
        return {'success':success, 'reply':ans}
    elif len(reply) < min(MIN_LENGTH, length):
        # The data returned is shorter than the minimum length or the length required (whichever is the shorter, return failed
        logging.warning("[LCR]: Reply shorter than minimum allowed from the LoRa module")
        return {'success':success, 'reply':ans}


    # Populate the first part of the data (ans) with the data
    # Using the given length, strip out the reply. If no length is given, take all except 5 bytes
    if length < 0:
        # No length given, assume overall length less 4
        length = len(reply) - 4
        logging.debug("[LCR]: Response is split based on the last 4 bytes being the status")

    ans[0] = reply[0:length]
    ans[1] = reply[len(reply) - len(pos_reply):]
    logging.debug("[LCR]: Split the response and got data:%s and reply:%s" % (ans[0], ans[1]))

    if ans[1] == pos_reply.encode('utf-8'):
        logging.info("[LCR]: Positive response received from the LoRa module: %s" % ans[1])
        success = True
    else:
        logging.warning("[LCR]: Negative response received from the LoRa module: %s" % ans[1])
        ans=[]
        success = False

    logging.info("[LCR} - Data of length %s read from the Serial port: %a" % (length, ans))
    return {'success':success, 'reply':ans}



def ReadDataOLD(fd, length=-1, pos_reply='OK00'):
    # Read the data from the serial port of known length
    # If length is not known, assume all data
    # returns a list containing 2 entries
    #   The success / failure
    #   The string back or an empty string if no response
    # An additonal optional parameter to determine the expected response, default OK00.

    success = False
    ans = [b'', b'']
    try:
        reply = fd.readall()
    except:
        logging.warning("[LCR]: Reading of data on the serial port FAILED")
        reply = b''

    logging.debug("[LCR]: Data Read back from the serial port :%s" % reply)
    logging.debug("[LCR]: Length being extracted :%s" % length)

    # The command below removes the characters from around the message, and I only need to remove the one at each end
    reply = reply.rstrip(b'>')
    reply = reply.strip(b'\n')

    if len(reply) < 1:
        # Data received from the LoRa module is empty, return failure
        logging.warning("[LCR]: No reply from the LoRa module")
        time.sleep(FAILDELAY)
        return {'success':success, 'reply':""}
    elif len(reply) < length:
        # The data returned is shorter than expected, return failed
        logging.warning("[LCR]: Reply shorter than expected from the LoRa module")
        return {'success':success, 'reply':""}
    elif len(reply) < MIN_LENGTH:
        # The data returned is shorter than expected, return failed
        logging.warning("[LCR]: Reply shorter than minimum allowed from the LoRa module")
        return {'success':success, 'reply':""}


    # Populate the first part of the data (ans) with the data
    # Using the given length, strip out the reply. If no length is given, take all except 5 bytes
    if length < 0:
        # Not given a length, so split on the control codes
        if reply.find(b'\r\n') > 0:
            ans = reply.split(b'\r\n')
            logging.debug("[LCR]: Reply Split using .split(b'\\r\\n') into :%s" % ans)
        else:
            ans[0] = b''
            ans[1] = reply
            logging.debug("[LCR]: Reply Split manually into :%s" % ans)
    else:
        # Spit on the length variable (Use -1 as it is positions 0 to ...)
        ans = [b'',b'']
        ans[0] = reply[0:length]
        ans[1] = reply[len(reply) - len(pos_reply):]
        logging.debug("[LCR]: Reply Split using length into :%s" % ans)

    logging.debug("[LCR]: Read the data and got data:%s and reply:%s" % (ans[0], ans[1]))
    if ans[1] == pos_reply.encode('utf-8'):
        logging.info("[LCR]: Positive response received  from the LoRa module: %s" % ans[1])
        success = True
    else:
        logging.warning("[LCR]: Negative response received from the LoRa module: %s" % ans[1])
        ans=[]
        success = False

    logging.debug("[LCR]: Data of length %s read from the Serial port: %a" % (length, ans))
    return {'success':success, 'reply':ans}


def SendConfigCommand(fd, command):
    # This function sends data and gets the reply for the various configuration commands.

    ans = WriteDataBinary(fd, command)
    if ans >0:
        time.sleep(SRDELAY)
        # No need to check the reply as it has already been validated
        ReadData(fd)
    else:
        logging.warning("[LCR]: Failed to Send Config Command %s" % command)

    return

def LoRaModuleWakeup(fd):
    # This function sends data and gets the reply for the various configuration commands.
    command =b'\n'
    working = False
    starttime = time.time()
    while (starttime + COMMS_TIMEOUT > time.time()) and working == False:
        ans = WriteDataBinary(fd, command)
        if ans >0:
            time.sleep(SRDELAY)
            # No need to check the reply as it has already been validated
            reply = ReadData(fd)
            working = reply['success']
        else:
            logging.warning("[LCR]: Failed to Send Config Command %s" % command)

    return

def SetupLoRa(fd):
    # send the right commands to setup the LoRa module
    logging.info("[LCR]: Setting up the LoRA module with the various commands")
    LoRaModuleWakeup(fd)

    SendConfigCommand(fd, b"AT!!")
    time.sleep(INTERDELAY)
    time.sleep(INTERDELAY)

    SendConfigCommand(fd, b"AT*v")
    time.sleep(INTERDELAY)
    SendConfigCommand(fd, b"glora")
    time.sleep(INTERDELAY)
    SendConfigCommand(fd, b"sloramode 1")
    return

def Setup():
    """
    Sets up the comms and returns the object that is the connection.
    """
    SetupGPIO()
    sp = SetupUART()
    SetupLoRa(sp)
    return sp

def SendRadioData(fd, message):
    # Takes the given data and sends it over the radio network

    # First determine the size of the data, adding 1 for the control character at the end
    length = len(message) + 1
    if length > 255:
        # Length is greater than 255, abort.
        logging.critical("[LCR]: Radio Message length is greater than 255 limit, aborting: %s" % message)
        ExitProgram()

    LEDControl(1)
    send = 'AT+X ' + format(length, '02X')
    send = send.encode('utf-8')
    reply = WriteDataBinary(fd, send)
    if reply >0:
        # reply is not empty, so successful
        time.sleep(SRDELAY)
        # Only need to check for a positive response, which is $, not the standard OK00
        ReadData(fd,pos_reply="$")

        time.sleep(SRDELAY)

        reply = WriteDataBinary(fd, message)
        if reply > 0:
            # No need to check response, only looking for positive reply
            time.sleep(SRDELAY)
            #time.sleep(SRDELAY)

            ReadData(fd)
        else:
            logging.warning("[LCR]: Sending of the Radio data message >%s< FAILED" % reply)

    else:
        logging.warning("[LCR]: Sending of the Radio data length message >%s< FAILED" % send)
        LEDFastFlash(0.5)
    LEDControl(0)
    logging.info("[LCR]: Radio Message >%s< successfully sent at time: %s" % (message, time.strftime("%d-%m-%y %H:%M:%S")))
    return

def WaitForDataAlertviaGPIO():
    # Routine monitors the GPIO pin and waits for the line to go high indicating a packet.
    logging.debug("[LCR]: Waiting for data pin to go high")
    logging.info(" ")       # Add blank line for readability of the log file

    status = 0
    while(status!=1):
        status = GPIO.input(INPUT_PIN)
    logging.debug("[LCR]: Data Pin gone high at time :%s" % time.strftime("%d-%m-%y %H:%M:%S"))
    return

def RadioDataAvailable(fd):
    # checks to see if there is radio data available to be read using AT+r / checkr.
    # returns zero if no data, flashesd the LED whilst receiving data
    WaitForDataAlertviaGPIO()
    LEDControl(1)
    data_length = 0
    reply = WriteDataBinary(fd, b'AT+r')
    if reply > 0:
        # Request for data length written successfully
        ans = ReadData(fd, 2)
        if ans['success'] == True:
            data_length = int(ans['reply'][0], 16)
        logging.info("[LCR]: Check for Radio Data (AT+r) returned %d bytes" % data_length)
    LEDControl(0)
    return data_length

def GetRadioData(fd, length=-1):
    # get the data from the radio, if no length, get all
    # use geta / AT+A
    reply = WriteDataBinary(fd, b'AT+A')
    if reply > 0:
        message = ReadData(fd, length)
        # Don't need to check for a successful reply as it will just pass empty data back
        logging.info("[LCR]: Radio Data (AT+A) returned >%s<" % message['reply'][0])
    return message['reply'][0]

def ReadRadioData(fd):
    # Routine to read and return data from the LoRa unit.
    # Currently sits in a loop waiting to read data

    while(True):
        received_len = RadioDataAvailable(fd)
        if received_len > 0:
            received = GetRadioData(fd, received_len)
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
            data = GetRadioData(fd, received_len)
            logging.debug("[LCR]: Comms Message being passed back to the HDD program: %s" % data)
            LEDControl(0)
    return data

def RadioDataTransmission(fd, message):
    # This function takes the given data and changes the format to match required
    # Then gets it sent and returns the response
    # Only called by an external program

    logging.debug("[LCR]: Data being passed into SendRadioData is:%s" % message)
    SendRadioData(fd, message)
    return

def ReturnRadioDataTimed(fd, waittime):
    # This function returns the radio data that has been received as a list
    # It is to be called by the external program.
    # It will wait for data packet for the supplied time, then return empty if there is nothing
    # Waittime is to be provided in seconds
    timeout = time.time() + waittime
    received_len = 0
    while received_len < 1:
        received_len = RadioDataAvailable(fd)
        if received_len > 0:
            received = GetRadioDataBinary(fd, received_len)

            logging.debug("[LCR]: Data being passed back to the main program: %s" % data)
        if time.time() > timeout:
            data = ''
            logging.debug("[LCR]: No data received within %s seconds, returning empty string" % waittime)
            break
    return data


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    """
    This is the main entry point for the program when it is being run independently.

    """
    logging.basicConfig(filename="LoRaCommsReceiver.txt", filemode="w",
        level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

    print("Bostin Technology\n")
    print("Please choose functionality (e to exit)")
    print(" - (S)ending")
    print(" - (R)eceiving")
    print(" - (L)ED Control")

    sp = SetupUART()
    SetupGPIO()
    while (True):
        choice = input ("Select Menu Option:")
        if choice.upper() == "S":
            SetupLoRa(sp)
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
            sp = SetupUART()
            SetupLoRa(sp)
            print("Receiving Messages")
            while(True):
                ReadRadioData(sp)

                print(".", end="", flush=True)
                #time.sleep(INTERDELAY)
        elif choice.upper() == "L":
            # Test the LED software
            LEDControl(1)
      #      LEDControl(0)
            time.sleep(0.5)
            LEDFastFlash(1)
        elif choice.upper() == "E":
            break
        else:
            print("Unknown Option")
    ExitProgram(sp)


