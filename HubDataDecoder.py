''' Hub Data Decoder
Started 21.8.16
Reads a LoRa data packet and decodes it.

Now uses logging. To add logging type
logging.level(message)
where level is either debug, info, warning, error, critical message is the text to log - can add variables into these messages
e.g.
logging.debug("Recevied this packet to decode:%s" % reply) replaces the %s with the value in reply as a string

31st Aug - Changed the data packet to be a string rather than a list.
'''
Simulate = True  # set this to false if using the radio module
import argparse
import logging

if Simulate != True:
    import LoRaCommsReceiver

# constants that will not change in program
# command bytes that are used by LoRa module
DataToSendReq = chr(0x34)
ClearToSendData = chr(0x35)
DataPacketandReq = chr(0x36)
DataPacketFinal = chr(0x37)
Ping = chr(0x32)
# ack codes
ACK = chr(0x22)                 # all good and confirmed
NackPreamble = chr(0x50)        # preamble erro - ascii P
NackCRC = chr(0x51)             # CRC error - ascii Q
NackAddrError = chr(0x60)       # address error - ascii '
NackMsgLen = chr(0x61)          # message length inconsisten - ascii a
NackPayload = chr(0x70)         # payload crc error- ascii p
NackCmdRecog = chr(0x7A)        # command not recognised - ascii €
    # should be 0x80 but logging doesn't seem to handle above 0x7F
NackCmdSync = chr(0x7B)         # command out of protocol sync
NackNotReadyforData = chr(0x7C) # not ready for data ascii ,


# initialise global variables for data packet. Defined here so that they are global
Packet = ''  # start with empty packet.
# pointers in packet
StartHubAddr = 0  # poisiton in packet where hub addr starts
StartELBAddr = 5  # posiiton in packet where ELB starts
StartCommand = 10  # posiiton of command byte
StartPayloadLength = 11  # position of payload length byte
StartPayload = 12  # poition of start of payload
# TODO - check these pointers are true of ping, request to send and data packets
ExecByte = "!"      # The executive by

def GetModuleData(sp, Simulate):
    # this module supplies a packet every time it is called
    # the packet depends on the value of sp passed.

    Payload = chr(0x7F) + chr(0x00) + chr(0x30) + \
                chr(0x45) + chr(0x12) + chr(0x25) + chr(0x12) + chr(0x15) + chr(0x01) + chr(0x02) + chr(0x03) + \
                chr(0x04) + chr(0x05) + chr(0x06) + chr(0x07) + chr(0x08) + chr(0x11) + chr(0x22) + chr(0x33) + \
                chr(0x44) + chr(0x11) + chr(0x22) + chr(0x33) + chr(0x22) + chr(0x45) + chr(0x67) + chr(0x56) + \
                chr(0x78) + chr(0x03) + chr(0xA4)
    '''
    ComsIdle = True
        Valid Commands =
                    Ping and SendDataReq
        Invalid Commnds =
                    ClearToSendData, DataPacketandReq, DataPacketFinal, Unrecognised
    ComsIdle = False
        Valid Commands =
                    DataPacketandReq and DataPacketFinal
        Invalid commands =
                    Ping, DataToSendReq, ClearToSendData, Unrecognised
                    DataPacketandReq from another ELB
                    DataPacketFinal from another ELB
    '''
    if Simulate:
        if sp == 1:
            # ping packet
            reply = '0000!1234!' + Ping
        elif sp == 2:
            # Data to send request
            reply = '0000!1234!' + DataToSendReq
        elif sp == 3:
            # data packet and request
            PayloadLength = 30
            reply = '0000!1234!' + DataPacketandReq + chr(PayloadLength) + Payload
        elif sp == 4:
            # data packet and final
            PayloadLength = 30
            reply = '0000!1234!' + DataPacketFinal + chr(PayloadLength) + Payload
        elif sp == 5:
            # ping packet
            reply = '0000!1234!' + Ping
        elif sp == 6:
            # DataPacketandReq before DataToSendReq
            PayloadLength = 30
            reply = '0000!1234!' + DataPacketandReq + chr(PayloadLength) + Payload
        elif sp == 7:
            # DataPacketFinal before DataToSendReq
            PayloadLength = 30
            reply = '0000!1234!' + DataPacketFinal + chr(PayloadLength) + Payload
        elif sp == 8:
            # ClearToSendData from another hub
            reply = '0000!4321!' + ClearToSendData
        elif sp == 9:
            # unrecognised
            reply = '0000!1234!' + 't'
        elif sp == 10:
            # ping
            reply = '0000!1234!' + Ping
        elif sp == 11:
            # DataToSendReq
            reply = '0000!1234!' + DataToSendReq
        elif sp == 12:
            # ComsIdle now false so send invalid commands from another ELB
            # Ping from another ELB
            reply = '0000!4321!' + Ping
        elif sp == 13:
            # ComsIdle now false so send invalid commands from another ELB
            # DataToSendReq from another ELB
            PayloadLength = 30
            reply = '0000!4321!' + DataPacketandReq + chr(PayloadLength) + Payload
        elif sp == 14:
            # ComsIdle now false so send invalid commands from another ELB
            # ClearToSendData from another Hub
            reply = '0000!4321!' + ClearToSendData
        elif sp == 15:
            # unrecognised
            reply = '0000!1234!' + ','
        elif sp == 16:
            # ping packet after
            reply = '0000!1234!' + Ping
        elif sp == 17:
            # Data to send request
            reply = '0000!1234!' + DataToSendReq
        elif sp == 18:
            # pping from another elb during coms
            reply = '0000!4321!' + Ping
        elif sp == 19:
            # data packet and request
            PayloadLength = 30
            reply = '0000!1234!' + DataPacketandReq + chr(PayloadLength) + Payload
        elif sp == 20:
            # DataToSendReq from another elb during coms
            reply = '0000!4321!' + DataToSendReq
        elif sp == 21:
            # data packet and final
            PayloadLength = 30
            reply = '0000!1234!' + DataPacketFinal + chr(PayloadLength) + Payload
        elif sp == 22:
            # ping packet
            reply = '0000!1234!' + Ping
        else:
            # make the rest pings
            reply = '0000!1234!' + Ping

            # TODO need to put data validation here

    else:
        # Running in normal mode
        # This function returns a packet of data as a string, only returns when data captured
        # Packet = []
        reply = LoRaCommsReceiver.ReturnRadioData(sp)

    logging.info(' ') # force new lne
    logging.info("i :%s" % sp)
    logging.info("Received this data to process :%s" % reply)

    return reply
    # return the data from the get data function


def WriteLogFile(Packet):
    # write log file.
    # takes a packet and appends it to a log file. This is the output from the Hub Decoder
    LogFileName = "Log" + Packet[StartELBAddr:StartELBAddr+4]
    LogFile = open("Log" + Packet[StartELBAddr] + "yymmddhhmmss", "w")
    PayloadLength = ord(Packet[StartPayloadLength])     # get payload length and convert to int
    # LogFile.write(Packet[StartPayload:StartPayload+PayloadLength])
    # LogFile.close()

def GenerateAck(Packet):
    # Function generates an Ack for response to a number of messages
    packet_to_send = ''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send = packet_to_send + ExecByte                                         # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]    # Sender address
    packet_to_send = packet_to_send +  ExecByte                     # Executive Byte
    packet_to_send = packet_to_send + ACK                     # Acknowledge

    return packet_to_send

def RespondToPing(fd, Packet, Simulate):
    # responds to the ping command.

    message = GenerateAck(Packet)
    logging.info("Responding to a PING - Ack Message :%s" % message)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)
    # Now need to wait for the answer or timeout.

    return


def RespondDataToSendReq(fd, Packet,Simulate):
    # responds to the Data to Send Request

    packet_to_send = ''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byt
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]   # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + ClearToSendData                       # Clear to Send data command

    logging.info("ClearToSendData :%s" % packet_to_send)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def RespondDataPacketandReq(fd, Packet, Simulate):
    # data packet received and further data is on its way

    message = GenerateAck(Packet)
    logging.info("DataPacketandReq :%s" % message)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def RespondDataPacketFinal(fd, Packet, Simulate):
    # data packet received and no more to come

    message = GenerateAck(Packet)
    logging.info("Received Final Packet :%s" % message)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def UnrecognisedCommand(fd,Packet,Simulate):
    # send relevant Nack.

    # Function generates an Ack for response to anumber of messages
    packet_to_send = ''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackCmdRecog                          # Nack with command unrecognised
    logging.info("Nack Cmd not Recognised Message :%s" % packet_to_send)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def SendPiBusyNack(fd,Packet,Simulate):
    # have been pinged from 2nd ELB while receiving data from 1st ELB
    # Function generates an Ack for response to anumber of messages
    packet_to_send = ''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackNotReadyforData                   # Nack with command unrecognised
    logging.info("Nack Not Ready for Data :%s" % packet_to_send)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def Main():
    # initialise variables
    ComsIdle = True  # set to false when an initial RequestToSendData has been received.
    CurrentELB = ''  # when coms has started this variable holds the ELB addr that we are talking to

    if Simulate != True:
        # Open the serial port and configure the Radio Module
        SerialPort = LoRaCommsReceiver.SetupUART()
        LoRaCommsReceiver.SetupLoRa(SerialPort)
    else:
        SerialPort = 0

    # while True:
    for i in range(25):
        '''
        The struture of the main loop is to loop forever getting data and then processing it.
        3 variables indicate if
            coms is idle - no conversation has been started
            a packet has been received - data received, validated and acked. Ready to write
            who we are talking to - the ELB address that has started a conversation
        '''
        if Simulate:
            Packet = GetModuleData(i, Simulate)
        else:
            Packet = GetModuleData(SerialPort,Simulate)
            # waits in Get data until we have now received a packet from the radio module and it has been checked for validity

        Command = Packet[StartCommand]          # extract command byte
        # TODO: Need to decode the full message received so I know the ELB address and if the message is for me!


        '''
        ComsIdle = True
            Valid Commands =
                        Ping and SendDataReq
            Invalid Commnds =
                        ClearToSendData, DataPacketandReq, DataPacketFinal, Unrecognised
        ComsIdle = False
            Valid Commands =
                        DataPacketandReq and DataPacketFinal
            Invalid commands =
                        Ping, DataToSendReq, ClearToSendData, Unrecognised
                        DataPacketandReq from another ELB
                        DataPacketFinal from another ELB
        '''
        #TODO need to add timeouts for coms
        if ComsIdle:  # not yet in communication with an ELB
            if Command == Ping:
                RespondToPing(SerialPort, Packet, Simulate) # respond to a ping command
            elif Command == DataToSendReq:
                ComsIdle = False                            # coms has started so no longer idle
                CurrentELB = Packet[StartELBAddr:StartELBAddr+4]
                RespondDataToSendReq(SerialPort,Packet,Simulate)
                # this will send CleartoSendData.
            elif Command == ClearToSendData or Command == DataPacketandReq or Command == DataPacketFinal:
                # commands invalid at this point
                logging.info("ClearToSendData, DataPacketandReq or DataPacketFinal at wrong time :%s" % Packet)
            else:
                UnrecognisedCommand(SerialPort, Packet, Simulate)
                    # send Nack with unrecognised cmd
        else:                                   # ComsIdle is true so talking to ELB
            if Command == DataPacketandReq and CurrentELB == Packet[StartELBAddr:StartELBAddr+4]:
                    # coms has started and received data packet with more to follow
                RespondDataPacketandReq(SerialPort,Packet,Simulate)     # send ack packet
                WriteLogFile(Packet)            # write this packet to a log file
            elif Command == DataPacketFinal and CurrentELB == Packet[StartELBAddr:StartELBAddr+4]:
                    # coms has started and received final data packet
                RespondDataPacketFinal(SerialPort,Packet,Simulate)
                WriteLogFile(Packet)                            # write this packet to a log file
                ComsIdle = True                                 # coms sequence comlete so reset coms idle
                CurrentELB = ''                                 # clear current ELB
            elif Command == DataPacketandReq and CurrentELB != Packet[StartELBAddr:StartELBAddr+4]:
                # coms has started and received data packet from wrong ELB
                SendPiBusyNack(SerialPort, Packet, Simulate)  # send Pi busy Nack
            elif Command == DataPacketFinal and CurrentELB != Packet[StartELBAddr:StartELBAddr+4]:
                # coms has started and received data packet from wrong ELB
                SendPiBusyNack(SerialPort, Packet, Simulate)  # send Pi busy Nack
            else:                               # handle invalid command
                if Command == Ping:                               # received ping from another ELB while receiving data
                    SendPiBusyNack(SerialPort,Packet,Simulate)      # send Pi busy Nack
                    # should be ack
                elif Command == DataToSendReq or Command == ClearToSendData:
                    logging.info("DataToSendReq or ClearToSendData when already in coms :%s" % Packet)
                else:
                    UnrecognisedCommand(SerialPort, Packet, Simulate)
                    # send Nack with unrecognised cmd


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    logging.basicConfig(filename="HubDecoder.txt", filemode="w", level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    # BUG logging is not defined if not on Pi
    # Define the optional arguments to enable it to work in different modes
    # To use this:-
    # if WorkingMode.simulate == True:    if the code is to be run in simulation mode only
    # or
    # if WorkingMode.simulate != True:    if the code is to be run in normal mode only

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--simulate", help="Run the program in simulate mode", action='store_true')
    parser.add_argument("-e", "--elb", help="Run program as a ELB, hub is default", action='store_true')
    WorkingMode = parser.parse_args()

    logging.info(
        "Starting main program with parsed arguments simulate:%s & eld:%s" % (WorkingMode.simulate, WorkingMode.elb))
    # Call the main function to run

    Main()
