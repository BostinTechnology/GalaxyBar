import serial
import datetime
import time
import math


RESPONSE_NUM_OF_TRIES=2

def set_tries(tries):
    global RESPONSE_NUM_OF_TRIES
    RESPONSE_NUM_OF_TRIES=tries

def flush_port():
    try:
        tries=0
        x=b'88'
        while tries <100 and x != b'' :
            x=port.read(1)
            tries=tries+1
            if x != b'':
                print("flush ",x)
    except:
        return(0)

def open_USB():
    try:     
        global port 
        port = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=10.00, rtscts = True )
        port.close()
        port.open()
        flush_port()
        print("Serial USB connection opened")
        return(1) 
    except:
        print("no Response from the USB Serial Connection")
        port.close()
        return(0)


        


def close():
    try:
        port.close()
        print("Serial connection closed")
    except:
        print("error closing serial connection")        


def open_UART():
    try:      
        port = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=10.00, rtscts = True )
        port.close()
        port.open()
        print("Serial UART connection opened")
        return(1)
    except:
        print("no Response from the UART Serial Connection")
        port.close()
        return(0)




def port_read(x):
    y=b''
    tries=0
    while y == b'' and tries < RESPONSE_NUM_OF_TRIES:
        try:
            y=port.read(x)
#            print("response=",y,RESPONSE_NUM_OF_TRIES)
        except:
            pass        
        tries=tries+1
    return(y)

                  
def write_to_EWC(data):
    trying=RESPONSE_NUM_OF_TRIES
    while trying > 0 :
        try:
            port.write(data)
#            print("write ",data)
            trying=0
        except:
            trying=trying-1
            print("Failed to write to EWC ",data)
            return(0)
    return(1)

  
def byte_to_bcd (byte):
    i=int.from_bytes(byte,"little")
    LSB=int(i/16)*10
    MSB=i-int(LSB/10)*16
    BCD=LSB+MSB
    return(BCD)


def bcd_to_byte(bcd):
    return(bytes([(int(bcd/10)*16+(bcd-int(bcd/10)*10))]))


def NewLogFile(file_name):
    savedLogs = open(file_name,"w")
    savedLogs.write(time.strftime("%y/%m/%d,%H:%M:%S") + "\n")
    savedLogs.close()


def UpdateLogFile (file_name,logfile):
    savedLogs = open(file_name,"a")
    savedLogs.write(logfile + "\n")
    savedLogs.close()


def NewServiceFile(file_name):
    savedLogs = open(file_name,"w")
    savedLogs.write(time.strftime("%y/%m/%d,%H:%M:%S") + "\n")
    savedLogs.close()


def UpdateServiceFile (file_name,logfile):
    savedLogs = open(file_name,"a")
    savedLogs.write(logfile + "\n")
    savedLogs.close()

def read_EEPROM_byte(address):
    bytes_to_send=b'\x45'+bytes([address])+b'\x03'
    check_sum=bytes([ord(b'\x45')^ord(bytes([address]))^ord(b'\x03')])
    check_s=int.from_bytes(check_sum,'little')
    bytes_to_send=bytes_to_send+check_sum      

    write_to_EWC(bytes_to_send)
    
    error_code = port_read(1)
    EWC_ID=-1
    if error_code == b'\x80' : #all ok
        EWC_byte = port_read(1)
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)
#        print("EEPROM byte (",address,") = ",ord(EWC_byte))
        check_sum=bytes([ord(b'\x80')^ord(EWC_byte)^ord(EWC_eof)])
        if check_sum != EWC_chk:
            error_code=b'\x88'
            print("check sum error getting EEPROM byte")
            return(-1)
        else:
            return(EWC_byte)
    return(-1)

def write_EEPROM_byte(address,value):
    bytes_to_send=b'\x50'+bytes([address])+bytes([value])+b'\x03'
    check_sum=bytes([ord(b'\x50')^ord(bytes([address]))^ord(bytes([value]))^ord(b'\x03')])
    check_s=int.from_bytes(check_sum,'little')
    bytes_to_send=bytes_to_send+check_sum      
    
    if write_to_EWC(bytes_to_send):
        if port_read(1) == b'\x80':
            port_read(2)
            return(1)
    return(0)
        

def flow_conversion():
    print("reading flow conversion")
    d1 = read_EEPROM_byte(21)
    if d1 != -1:
        d2 = read_EEPROM_byte(22)
        D=int.from_bytes(d1,'little')*256+int.from_bytes(d2,'little') 
        return(D)
    else:
        return(0)  

    return(0)


def set_flow_conversion(flow):
    print("setting flow_conversion",flow)
    if flow >= 256*256-1 or flow < 0:
        return(0)
    MSB=int(flow/256)
    LSB=flow-(MSB*256) 
    if write_EEPROM_byte(21,MSB):
        if write_EEPROM_byte(22,LSB):
            return(1)
    return(0)


def polling_rate():
    print("reading polling_rate")
    return(int.from_bytes(read_EEPROM_byte(19),'little'))


def set_polling_rate(rate):
    rate=int(16*(math.log(rate,2)+8))		#convert from seconds to EWC rate 70= 1sec
    print("setting polling_rate",rate)
    if rate >= 255 or rate < 0:
        return(0)
    return(write_EEPROM_byte(19,rate))


def credit_low_limit():
    print("reading credit_low_limit")
    return(int.from_bytes(read_EEPROM_byte(20),'little'))


def set_credit_low_limit(limit):
    print("setting credit_low_limit",limit)
    if limit >= 255 or limit < 0:
        return(0)
    return(write_EEPROM_byte(20,limit))


def power_up_count():
    print("reading power_up_count")
    return(int.from_bytes(read_EEPROM_byte(28),'little'))


def set_power_up_count(count):
    print("setting power_up_count",count)
    if count >= 255 or count < 0:
        return(0)
    return(write_EEPROM_byte(28,count))


def id():
    print("reading id")
    EWC_id1 = read_EEPROM_byte(24)
    if EWC_id1 != -1:
        EWC_id2 = read_EEPROM_byte(25)
        EWC_id3 = read_EEPROM_byte(26)
        EWC_id4 = read_EEPROM_byte(27)

        EWC_ID=int.from_bytes(EWC_id1,'little')*256*256*256+int.from_bytes(EWC_id2,'little')*256*256+int.from_bytes(EWC_id3,'little')*256+int.from_bytes(EWC_id4,'little') # ID1*256+ID2

#        print("EWC ID =",EWC_ID)
        return(EWC_ID)
    else:
        return(-1)  


def set_id(id):
    print("setting id",id)
    if id >= 256*256*256*256-1 or id < 0:
        return(0)

    MSB1=int(id/256/256/256)
    MSB2=int(id/256/256)
    MSB3=int(id/256)
    LSB=id-(MSB1*256*256*256)-(MSB2*256*256)-(MSB3*256) 
    if write_EEPROM_byte(24,MSB1):
        if write_EEPROM_byte(25,MSB2):
            if write_EEPROM_byte(26,MSB3):
                if write_EEPROM_byte(27,LSB):
                    return(1)
    return(0)

def valve_on():
    print("turning valve on")
    write_to_EWC(b'\x56\x03\x55')
    if port_read(1) == b'\x80':
        port_read(2)
        return(1)
    print("cannot turn valve on")
    return(0)

def valve_off():
    print("turning valve off")
    write_to_EWC(b'\x4F\x03\x4C')
    if port_read(1) == b'\x80':
        point1 = port_read(1)
        point2 = port_read(1)
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)
        
        check_sum = bytes([ord(b'\x80')^ord(point1)^ord(point2)^ord(EWC_eof)])
#        print("check sums",check_sum,EWC_chk)

        if check_sum != EWC_chk:
            print("valve_off: returned Litres chksum error")
            return(-1)
        
        litres=int.from_bytes(point1,'little')*256+int.from_bytes(point2,'little') # byte1*256+byte2
        return(litres)
    print("valve_off: could not turn valve off")
    return(-1)


def version():
    tries=0
    response=b''
    big_response=b''
    write_to_EWC(b'\x4d\x03\x4e')
    while response != b'\x00' and response != b'\x88' and tries < RESPONSE_NUM_OF_TRIES:     #quit if end of string or error
#        print("response=",response)

        big_response = big_response + response
        response = port_read(1)
        if response == b'' :
            tries=tries+1
        
    if response == b'\x88' :
        print("Error getting version response \x88")
        return(-1)

    try:
        big_response=big_response[4:]
        version_str = big_response.decode("utf-8")
    except:
        version_str='error decoding Vers'
        
    print("tried getting version",tries+1,"times out of",RESPONSE_NUM_OF_TRIES)
    if tries >= RESPONSE_NUM_OF_TRIES:
        print("Time out getting version response")
        return(-1)
    try:
        print(version_str)
        version_str=version_str.split("(")[1].split(")")[0]
    except:
        version_str='error splitting version'
    return(version_str)


def clock_time():
    write_to_EWC(b'\x54\x03\x57')
    error_code = port_read(1)
    if error_code == b'\x80' : #all ok
        secs = port_read(1)
        mins = port_read(1)
        hours = port_read(1)
        day = port_read(1)
        month = port_read(1)
        year = port_read(1)
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)

        ss=byte_to_bcd(secs) # convert the byte 0x36 into 36
        mm=byte_to_bcd(mins)
        hh=byte_to_bcd(hours)
        dd=byte_to_bcd(day)
        MM=byte_to_bcd(month)
        YY=byte_to_bcd(year)
        
        return (ss,mm,hh,dd,MM,YY)

    if error_code == b'\x88':   #failed
        port_read(2)
        print ("error getting ID \x88")
        return(-1,-1,-1,-1,-1,-1)

def set_time(ss,mm,hh,dd,MM,YY):
    ss=bcd_to_byte(ss)
    mm=bcd_to_byte(mm)
    hh=bcd_to_byte(hh)
    dd=bcd_to_byte(dd)
    MM=bcd_to_byte(MM)
    YY=bcd_to_byte(YY)
    bytes_to_send=b'\x43'+ss+mm+hh+dd+MM+YY+b'\x03'
    check_sum=bytes([ord(b'\x43')^ord(ss)^ord(mm)^ord(hh)^ord(dd)^ord(MM)^ord(YY)^ord(b'\x03')])
    check_s=int.from_bytes(check_sum,'little')
    bytes_to_send=bytes_to_send+check_sum                
    length=len(bytes_to_send)

    write_to_EWC(bytes_to_send)
    error_code = port_read(1)
    if error_code == b'\x80' : #all ok
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)
        print("Clock Set OK ")
        return(1)
    if error_code == b'\x88':   #failed
        port_read(2)
        print ("error setting clock ,",error_code)
        return(0)
    print("error setting clock",error_code)
    return(0)
    
def get_log_pointer():
    write_to_EWC(b'\x72\x03\x71')
    error_code = port_read(1)
    if error_code == b'\x80' : #all ok
        point1 = port_read(1)
        point2 = port_read(1)
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)
        
        check_sum = bytes([ord(b'\x80')^ord(point1)^ord(point2)^ord(EWC_eof)])
#        print("check sums",check_sum,EWC_chk)

        if check_sum != EWC_chk:
            print("get_EWC_log_pointer chksum error")
            return(-1)
        
        log_pointer=int.from_bytes(point1,'little')*256+int.from_bytes(point2,'little') # byte1*256+byte2
        return (log_pointer)

    if error_code == b'\x88':   #failed
        port_read(2)
        print ("error getting log pointer \x88")
        return(-1)

    return(-1)

def set_log_pointer(p):

    MSB=int(p/256)
    LSB=p-(MSB*256) 
    
    bytes_to_send=b'\x77'+bytes([MSB])+bytes([LSB])+b'\x03'
    check_sum=bytes([ord(b'\x77')^MSB^LSB^ord(b'\x03')])
    check_s=int.from_bytes(check_sum,'little')
    bytes_to_send=bytes_to_send+check_sum                
    length=len(bytes_to_send)

    write_to_EWC(bytes_to_send)
    error_code = port_read(1)

    if error_code == b'\x80' : #all ok
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)
        print("EWC pointer Set OK to",p)
        return(1)

    if error_code == b'\x88':   #failed
        port_read(2)
        print ("error setting EWC Pointer ,",error_code)
        return(0)
    print ("error setting EWC Pointer ,",error_code)
    

def get_log(pointer):
   
    msb=int(pointer/256)
    lsb=pointer-(msb*256)


    bytes_to_send=b'\x52'+bytes([msb])+bytes([lsb])+b'\x03'

    check_sum=bytes([ord(b'\x52')^msb^lsb^ord(b'\x03')])
    check_s=int.from_bytes(check_sum,'little')

    bytes_to_send=bytes_to_send+check_sum                
    length=len(bytes_to_send)

    write_to_EWC(bytes_to_send)

    time_out = 0
    error_code = b''
    while error_code == b'' and time_out < RESPONSE_NUM_OF_TRIES:
        error_code = port_read(1)
        if error_code == b'' :
            time.sleep(time_out/4)
            time_out = time_out+1
                                       
    if error_code == b'\x80' : #all ok
        EE=port_read(1)
        secs = port_read(1)  
        mins = port_read(1)
        hours = port_read(1)
        day = port_read(1)
        month = port_read(1)
        year = port_read(1)
        uid1 = port_read(1)
        uid2 = port_read(1)
        uid3 = port_read(1)
        uid4 = port_read(1)
        uc1= port_read(1)
        uc2= port_read(1)
        uc3= port_read(1)
        uc4= port_read(1)
        
        sc1 = port_read(1)
        sc2 = port_read(1)
        sc3 = port_read(1)
        sc4 = port_read(1)
        ec1 = port_read(1)
        ec2 = port_read(1)
        ec3 = port_read(1)
        ec4 = port_read(1)
        fc1 = port_read(1)
        fc2 = port_read(1)
        ft1 = port_read(1)
        ft2 = port_read(1)
        EWC_eof = port_read(1)
        EWC_chk = port_read(1)

        log_error=ord(EE)
        ss=byte_to_bcd(secs) # convert the byte 0x36 into 36
        mm=byte_to_bcd(mins)
        hh=byte_to_bcd(hours)
        dd=byte_to_bcd(day)
        MM=byte_to_bcd(month)
        YY=byte_to_bcd(year)

        uid_int= int.from_bytes(uid4,'little')+int.from_bytes(uid3,'little')*256+int.from_bytes(uid2,'little')*256*256+int.from_bytes(uid1,'little')*256*256*256
        uid_hex=format(uid_int,'x')

        uc_int= int.from_bytes(uc4,'little')+int.from_bytes(uc3,'little')*256+int.from_bytes(uc2,'little')*256*256+int.from_bytes(uc1,'little')*256*256*256

        sc_int= int.from_bytes(sc4,'little')+int.from_bytes(sc3,'little')*256+int.from_bytes(sc2,'little')*256*256+int.from_bytes(sc1,'little')*256*256*256

        ec_int= int.from_bytes(ec4,'little')+int.from_bytes(ec3,'little')*256+int.from_bytes(ec2,'little')*256*256+int.from_bytes(ec1,'little')*256*256*256

        fc_int= int.from_bytes(fc2,'little')+int.from_bytes(fc1,'little')*256

        ft_int= int.from_bytes(ft2,'little')+int.from_bytes(ft1,'little')*256
  
        #Check EndCreditValue is correct
        if ec_int ==0 and fc_int ==0:
            ec_int = sc_int

        

        #Convert to correct Flow rate
        flow_rate=0
        pr=polling_rate()
        pr=math.pow(2,(pr/16))/256

        vc=flow_conversion() 

        if ft_int and pr and vc:
            flow_rate = int((fc_int*60)/(ft_int*pr*vc))
        else:
            flow_rate=0

     
        return(id(),log_error, ss,mm,hh,dd,MM,YY, uid_hex,uc_int,sc_int,ec_int,fc_int,flow_rate)

    if error_code == b'\x88':   #failed
        port_read(2)
        print ("error getting log ,",error_code)
        return(0)

    return(0)


