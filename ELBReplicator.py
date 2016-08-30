#!/usr/bin/env python3
"""
A test program to generate UART packages that reflect the LoRa transmissions.
These are sent out over the transmit line, with a wire loop so they can be received.

It is intended to be run for testing and development

"""

#TODO: to be checked to see if required
#TODO: Need to add logging throughout for debugging

import logging
import time
import math
import sys
import random
import argparse
import LoRaCommsReceiver

#TODO: Have more levels of logging so I don't generate too much data

# constants that will not change in program
# command bytes that are used by LoRa module
AssociationRequest = 0x30
AssociationConfiramtion = 0x31
Ping = 0x32
CommandForModule = 0x33
DataToSendRequest = 0x34
ClearToSendData = 0x35
DataPacketandReq = 0x36
DataPacketFinal = 0x37


# initialise global variables for data packet. Defined here so that they are global
Packet = []         # start with empty packet
# pointers in packet
StartHubAddr = 0    # poisiton in packet where hub addr starts
StartELBAddr = 5    # posiiton in packet where ELB starts
StartCommand = 10   # posiiton of command byte
StartPayloadLength = 11     # position of payload length byte
StartPayload = 12   # poition of start of payload
#TODO - check thees pointers are true of ping, request to send and data packets
Command = 0         # default value for command

# initialise variables
CommsMode = "IDLE"  # Set to comms being instigated
                    # Possible values are PING, ASSC, SEND
CurrentHub = "0000" # when comms has started this variable holds the Hub addr that we are talking to
                    # all others will be ignored.
CurrentELB = "5252" # This is the ELB address
ExecByte = "!"      # The executive byte to use
PacketReceived = False  # set true when a packet has been received - trigger write operation.

WaitTime = 10       # The time allowed for the ELB to listen for data before starting to send something
Reply_Wait = 5      # The time the ELB waits for a response
Retries = 3         # How many times the module will retry a command


def GetModuleData(sp):
    # function to get data from LoRa module
    # need to wait here until we have data
    # optional

    if WorkingMode.simulate:
        # this is a data packet - Packet = ['0','0','0','0','1','2','3','4','!',Command,PayloadLength,0x80,0x00,0x30,0x45,0x12,0x25,0x12,0x15,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x11,0x22,0x33,0x44,0x11,0x22,0x33,0x22,0x45,0x67,0x56,0x78,0x03,0xA4]   # build packet
        # ping packet
        reply = ['0','0','0','0','!','1','2','3','4','!',Ping]

        # need to put data validation here

    else:
        # Running in normal mode
        # This function returns a packet of data as a string, only returns when data captured
        Packet = []

#TODO: The Waittime is the time after a ping response the ELB waits for.

        reply = LoRaCommsReceiver.ReturnRadioDataTimed(sp, Reply_Wait)
        # This can be an empty packet if no data found in the time allowed
        print ("Got this: %s" % reply)

    return reply
    # return the data from the get data function

def GetPayload():
    """
    Returns a defined payload
    """
    payload_length = 27
    load = []
    load = [chr(0x80)]
    for f in range(1, payload_length):
        load.insert(f, chr(random.randint(0x00, 0xff)))
    logging.debug("Random Payload Generated of %x bytes:%s" % (payload_length,load))
    return load

def ProcessCommand(sp):
    # Process the received command from the HUB
    logging.info("Responding to the received COMMAND message from the HUB")
    return

def SendNewAssociationRequest(sp):
    # This function performs all that is necessary for a new association
    logging.info("Performing a NEW ASSSOCIATION with the HUB")
    packet_to_send = []
    # Receiver address
    packet_to_send = packet_to_send + list(CurrentHub)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Sender address
    packet_to_send = packet_to_send + list(CurrentELB)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Command
    packet_to_send.append(chr(AssociationRequest))
    logging.info("Ping Message message:%s" % packet_to_send)

#TODO: Add in retry loop

    LoRaCommsReceiver.RadioDataTransmission(sp, packet_to_send)
    # Now need to wait for the answer or timeout.
    reply = LoRaCommsReceiver.ReturnRadioDataTimed(sp, WaitTime)
    logging.debug("Ping Response from the HUB :%s" % reply)

#TODO: Check Ping response is positive
    print("Ping response received >%s< (blank = no response)" % reply)
    return

def SendDataToSendRequest(sp):
    # This function performs all that is necessary for a new association
    logging.info("Performing a DATA TO SEND REQUEST with the HUB")
    packet_to_send = []
    # Receiver address
    packet_to_send = packet_to_send + list(CurrentHub)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Sender address
    packet_to_send = packet_to_send + list(CurrentELB)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Command
    packet_to_send.append(chr(DataToSendRequest))
    logging.info("Data To Send Request message:%s" % packet_to_send)

#TODO: Add in retry loop

    LoRaCommsReceiver.RadioDataTransmission(sp, packet_to_send)
    # Now need to wait for the answer or timeout.
    reply = LoRaCommsReceiver.ReturnRadioDataTimed(sp, WaitTime)
    logging.debug("Data To Send Request Response from the HUB :%s" % reply)

#TODO: Check Ping response is positive
    print("Data To Send Request response received >%s< (blank = no response)" % reply)
    return

def SendDataPacketandReq(sp):
    # This function performs all that is necessary for sending data
    logging.info("Performing a DATA PACKET + REQ with the HUB")
    packet_to_send = []
    # Receiver address
    packet_to_send = packet_to_send + list(CurrentHub)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Sender address
    packet_to_send = packet_to_send + list(CurrentELB)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Command
    packet_to_send.append(chr(DataPacketandReq))
    # Generate Payload
    payload = GetPayload()
    # Length of payload
    packet_to_send.append(chr(len(payload)))
    for items in payload:
        packet_to_send.append(items)
    logging.info("Data Packet + Req message:%s" % packet_to_send)

#TODO: Add in retry loop

    LoRaCommsReceiver.RadioDataTransmission(sp, packet_to_send)
    # Now need to wait for the answer or timeout.
    reply = LoRaCommsReceiver.ReturnRadioDataTimed(sp, WaitTime)
    logging.debug("Data Packet + Req Response from the HUB :%s" % reply)

#TODO: Check Ping response is positive
    print("Data Packet + Req response received >%s< (blank = no response)" % reply)
    return

def SendDataPacketFinal(sp):
    # This function performs all that is necessary for sending data
    logging.info("Performing a DATA PACKET FINAL with the HUB")
    packet_to_send = []
    # Receiver address
    packet_to_send = packet_to_send + list(CurrentHub)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Sender address
    packet_to_send = packet_to_send + list(CurrentELB)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Command
    packet_to_send.append(chr(DataPacketFinal))
    # Generate Payload
    payload = GetPayload()
    # Length of payload
    packet_to_send.append(chr(len(payload)))
    for items in payload:
        packet_to_send.append(items)
    logging.info("Data Packet + Req message:%s" % packet_to_send)

#TODO: Add in retry loop

    LoRaCommsReceiver.RadioDataTransmission(sp, packet_to_send)
    # Now need to wait for the answer or timeout.
    reply = LoRaCommsReceiver.ReturnRadioDataTimed(sp, WaitTime)
    logging.debug("Data Packet Final Response from the HUB :%s" % reply)

#TODO: Check Ping response is positive
    print("Data Packet Final response received >%s< (blank = no response)" % reply)
    return

def SendPing(sp):
    # Send a PING message to the HUB
    """
    Function generates an Ping Message and puts it into a list for use.
    """
    logging.info("Sending a PING message to the HUB")
    packet_to_send = []
    # Receiver address
    packet_to_send = packet_to_send + list(CurrentHub)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Sender address
    packet_to_send = packet_to_send + list(CurrentELB)
    # Executive Byte
    packet_to_send.append(ExecByte)
    # Command
    packet_to_send.append(chr(Ping))
    logging.info("Ping Message message:%s" % packet_to_send)

#TODO: Add in retry loop

    LoRaCommsReceiver.RadioDataTransmission(sp, packet_to_send)
    # Now need to wait for the answer or timeout.
    reply = LoRaCommsReceiver.ReturnRadioDataTimed(sp, WaitTime)
    logging.debug("Ping Response from the HUB :%s" % reply)

#TODO: Check Ping response is positive
    print("Ping response received >%s< (blank = no response)" % reply)
    return

def UnrecognisedCommand():
    # send relevant Nack.
    logging.info("REceived an Unrecognised command from the HUB")
    return


def Main():

    if WorkingMode.simulate != True:
        # Open the serial port and configure the Radio Module
        SerialPort = LoRaCommsReceiver.SetupUART()
        LoRaCommsReceiver.SetupLoRa(SerialPort)

    while True:
        '''
        The struture of the main loop is to loop forever getting data and then processing it.
        3 variables indicate if
            coms is idle - no conversation has been started
            a packet has been received - data received, validated and acked. Ready to write
            who we are talking to - the ELB address that has started a conversation
        '''
        print ("in main loop")

#TODO: Need to put something in here to cycle round the various messages to get comms working
#       The code below assumes CommsMode has been set
#       I'm not sure what the actual ELB does for this

# This list determines the order the packets are sent
        for mode in ('PING','ASSC', 'SEND', 'LAST'):
            CommsMode = mode
            print("%s" % mode)
        #CommsMode = "PING"


#BUG command is a list element and not a number

            if CommsMode == "IDLE":     # not yet in communication with an Hub
                # First check if there is any data to be processed
                Packet = GetModuleData(SerialPort)
                     # waits in Get data until we have now received a packet from the radio module and it has been checked for validity
                print ("Packet of Data %s" % Packet)
                print ("Command Byte Location %s" % StartCommand)
                Command = Packet[StartCommand:StartCommand+1]   # extract command byte
                print ("ComsIdle = False")
                if Command == [CommandForModule]:
                    print("Command For Module")
                    ProcessCommand(SerialPort)
                else:
                    UnrecognisedCommand()
            elif CommsMode == "ASSC":
                # Associate with the HUB
                SendNewAssociationRequest(SerialPort)
            elif CommsMode == "SEND":
                # Send data to the HUB
                SendDataPacketandReq(SerialPort)
            elif CommsMode == "LAST":
                # Send data to the HUB
                SendDataPacketFinal(SerialPort)
            elif CommsMode == "PING":
                # Send a ping message
                SendPing(SerialPort)
            else:
                UnrecognisedCommand()



# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":

    logging.basicConfig(filename="ELBReplicator.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

    # Define the optional arguments to enable it to work in different modes
    # To use this:-
    # if WorkingMode.simulate == True:    if the code is to be run in simulation mode only
    # or
    # if WorkingMode.simulate != True:    if the code is to be run in normal mode only

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--simulate", help="Run the program in simulate mode", action='store_true')
    WorkingMode = parser.parse_args()

    logging.info("Starting main program with parsed arguments simulate:%s" % WorkingMode.simulate)
    # Call the main function to run

    Main()
