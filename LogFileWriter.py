#!/usr/bin/env python3
"""
This program is used to take a given packet of data and write it to the log file

It is intended to be used as part of the LoRa Monitor, but it can be run independently.

"""

import logging
import math
import time
from uuid import getnode

#BUG: Tap ID is not defined, set to a default value of 1

TAP_ID = 1

#BUG Polling rate is held within the EEPROM, not accessible to this function at this time!

#   in eWATERTap return(int.from_bytes(read_EEPROM_byte(19),'little'))
POLLING_RATE = 2

#BUG Flow conversion is held within the EEPROM, not accessible to this function
#    d1 = read_EEPROM_byte(21)
#    if d1 != -1:
#        d2 = read_EEPROM_byte(22)
#        D=int.from_bytes(d1,'little')*256+int.from_bytes(d2,'little')
#        return(D)
#    else:
#        return(0)
FLOW_CONVERSION = 600

def byte_to_bcd_old (byte):
    # Taking the given byte, return the binary coded decimal version
    i=int.from_bytes(byte,"little")
    lsb=int(i/16)*10
    msb=i-int(lsb/10)*16
    bcd = lsb + msb
    return bcd

def byte_to_bcd(byte):
    # Taking the given byte as an int, return the bcd equivalent
    if (byte & 0xf0) >> 4 > 9 or (byte & 0x0f) > 9:
        logging.warning("Byte to BCD Conversion encountered a non BCD value, set to 99")
        bcd = 99
    else:
        bcd = int(format(byte,'x'))
    return bcd

def GetMACAddress():
    # Read the MAC address for the ethernet card and return it as a int
    try:
        sys = open('/sys/class/net/eth0/address').read()
    except:
        sys = '00:00:00:00:00:00'
        logging.warning("Reading of the MAC address from system file failed")
    logging.debug("MAC Address captured (all zero's is a failure):%s" % sys)
    mac = sys.replace(':','')

    return mac[0:12]

def GenerateLogData(tap_id, data_packet):
    # Given the binary string of data, return the data to be written to the log file
    # This function assumes data passed in has been validated

    # Split each byte of the packet into the various bits.
    try:
        EE=data_packet[0]
        secs = data_packet[1]
        mins = data_packet[2]
        hours = data_packet[3]
        day = data_packet[4]
        month = data_packet[5]
        year = data_packet[6]
        uid1 = data_packet[7]
        uid2 = data_packet[8]
        uid3 = data_packet[9]
        uid4 = data_packet[10]
        uc1= data_packet[11]
        uc2= data_packet[12]
        uc3= data_packet[13]
        uc4= data_packet[14]
        sc1 = data_packet[15]
        sc2 = data_packet[16]
        sc3 = data_packet[17]
        sc4 = data_packet[18]
        ec1 = data_packet[19]
        ec2 = data_packet[20]
        ec3 = data_packet[21]
        ec4 = data_packet[22]
        fc1 = data_packet[23]
        fc2 = data_packet[24]
        ft1 = data_packet[25]
        ft2 = data_packet[26]
    except:
        logging.Wwarning("Splitting of data into 27 bytes failed")
        return {'success':False, 'data':[]}


    # Create the values to be written into the log file

    log_error=EE            # data is already a single byte
    # Decode the time
    ss=byte_to_bcd(secs)
    mm=byte_to_bcd(mins)
    hh=byte_to_bcd(hours)
    dd=byte_to_bcd(day)
    MM=byte_to_bcd(month)
    YY=byte_to_bcd(year)

    # Decode the Tag ID
    uid_int= uid4 + (uid3*256) + (uid2*256*256) + (uid1*256*256*256)
    uid_hex=format(uid_int,'x')

    # Decode the Usage Count
    uc_int= uc4 + (uc3*256) + (uc2*256*256) + (uc1*256*256*256)

    # Decode the Start Credit
    sc_int= sc4 + (sc3*256) + (sc2*256*256) + (sc1*256*256*256)

    #Decode the End Credit
    ec_int= ec4 + (ec3*256) + (ec2*256*256) + (ec1*256*256*256)

    # Decide the Flow Count
    fc_int= fc2 + (fc1*256)

    # Decode the Flow Rate
    ft_int= ft2 + (ft1*256)

    #Check EndCreditValue is correct
    if ec_int ==0 and fc_int ==0:
        ec_int = sc_int

    #Convert to correct Flow rate
    flow_rate=0

#BUG: Polling rate is held within the eeprom, not able to access it at the moment
    pr = POLLING_RATE
    # pr=polling_rate()         #Polling Rate is not defined, reda out of EEPRON somewhere
    pr=math.pow(2,(pr/16))/256

#BUG: Flow Conversion is calculated from values is held within the eeprom, not able to access it at the moment
    vc=FLOW_CONVERSION

    if ft_int and pr and vc:
        flow_rate = int((fc_int*60)/(ft_int*pr*vc))
    else:
        flow_rate=0

    mac_addr = GetMACAddress()

    data = (tap_id,log_error, ss,mm,hh,dd,MM,YY, uid_hex,uc_int,sc_int,ec_int,fc_int,flow_rate, mac_addr)

    return{'success': True, 'data':data}


def CheckPacket(data_packet):
    # Function takes the given packet of data and checks it is suitable
    # returns True if ok, False if not
    success = False

    if len(data_packet) < 27:
        logging.WARNING("data packet too short, logging aborted with packet: %s" % data_packet)

    logging.debug("Data Packet ok to Use")
    return True

def WriteLogFile(elb_name, data_to_write):
    # write log file.
    # takes a packet and appends it to a log file. This is the output from the Hub Decoder

#BUG: This needs to be in a try / except loop

    FileTime = time.strftime("%y%m%d%H%M%S",time.localtime())
    LogFile = open("ELB" + str(elb_name) + FileTime + ".txt", "w")
    LogFile.write(data_to_write)
    logging.debug("Written data to log file!: %s" % data_to_write)
    LogFile.close()

    return

def ConvertToString(payload):
    # Function that converts the list to a string
    response = str(payload)
    response = response.lstrip('(')
    response = response.rstrip(')')

    return response

def ConvertToCSV(payload):
    # Convert the payload to a string for the CSV file
    output_data = ""
    for i in payload:
        output_data = output_data + str(i) + ","
    #output_data.rstrip(',')
    output_data = output_data.strip(',')
    logging.debug("String version of the payload: %s" % output_data)
    return output_data

def GenerateSampleData():
    # Creates same data and returns it

    sample_data = b'123456789012345678901234567'
    logging.info("Sample Data Packet:%s" % sample_data)
    return sample_data

def GenerateSampleELBName():
    # Creates the same ELB name for testing and returns it

    sample_elbname = b'1234'
    logging.info("Sample ELB Name:%s" % sample_elbname)
    return sample_elbname

def ConvertELBName(elb_name):
    # Take the given EBL address as a binary string and return a string
    try:
        tap_id = int(elb_name,16)
    except:
        tap_id = TAP_ID
        logging.warning("Unable to convert ELB Name, suing default")
    return tap_id

def LogFileCreation(elb_bytes, payload):
    # this function is called from the main program to write data to the log file

    if CheckPacket(payload):
        elb = ConvertELBName(elb_bytes)
        logdata = GenerateLogData(elb, payload)
        if logdata['success']:
            logdata = ConvertToString(logdata)
            WriteLogFile(elb, logdata)

    return


def main():


    # Need to be given the ELB Name and the payload


    logging.basicConfig(filename="LogFileWriter.txt", filemode="w", level=logging.DEBUG,
                        format='%(asctime)s:%(levelname)s:%(message)s')

    sample = GenerateSampleData()
    elb_bytes = GenerateSampleELBName()
    if CheckPacket(sample):
        elb = ConvertELBName(elb_bytes)
        logdata = GenerateLogData(elb, sample)
        if logdata['success']:
            #logdatacsv = ConvertToCSV(logdata['data'])
            data = ConvertToString(logdata['data'])
            WriteLogFile(elb, data)

    return


if __name__ == '__main__':
    main()

