import serial
import datetime
import time
import glob
import os
import sys
import http.client
import RPi.GPIO as GPIO
import ast
import eWATERtap as EWC

RESPONSE_NUM_OF_TRIES = 1

print("eWATERtap-getlog.py Started")

glob_file_name=str(sys.argv[1])
print("filename=",glob_file_name)


def report_on_EWC(file_name):
    EWC.NewServiceFile(service_name)
    EWC.UpdateServiceFile(file_name,str(EWC.version())+","+str(EWC.id())+","+str(EWC.power_up_count())+","+str(EWC.flow_conversion())+","+str(EWC.credit_low_limit())+","+str(EWC.polling_rate()))
            

def get_logfile(name):
    EWC.NewLogFile(name)
    log_error=1

    pointer_max=-1
    tries = 0
    while pointer_max == -1 and tries < RESPONSE_NUM_OF_TRIES: # sleep for increasing time
        pointer_max = EWC.get_log_pointer()
        print("Number of records =",pointer_max)
        if pointer_max == -1:
            time.sleep(pointer_error)
            tries=tries+1
        
    pointer_num = 1
    while pointer_num <= pointer_max:
        tries=0
        EWC_log = 0
        while EWC_log == 0 and tries < RESPONSE_NUM_OF_TRIES:
            EWC_log=EWC.get_log(pointer_num-1)
            if EWC_log==0: # sleep for an increasing amount of time until ok
                print("sleeping")
                time.sleep(log_error)
                tries = tries + 1
                log_error=1
            else:
                log_error=0                 
        EWC.UpdateLogFile(name,str(EWC_log))
        pointer_num = pointer_num + 1


    if log_error==0:
        EWC.set_log_pointer(0)      #   Resets the Tap log to begining
    else:
        EWC.NewLogFile(name)   # failed to get any data records, so empty the log file and DONT reset the tap log pointer

def update_tap():
    ss=int(time.strftime("%S"))
    mm=int(time.strftime("%M"))
    hh=int(time.strftime("%H"))
    dd=int(time.strftime("%d"))
    MM=int(time.strftime("%m"))
    YY=int(time.strftime("%y"))
    EWC.set_time(ss,mm,hh,dd,MM,YY)

    EWC.set_polling_rate(2)
    EWC.set_flow_conversion(600)
    EWC.set_credit_low_limit(40)

    EWC.set_id(1)






print("start time=",time.strftime("%y%m%d%H%M%S"))
log_name=glob_file_name+"log.txt"
service_name=glob_file_name+"serv.txt"

print("log_name=",log_name)   

EWC.set_tries(RESPONSE_NUM_OF_TRIES)

if EWC.open_USB() and EWC.id() != -1:	# Opens the EWC port _USB or _UART and treis to read the version  
    report_on_EWC(service_name)		# create a Service log file for the tap parameters
    get_logfile(log_name)			# create a usage log file
    update_tap()					# update the tap with any changed updates
else:
    print("cannot read EWC data")

EWC.close()
print("end time=",time.strftime("%y%m%d%H%M%S"))
print("eWATERtap-getlog.py Finished")

    
