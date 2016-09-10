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
Simulate = False  # set this to false if using the radio module
import argparse
import logging
import time

if Simulate != True:
    import LoRaCommsReceiver
    import LogFileWriter

# How long we wait for a data packet
COMMS_TIMEOUT = 2

# constants that will not change in program
# command bytes that are used by LoRa module
DataToSendReq = chr(0x34).encode('utf-8')
ClearToSendData = chr(0x35).encode('utf-8')
DataPacketandReq = chr(0x36).encode('utf-8')
DataPacketFinal = chr(0x37).encode('utf-8')
Ping = chr(0x32).encode('utf-8')
# ack codes
ACK = chr(0x22).encode('utf-8')                 # all good and confirmed
NackPreamble = chr(0x50).encode('utf-8')        # preamble erro - ascii P
NackCRC = chr(0x51).encode('utf-8')             # CRC error - ascii Q
NackAddrError = chr(0x60).encode('utf-8')       # address error - ascii '
NackMsgLen = chr(0x61).encode('utf-8')          # message length inconsisten - ascii a
NackPayload = chr(0x70).encode('utf-8')         # payload crc error- ascii p
NackCmdRecog = chr(0x7A).encode('utf-8')        # command not recognised - ascii €
    # should be 0x80 but logging doesn't seem to handle above 0x7F
NackCmdSync = chr(0x7B).encode('utf-8')         # command out of protocol sync
NackNotReadyforData = chr(0x7C).encode('utf-8') # not ready for data ascii ,


# initialise global variables for data packet. Defined here so that they are global
Packet = b''  # start with empty packet.
# pointers in packet
StartHubAddr = 0  # poisiton in packet where hub addr starts
StartELBAddr = 5  # posiiton in packet where ELB starts
StartCommand = 10  # posiiton of command byte
StartPayloadLength = 11  # position of payload length byte
StartPayload = 12  # poition of start of payload
# TODO - check these pointers are true of ping, request to send and data packets
ExecByte = "!".encode('utf-8')      # The executive by

ZeroPayload = chr(0x00).encode('utf-8')           # used to indicate there is zero payload

# Initialise files

def ValidatePayload (Packet):
    # checks payload of the packet and looks for CRC
    # assumesthat only a packet with daat is sent to this routine

    PayloadValid = False                                # assume payload is not valid
    PayloadLength = int(Packet[StartPayloadLength])     # get payload length
    Payload = Packet[StartPayload:StartPayload + PayloadLength]        # extract payload
    Checksum = 0                                  # zero checksum
    for i in range(PayloadLength):                  # check each byte in the payload
        Checksum = Checksum ^ int(Packet[StartPayload + i])

    return Checksum == 0        # checsum vald if equal to 0

def ValidatePacket (Packet):
    # routine to validate a packet that has been received
    # checks for 5th and 10th bytes to be '!' or '>'
    # checks length to ba ta least 12 bytes
    # for if command is DataPacketandReq or DataPacketFinal then it can perform a CRC on the payload

    ValidPacket = False         # assume packet is invalid
    if chr(Packet[StartHubAddr+4]).encode('utf-8') == b'!' or chr(Packet[StartHubAddr+4]).encode('utf-8') == b'>':
            # packet has valid 1st address descripters so continue
        if chr(Packet[StartELBAddr+4]).encode('utf-8') == b'!' or chr(Packet[StartELBAddr+4]).encode('utf-8') == b'>':
            # 2nd addr descripter valid so continue
            if len(Packet) >= 12:                       # packet is long enough so continue
                if chr(Packet[StartCommand]).encode('utf-8') == DataPacketandReq or \
                        chr(Packet[StartCommand]).encode('utf-8') == DataPacketFinal:
                            # now check payload
                   ValidPacket = ValidatePayload(Packet)
                elif chr(Packet[StartCommand]).encode('utf-8') == Ping or \
                            chr(Packet[StartCommand]).encode('utf-8') == DataToSendReq:
                    # no payload so only addr descripters and messag elength can be used
                    ValidPacket = True

    return ValidPacket

def GetModuleData(sp, Simulate):
    # this module supplies a packet every time it is called
    # if simulating then packets are created and returned. The returned packet depends on the value of sp passed.

    if Simulate:
        # Simulation Packets
        HubAddr = b'0000!'
        Hub2Addr= b'2222!'
        ELB1Addr = b'1234!'
        ELB2Addr = b'5678!'
        ELB3Addr = b'9876!'


        ELB1_Ping = HubAddr +ELB1Addr + Ping + ZeroPayload  # zero payload on end
        ELB2_Ping = HubAddr +ELB2Addr + Ping + ZeroPayload
        ELB1_DataToSendReq = HubAddr + ELB1Addr + DataToSendReq + ZeroPayload
        ELB2_DataToSendReq = HubAddr + ELB2Addr + DataToSendReq + ZeroPayload
        HUB_to_ELB1_ClearToSendData = ELB1Addr + HubAddr + ClearToSendData + ZeroPayload
        HUB2_to_ELB3_ClearToSendData = ELB1Addr + HubAddr + ClearToSendData + ZeroPayload
        ELB1_DataPacketandReq = HubAddr + ELB1Addr + DataPacketandReq + \
                            chr(37).encode('utf-8')+ b'Data from ELB 1. More data to follow' + b'\x7d'
        ELB2_DataPacketandReq = HubAddr + ELB2Addr + DataPacketandReq + \
                            chr(37).encode('utf-8') + b'Data from ELB 2. More data to follow' + b'\x7e'
        ELB1_DataPacketFinal = HubAddr + ELB1Addr + DataPacketFinal + \
                            chr(30).encode('utf-8') + b'Data from ELB 1. Final Packet' + b'\x36'
        ELB2_DataPacketFinal = HubAddr + ELB2Addr + DataPacketFinal + \
                            chr(29).encode('utf-8') + b'Data from ELB 2. Final Packet' + b'\00'
        Hub_Ack_ELB1 = ELB1Addr + HubAddr + ACK + b'\x00'   # add zero payload on end
        Hub_Ack_ELB2 = ELB2Addr + HubAddr + ACK + b'\x00'
        ELB_Unrecognised = HubAddr + ELB1Addr + b'u' + ZeroPayload
        Hub_to_ELB1_Nack_NotReady = HubAddr + ELB1Addr + NackNotReadyforData + ZeroPayload
        Hub_to_ELB2_Nack_NotReady = HubAddr + ELB2Addr + NackNotReadyforData + ZeroPayload
        Hub_to_ELB1_Nack_Unrecog = HubAddr + ELB1Addr + NackCmdRecog + ZeroPayload
        Hub_to_ELB2_Nack_Unrecog = HubAddr + ELB2Addr + NackCmdRecog + ZeroPayload

        Payload = chr(0x7F) + chr(0x00) + chr(0x30) + \
                  chr(0x45) + chr(0x12) + chr(0x25) + chr(0x12) + chr(0x15) + chr(0x01) + chr(0x02) + chr(0x03) + \
                  chr(0x04) + chr(0x05) + chr(0x06) + chr(0x07) + chr(0x08) + chr(0x11) + chr(0x22) + chr(0x33) + \
                  chr(0x44) + chr(0x11) + chr(0x22) + chr(0x33) + chr(0x22) + chr(0x45) + chr(0x67) + chr(0x56) + \
                  chr(0x78) + chr(0x03) + chr(0xA4)
        Payload = Payload.encode('utf-8')
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
        Simulation_Packets = [
                b'0000!\x00\x11$\xb4U2\x00',    # string from ELB
                ELB1_Ping,                      # 0: ELB1 ping
                ELB1_DataToSendReq,             # 1: ELB1 requesting to send data
                ELB1_DataPacketandReq,          # 2: Data from ELB. More to follow
                ELB1_DataPacketFinal,           # 3: final data from ELB1
                ELB1_Ping,                      # 3: ELB1 ping
                    # ComsIdle now True
                ELB1_DataPacketandReq,          # 5: Data from ELB with no ClearToSendData
                ELB1_DataPacketFinal,           # 6: Final data from ELB1 with no ClearToSend
                HUB2_to_ELB3_ClearToSendData,   # 7: Clear to send from another hub
                ELB_Unrecognised,               # 8: Unrecognised command
                ELB1_Ping,                      # 9: ELB1 ping
                ELB1_DataToSendReq,             # 10: ELB1 requesting to send data.
                    # ComsIdle now False
                ELB2_Ping,                      # 11: ping from ELB2 after data to send req
                ELB2_DataPacketandReq,          # 12: data packet from another ELB
                HUB2_to_ELB3_ClearToSendData,   # 13: Cler to Send from another hub
                ELB_Unrecognised,               # 14: Unrecognised command
                ELB1_DataPacketFinal,           # 15: Final data packet from ELB1
                    #ComsIdle now true
                ELB1_Ping,                      #16: ELB1 ping
                ELB2_Ping,                      # 17: ELB 2 ping
                ELB2_DataToSendReq,             # 18: Start coms with ELB 2
                ELB1_DataToSendReq,             # 19: ELB 1 tries to send data at teh same time
                ELB1_Ping,                      # 20: ELB 1 pings hub
                ELB2_DataPacketandReq,          # 21: ELB2 send data
                ELB1_DataToSendReq,             # 22: ELB1 tries again
                ELB1_DataPacketFinal,           # 23: ELB1 sends data
                ELB2_DataPacketFinal            # 24: final data from ELB2
            ]

        reply = Simulation_Packets[sp]

    else:
        # Running in normal mode
        # This function returns a packet of data as a string, only returns when data captured
        # Packet = []
        reply = LoRaCommsReceiver.ReturnRadioData(sp)

    logging.info(' ')  # force new lne
    print("[GMD] - Received this data to process :%s" % reply, flush=True)
    logging.info("Received this data to process :%s" % reply)

    return reply
    # return the data from the get data function


def WriteLogFile(Packet):
    # Takes the given log file and passes it to the writing routine

#    ELBName = ''.join([hex(i) for i in Packet[StartELBAddr:StartELBAddr+4]])
        # takes 4 bytes of ELB addr and converts to a hex string, eg. 0x000x110x240xb4
    ELBName = Packet[StartELBAddr:StartELBAddr+4]
        # Pass the ELB name into the logwriter
    PayloadLength = Packet[StartPayloadLength]     # get payload length as int
    DataToWrite = Packet[StartPayload:StartPayload+PayloadLength]
    logging.debug("Write from ELB:%s, this length %s this data:%s" % (ELBName, PayloadLength, DataToWrite))

    if Simulate != True:
        LogFileWriter.LogFileCreation(ELBName, DataToWrite)

    else:
        print("\nData to be written:\n %s \n" % DataToWrite)
    return

def GenerateAck(Packet):
    # Function generates an Ack for response to a number of messages
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send = packet_to_send + ExecByte                                         # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]    # Sender address
    packet_to_send = packet_to_send +  ExecByte                     # Executive Byte
    packet_to_send = packet_to_send + ACK                     # Acknowledge
    packet_to_send = packet_to_send + ZeroPayload                   # add zero payload length

    return packet_to_send

def RespondToPing(fd, Packet, Simulate):
    # responds to the ping command.

    message = GenerateAck(Packet)
    logging.info("Responding to a PING - Ack Message :%s" % message)
    print("Send ACK :%s" % message)      # send message to execution window
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)
    # Now need to wait for the answer or timeout.

    return


def RespondDataToSendReq(fd, Packet,Simulate):
    # responds to the Data to Send Request

    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr+4]   # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byt
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr+4]   # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + ClearToSendData                       # Clear to Send data command
    packet_to_send = packet_to_send + ZeroPayload                               # add zero payload length

    logging.info("ClearToSendData :%s" % packet_to_send)
    print("[HDC-Rto CTS] - Clear to Send :%s" % packet_to_send)      # send message to execution window
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def RespondDataPacketandReq(fd, Packet, Simulate):
    # data packet received and further data is on its way

    message = GenerateAck(Packet)
    logging.info("DataPacketandReq :%s" % message)
    print("Data. More to follow :%s" % message)      # send message to execution window
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def RespondDataPacketFinal(fd, Packet, Simulate):
    # data packet received and no more to come

    message = GenerateAck(Packet)
    logging.info("Received Final Packet :%s" % message)
    print("Final data :%s" % message)      # send message to execution window
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, message)


def UnrecognisedCommand(fd,Packet,Simulate):
    # send relevant Nack.

    print ("Unrecognised Command")
    # Function generates an Ack for response to anumber of messages
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackCmdRecog                          # Nack with command unrecognised
    packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length
    logging.info("Nack Cmd not Recognised Message :%s" % packet_to_send)
    print("Unrecognised Command :%s" % packet_to_send)      # send message to execution window
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def SendPiBusyNack(fd,Packet,Simulate):
    # have been pinged from 2nd ELB while receiving data from 1st ELB
    # Function generates an Ack for response to anumber of messages
    packet_to_send = b''
    packet_to_send = packet_to_send + Packet[StartELBAddr:StartELBAddr + 4] # Receiver address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + Packet[StartHubAddr:StartHubAddr + 4] # Sender address
    packet_to_send = packet_to_send + ExecByte                              # Executive Byte
    packet_to_send = packet_to_send + NackNotReadyforData                   # Nack with command unrecognised
    packet_to_send = packet_to_send + ZeroPayload                           # add zero payload length
    logging.info("Nack Not Ready for Data :%s" % packet_to_send)
    print('Pi busy Nack :%s' % packet_to_send)      # send message to execution window
    if Simulate != True:
        LoRaCommsReceiver.RadioDataTransmission(fd, packet_to_send)


def Main():
    # initialise variables
    ComsIdle = True  # set to false when an initial RequestToSendData has been received.
    CurrentELB = b''  # when coms has started this variable holds the ELB addr that we are talking to
    TimeLastValidPacket = time.time()       # reset time of last valid packet

    if Simulate != True:
        # Open the serial port and configure the Radio Module
        LoRaCommsReceiver.SetupGPIO()
        SerialPort = LoRaCommsReceiver.SetupUART()
        LoRaCommsReceiver.SetupLoRa(SerialPort)
    else:
        SerialPort = 0

    while True:
        i=0
        print("NEW LOOP IN MAIN", flush=True)
    #for i in range(25):
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

        if ValidatePacket(Packet):       # is this a valid packet
            logging.info("This data is valid :%s" % Packet)
            print ("[MAIN] - This data is valid")   # print packet to window
            TimePacketReceived = time.time()        # The time the last valid packet was received
            Command = chr(Packet[StartCommand]).encode('utf-8')          # extract command byte as byte String
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
            if (TimePacketReceived - TimeLastValidPacket) > COMMS_TIMEOUT:
                # this data packet was received outside the comms window
                ComsIdle = True

            if ComsIdle:  # not yet in communication with an ELB
                if Command == Ping:
                    RespondToPing(SerialPort, Packet, Simulate) # respond to a ping command
                elif Command == DataToSendReq:
                    ComsIdle = False                            # coms has started so no longer idle
                    CurrentELB = Packet[StartELBAddr:StartELBAddr+4]
                    RespondDataToSendReq(SerialPort,Packet,Simulate)
                    TimeLastValidPacket = TimePacketReceived # time.time()
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
                    TimeLastValidPacket = TimePacketReceived # time.time()
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
                        RespondToPing(SerialPort,Packet,Simulate)      # send Ack to ping
                    elif Command == DataToSendReq or Command == ClearToSendData:
                        logging.info("DataToSendReq or ClearToSendData when already in coms :%s" % Packet)
                    else:
                        UnrecognisedCommand(SerialPort, Packet, Simulate)
                        # send Nack with unrecognised cmd
        else:
            logging.info("This data is invalid :%s" % Packet)
            print("This data is invalid :%s" % Packet)      # send message to execution window

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
