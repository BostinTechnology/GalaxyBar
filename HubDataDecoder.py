''' Hub Data Decoder
Started 21.8.16
Reads a LoRa data packet and decodes it.

Now uses logging. To add logging type
logging.level(message)
where level is either debug, info, warning, error, critical
message is the text to log - can add variables into these messages

e.g.
logging.debug("Recevied this packet to decode:%s" % reply)
replaces the %s with the value in reply as a string

'''
Simulate = False  # set this to false if using the radio module
import argparse
import logging

if Simulate != True:
    import LoRaCommsReceiver

# constants that will not change in program
# command bytes that are used by LoRa module
DataToSendReq = 0x34
ClearToSendData = 0x35
DataPacketandReq = 0x36
DataPacketFinal = 0x37
Ping = 0x32
# ack codes
ACK = 0x22              # all good and confirmed
NackPreamble = 0x50     # preamble erro - ascii P
NackCRC = 0x51          # CRC error - ascii Q
NackAddrError = 0x60    # address error - ascii '
NackMsgLen = 0x61       # message length inconsisten - ascii a
NackPayload = 0x70      # payload crc error- ascii p
NackCmdRecog = 0x80     # command not recognised - ascii €
NackCmdSync = 0x81      # command out of protocol sync
NackNotReadyforData = 0x82  # not ready for data ascii ,


# initialise global variables for data packet. Defined here so that they are global
Packet = []  # start with empty packet
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

    if Simulate:
        if sp == 1:
            # ping packet
            reply = ['0', '0', '0', '0', '!', '1', '2', '3', '4', '!', Ping]
        elif sp == 2:
            # Data to send request
            reply = ['0', '0', '0', '0', '!', '1', '2', '3', '4', '!', DataToSendReq]
        elif sp == 3:
            # data packet and request
            PayloadLength = 30
            reply = ['0', '0', '0', '0', '!', '1', '2', '3', '4', '!', DataPacketandReq, PayloadLength, 0x80, 0x00,
                     0x30, 0x45, 0x12, 0x25, 0x12, 0x15, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x22,
                     0x33, 0x44, 0x11, 0x22, 0x33, 0x22, 0x45, 0x67, 0x56, 0x78, 0x03, 0xA4]
        elif sp == 4:
            # data packet and final
            PayloadLength = 30
            reply = ['0', '0', '0', '0', '!', '1', '2', '3', '4', '!', DataPacketFinal, PayloadLength, 0x80, 0x00, 0x30,
                     0x45, 0x12, 0x25, 0x12, 0x15, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x11, 0x22, 0x33,
                     0x44, 0x11, 0x22, 0x33, 0x22, 0x45, 0x67, 0x56, 0x78, 0x03, 0xA4]
        else:
            # make the rest pings
            reply = ['0', '0', '0', '0', '!', '1', '2', '3', '4', '!', Ping]

            # TODO need to put data validation here

    else:
        # Running in normal mode
        # This function returns a packet of data as a string, only returns when data captured
        # Packet = []
        reply = LoRaCommsReceiver.ReturnRadioData(sp)
        logging.info("Received this data to process :%s" % reply)

    return reply
    # return the data from the get data function


def WriteLogFile(Packet):
    # write log file
    LogFileName = "Log" + Packet[StartELBAddr:StartELBAddr+4])
    LogFile = open("Log" + chr(Packet[StartELBAddr]) + "yymmddhhmmss", "w")
    PayloadLength = Packet[StartPayloadLength]
    LogFile.write(Packet[StartPayload:StartPayload+PayloadLength])
    LogFile.close()

def GenerateAck(Packet):
    # Function generates an Ack for response to anumber of messages
    packet_to_send = []
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send.append(ExecByte)                                         # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]    # Sender address
    packet_to_send.append(ExecByte)                     # Executive Byte
    packet_to_send.append(chr(ACK))                     # Acknowledge
    #TODO I think we do not need chr(ACK)
    logging.info("Ack Message :%s" % packet_to_send)

    return packet_to_send

def RespondToPing(fd, Packet, Simulate):
    # responds to the ping command.

    logging.info("Responding to a PING message to the ELB")

    message = GenerateAck(Packet)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)
    # Now need to wait for the answer or timeout.

    return


def RespondDataToSendReq(fd, Packet,Simulate):
    #TODO need fd passed
    # responds to the Data to Send Request
    print("DataToSendRequest")
    HubAddr = Packet[StartHubAddr:StartHubAddr+4]
    ELBAddr = Packet[StartELBAddr:StartELBAddr+4]
    packet_to_send = []
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send.append(ExecByte)                                         # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]   # Sender address
    packet_to_send.append(ExecByte)                                         # Executive Byte
    packet_to_send.append(ClearToSendData)                                  # Clear to Send data command

    #bug
    message = GenerateAck(Packet)
    logging.info("ClearToSendData :%s" % message)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def RespondDataPacketandReq(fd, Packet, Simulate):
    # data packet received and further data is on its way
    print("in respond to data packet received and another to follow")
    message = GenerateAck(Packet)
    logging.info("DataPacketandReq :%s" % message)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def RespondDataPacketFinal(fd, Packet, Simulate):
    # data packet received and no more to come
    print("in respond to last data packet")
    message = GenerateAck(Packet)
    logging.info("Received Final Packet :%s" % message)
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def UnrecognisedCommand(fd,Packet,Simulate):
    # send relevant Nack.
    print("in respond to unrecognised")

    # Function generates an Ack for response to anumber of messages
    packet_to_send = []
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4]  # Receiver address
    packet_to_send.append(ExecByte)  # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4]  # Sender address
    packet_to_send.append(ExecByte)  # Executive Byte
    packet_to_send.append(chr(NackCmdRecog))  # Nack with command unrecognised
    logging.info("Nack Cmd not Recognised Message :%s" % packet_to_send)


def Main():
    # initialise variables
    ComsIdle = True  # set to false when an initial RequestToSendData has been received.
    CurrentELB = "0000"  # when coms has started this variable holds the ELB addr that we are talking to
    # all others will be ignored.
    PacketReceived = False  # set true when a packet has been received - trigger write operation.

    if Simulate != True:
        # Open the serial port and configure the Radio Module
        SerialPort = LoRaCommsReceiver.SetupUART()
        LoRaCommsReceiver.SetupLoRa(SerialPort)
    else:
        SerialPort = 0

    # while True:
    for i in range(10):
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
        print ("Packet of Data %s" % Packet)
        print ("Command Byte Location %s" % StartCommand)
        Command = Packet[StartCommand:StartCommand + 1]  # extract command byte
        # TODO: Need to decode the full message received so I know the ELB address and if the message is for me!
        if ComsIdle:  # not yet in communication with an ELB
            print("ComsIdle = False. i", i)
            if Command == [Ping]:
                RespondToPing(SerialPort, Packet, Simulate)  # respond to a ping command
            elif Command == [DataToSendReq]:
                ComsIdle = False  # coms has started so no longer idle
                RespondDataToSendReq(SerialPort,Packet,Simulate)
                # this will send CleartoSendData.
            else:
                UnrecognisedCommand()
        elif Command == [DataPacketandReq]:  # coms has started and received data packet with more to follow
            RespondDataPacketandReq(SerialPort,Packet,Simulate)     # send ack packet
            WriteLogFile(Packet)            # write this packet to a log file
        elif Command == [DataPacketFinal]:  # coms has started and received final data packet
            RespondDataPacketFinal(SerialPort,Packet,Simulate)
            WriteLogFile(Packet)  # write this packet to a log file
            ComsIdle = True  # reset coms idle
        else:
            UnrecognisedCommand(SerialPort,Packet,Simulate)


# Only call the independent routine if the module is being called directly, else it is handled by the calling program
if __name__ == "__main__":
    logging.basicConfig(filename="LoRaComms.txt", filemode="w", level=logging.DEBUG,
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
