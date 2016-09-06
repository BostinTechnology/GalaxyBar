#!/usr/bin/env python3
"""
Program to monitor and listen to LoRa transmissions

Uses Tkinter to provide a graphical interface
Screen layout
Useful Buttons across the top
Intrepreted command - decoded view of the command
Command stream - a flow of messages coming in
"""

from tkinter import *
#from tkinter import ttk

import random
import logging

logging.basicConfig(filename="LoRaMonitor.txt", filemode="w", level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

import LoRaCommsReceiver


# MAXROWS is the maximum number of rows to be in the stream window
MAXROWS = 10,000

#TODO: Display the data in hex, not numeric.
#TODO: Control the maximum number of rows in the stream window.
#TODO: Implement Save
#TODO: Have the buttons change for when they are clicked or unclicked.

class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self,master)

        # These variables are used to display the decoded values
        self.decodesender=StringVar()
        self.decodereceiver=StringVar()
        self.decodecommand=StringVar()
        self.decodepayload=StringVar()
        self.running = False    # Used to determine if we are capturing or not.

        # Create a Tkinter variable, a instance variable and set them to the same
        self.strm = StringVar()
        self.stream = []

        # These variables are for the selected items from the list
        self.selectedtext = ""
        self.selectedlist = []
        self.selectedposn = 0

        # Build the header row
        header_frame = Frame(self, relief='ridge')
        Label(header_frame, text="Lora Monitor").grid(row=0, column=0, sticky=W, padx=10)
        Label(header_frame, text="Bostin Technology").grid(row=0, column=4, sticky=E, padx=10)
        header_frame.grid(row=0)

        # Build the buttons row
        buttons_frame = Frame(self, relief='ridge')
        capture = Button(buttons_frame, text="Capture", command=self.capture).grid(row=1, column=0, padx=5)
        pause = Button(buttons_frame, text="Pause", command=self.pause).grid(row=1, column=1, padx=5)
        save = Button(buttons_frame, text="Save", command=self.save).grid(row=1, column=2, padx=5)
        clear = Button(buttons_frame, text="Clear", command=self.clear).grid(row=1, column=3, padx=5)
        exit_program = Button(buttons_frame, text="Exit", command=self.exit_program).grid(row=1, column=4, padx=5)
        buttons_frame.grid(row=1, pady=5)

        # Build the decode frame
        decode_frame = LabelFrame(self, text="Detailed View")
        Label(decode_frame, text="Sender Address:").grid(row=0, column=0, sticky=NW)
        Label(decode_frame, textvariable=self.decodesender, width=25, justify=LEFT).grid(row=0, column=1, sticky=NW)
        Label(decode_frame, text="Receiver Address:").grid(row=0, column=2, sticky=NW)
        Label(decode_frame, textvariable=self.decodereceiver, width=25, justify=LEFT).grid(row=0, column=3, sticky=NW)
        Label(decode_frame, text="Command:").grid(row=1, column=0, sticky=NW)
        Label(decode_frame, textvariable=self.decodecommand, width=5, justify=LEFT).grid(row=1, column=1, sticky=NW)
        Label(decode_frame, text="Payload:").grid(row=2, column=0, sticky=NW)
        Label(decode_frame, textvariable=self.decodepayload, justify=LEFT, height=3, width=100, wraplength=800).grid(row=3, column=0, columnspan=4, sticky=NW)
        decode_frame.grid(row=2)

        # Build the streaming row
        stream_frame = LabelFrame(self, text="Monitoring Stream")
        self.streambox = Listbox(stream_frame, listvariable=self.strm, height=20, width=110, selectmode=SINGLE)
        self.streambox.grid(row=0, column=0)
        self.streambox.bind("<<ListboxSelect>>",self.SelectText)
        # TODO: need to add a scroll bar -
        stream_frame.grid(row=3)

        # Put it all together on the screen
        self.pack(fill=BOTH, expand=NO)
        root.after(100, self.Running)

    def Running(self):
        """
        This is called every 100 millieconds and manages all the updates for the screen.
        """
        if self.running:
            # .after is a 1 shot timer, after 100mS, the self.update method is called
            self.UpdateStream()
        root.after(100, self.Running)


    def SetStream(self, newtext):
        logging.debug("New text passed in:%s" % newtext)
        self.stream = newtext

    def UpdateStream(self):
        """
        If there is any data in the incoming stream, add it to the listbox,
        but then clear the incoming stream to stop it being re-added!
        """
        if len(self.stream) >0:
            logging.debug("Length of the data to be added:%d" % len(self.stream))
#BUG: Text needs to be displayed as hex, not numeric. Don't know if this is possible??
            self.streambox.insert(0,self.stream)
            self.stream = []
        root.update_idletasks()

    def SelectText(self,event):
        # Called when the user clicks on a row of data
        # Get the data out of the listbox, it is returned as a string
        self.selectedposn = self.streambox.curselection()
        if len(self.selectedposn) == 0:
            logging.debug("Clicked on Listbox, but the box was empty so returned")
            return
        logging.debug("Selected Text position(self.selectedposn):%s" % self.selectedposn)
        self.selectedtext = self.streambox.get(self.selectedposn)
        #first strip the sq brackets and then split it back into a list
        logging.info("Selected Text(self.selectedtext):%s" % self.selectedtext)
        self.selectedtext = self.selectedtext.strip("[]")
        self.selectedlist = self.selectedtext.split(", ")
        logging.debug("Selected List (self.selectedlist):%s" % self.selectedlist)
        self.Decode()
        return

    def Decode(self):
        """
        Uses the currently selected self.selectedtext to populate the decode variables
        """
        self.decodesender.set(self.selectedlist[0:5])
        logging.info("Decoded Sender:%s" % self.decodesender)
        self.decodereceiver.set(self.selectedlist[5:10])
        logging.info("Decoded Receiver:%s" % self.decodereceiver)
        self.decodecommand.set(self.selectedlist[10:11])
        logging.info("Decoded Command:%s" % self.decodecommand)
        self.decodepayload.set(self.selectedlist[11:len(self.selectedlist)])
        logging.info("Decoded Payload:%s" % self.decodepayload)
        return

    def capture(self):
        # called form the capture button
        logging.debug("Starting Capture")
        self.running = True
        return

    def save(self):
        print("Not Yet Implemented")
        return

    def clear(self):
        # Empty the incoming string, the holding variable and clear the listbox contents
        self.stream.clear()
        self.strm.set(self.stream)
        self.streambox.delete(0,END)

        print("Self.stream:%s" % self.stream)
        print("Self.strm  :%s" % self.strm)
        return

    def pause(self):
        # called from the stop button
        logging.debug("Stopping Capture")
        self.running = False
        return

    def exit_program(self):
        exit()
        return

def GetValue():
    # Function to retrieve the value from the LoRa
    # Just an example at the moment
    # This is self running and will ssend new data every 1000mS
    text_to_add = []
    text_to_add = LoRaCommsReceiver.ReadData(comm)
    text_to_add = text_to_add['reply'][0]
    logging.debug("Data to be added:%s" % text_to_add)
    if len(text_to_add) >0:
        app.SetStream(text_to_add)
    root.after(10, GetValue)    #was 1000



root = Tk()
app = App(master=root)
app.master.title("LoRa Monitoring Tool")
LoRaCommsReceiver.SetupGPIO()
comm = LoRaCommsReceiver.SetupUART()
LoRaCommsReceiver.SetupLoRa(comm)

GetValue()
app.mainloop()


