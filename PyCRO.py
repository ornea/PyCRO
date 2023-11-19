# PyCRO(w)  (17-Nov-2023)
# For Python version 3
# With external module pyaudio (for Python version 3); NUMPY module (for used Python version)
# Created by Onno Hoekstra (pa2ohh)
#
# 17/9/15 Rich Heslip VE3MKC https://github.com/rheslip/PyDSA
# modified to capture samples from Rigol DS1102E scope for a basic 100Mhz SA
#
# This version slightly has a modified Sweep() routine for the DS1054Z by Kerr Smith Jan 31 2016

# Nov 2023 This version modified to simply plot the original trace,(no FFT)  log data and screenshots with pretty's such as Quantiphy by JPR
#
import os
import math
import time
import numpy
#import tkFont
import tkinter.font as TkFont
import sys
#from telnetlib_receive_all_py3 import Telnet
#import visa
from ds1054z import DS1054Z #invalid measuremnts usually return 'None' my version has been modified to return  9.9e37 passed on from the scope: # This is a value which means that the measurement cannot be taken for some reason (channel disconnected/no edge in the trace etc.)
from time import sleep
from tkinter import *
from quantiphy import Quantity
from tkinter import ttk
from tkinter import messagebox

import tkinter.filedialog as simpledialog
import tkinter.simpledialog as simpledialog
#from tkFileDialog import askopenfilename
#from tkSimpleDialog import askstring
#from tkMessageBox import *

shutdown = "no"

NUMPYenabled = True         # If NUMPY installed, then the FFT calculations is 4x faster than the own FFT calculation

company = 0
model = 1
serial = 2
# Values that can be modified
GRWN = 1024                  # Width of the grid
GRHN = 512                  # Height of the grid
X0L = 20                    # Left top X value of grid
Y0T = 25                    # Left top Y value of grid

Vdiv = 8                    # Number of vertical divisions

TRACEreset = True           # True for first new trace, reset max hold and averageing
SWEEPsingle = False         # flag to sweep once

SAMPLErate = 1000000        # scope sample rate, read from scope when we read the buffer
SAMPLEsize = 16384          # default sample size
SAMPLEdepth = 0             # 0 normal, 1 long
YREFerence = 0
XREFerence = 0
YORigion = 0
XORigion = 0


filename = ""
startLogTime =""

SCALElist = [0.01,0.02,0.05,0.1,0.2,0.5,1,2,5]
DBdivlist = [1, 2, 3, 5, 10, 20] # dB per division
DBdivindex = 5              # 20 dB/div as initial value

ParameterList = ["VMAX","VMIN","VPP","VTOP","VBASe","VAMP","VAVG",
    "VRMS","OVERshoot","PREShoot","MARea","MPARea","PERiod",
    "FREQuency","RTIMe","FTIMe","PWIDth","NWIDth","PDUTy",
    "NDUTy","TVMAX",
    "TVMIN","PSLEWrate","NSLEWrate","VUPper","VMID","VLOWer",
    "VARIance","PVRMS","PPULses","NPULses","PEDGes","NEDGes",
    "RPM"]

ParameterUnitsList = ["V","V","V","V","V","V","V",
    "V","V","V","V/S","V/S","S",
    "Hz","S","S","S","S","%",
    "%","S",
    "S","V/S","V/S","V","V","V",
    "V2","V","P","P","E","E",
    "rpm"]


ChannelCouplinglist = ["DC","AC","GND"]
ChannelList = ["CHANNEL 1","CHANNEL 2","CHANNEL 3","CHANNEL 4"]


# Colors that can be modified
COLORframes = "#000080"     # Color = "#rrggbb" rr=red gg=green bb=blue, Hexadecimal values 00 - ff
COLORcanvas = "#000000"
COLORgrid = "#808080"
COLORtrace1 = "#00ff00"
COLORtrace2 = "#ff8000"
COLORtext = "#ffffff"
COLORsignalband = "#ff0000"
COLORaudiobar = "#606060"
COLORaudiook = "#00ff00"
COLORaudiomax = "#ff0000"
COLORred = "#ff0000"
COLORyellow = "#ffff00"
COLORgreen = "#00ff00"
COLORmagenta = "#00ffff"
COLORlightgrey = "#D3D3D3"
COLORMarker1= "#ff0000"
COLORMarker2= "#00ffff"
COLORMarkerP= "#ffff00"

# Button sizes that can be modified
Buttonwidth1 = 12
Buttonwidth2 = 8


# Initialisation of general variables
CHANNEL = 1
triggerLevel = 0.0        # triggerLevel
STOPfrequency = 10000000.0     # Stopfrequency
TimebasePerDiv = "0" 
VoltPerDiv = "0"
VoltsPeakPeak = "0"
SweepNo = 0 


# Other global variables required in various routines

GRW = GRWN                  # Initialize GRW
GRH = GRHN                  # Initialize GRH

CANVASwidth = GRW + 2 * X0L # The canvas width
CANVASheight = GRH + 80     # The canvas height

SIGNAL1 = []                # trace channel 1

FFTresult = []              # FFT result
T1line = []                 # Trace line channel 1
T2line = []                 # Trace line channel 2

RUNstatus = 1               # 0 stopped, 1 start, 2 running, 3 stop now, 4 stop and restart
STOREtrace = False          # Store and display trace
                            # 3=Hann (B=1.5), 4=Blackman (B=1.73), 5=Nuttall (B=2.02), 6=Flat top (B=3.77)
SIGNALlevel = 0.0            # Level of audio input 0 to 1


vertMarkerNo = 0
Marker1x = [0,0]                # marker pip 1 location
Marker1y = [0,0]

Marker2x = 0                # marker pip 2
Marker2y = 0

if NUMPYenabled == True:
    try:
        import numpy.fft
    except:
        NUMPYenabled = False


# =================================== Start widgets routines ========================================
def Bnot():
    print ( "Routine not made yet" )

def on_click(self, event):
        # Last click in absolute coordinates
        self.prev_var.set('%s:%s' % self.last_point)
        # Current point in relative coordinates
        self.curr_var.set('%s:%s' % (event.x - self.last_point[0], event.y - self.last_point[1]))
        self.last_point = event.x, event.y
        print ("here")

# handle markers when mouse is clicked in middle frame
def Bmarker1(event):
    global Marker1x
    global Marker1y
    global Y0T
    global X0L
    global GRH
    global GRW
    global vertMarkerNo


    if ((event.x > 20) & (event.y >20) & (event.y<Y0T + GRH) & (event.x<X0L + GRW)):
        Marker1x[vertMarkerNo]=event.x
        Marker1y[vertMarkerNo]=event.y
    
    vertMarkerNo  ^= 1
    print (vertMarkerNo)
    print ( "button 1 clicked at", event.x, event.y )

def Bmarker2(event):
    global Marker2x
    global Marker2y

    Marker2x=event.x
    Marker2y=event.y
    #print ( "button 2 clicked at", event.x, event.y )

def BgetScreenshot():
    #from PIL import Image
    #import io
    path_to_screenshots = "screenshots\\"
    
    try:
        os.makedirs(path_to_screenshots)
    except FileExistsError:
        pass
    img_data = scope.display_data
    #im = Image.open(io.BytesIO(img_data))
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    file = open(path_to_screenshots + 'screen' + timestamp + '.bmp', 'wb')
    file.write(img_data)
    file.close()
    print ("Screenshot saved:" + path_to_screenshots + 'screen' + timestamp + '.bmp')


def BAutoScale():
    scope.write(":AUToscale")
    sleep(10)


def CHANNELset(event):
    global CHANNEL
    CHANNEL = cbCh.current() + 1
    setupChannel(CHANNEL)
   
    
    UpdateScreen()          # Always Update

def my_get_channel_measurement(ch,param,type="CURRent"):
    if(param == "RPM"):
        reading = scope.get_channel_measurement(CHANNEL, "FREQuency", type='CURRent')
        reading = reading * 60
    else:
        reading = scope.get_channel_measurement(CHANNEL, param, type='CURRent')
    return(reading)
    
def BParamList():
    global ParameterListChk

    noOfCols = 5
    chkBoxWidth = 10
    chkBoxHeight = 1

    ParameterLoggingSelectionFrame = LabelFrame(root, bg = COLORyellow, background=COLORlightgrey, borderwidth=10, relief=RIDGE, text="Parameter Selector",font=(60))
    ParameterLoggingSelectionFrame.place(x = 250, y = 20, width = (noOfCols * chkBoxWidth)*8 + (noOfCols * 4)*8  , height = 310)
    for checkers in range(len(ParameterListChk)):
        cRow = int(checkers / 5) + 1
        cCol =  (checkers % 5) + 0
        Checkbutton(ParameterLoggingSelectionFrame, text=ParameterList[checkers], variable=ParameterListChk[checkers],width = chkBoxWidth, height = chkBoxHeight).grid(row = cRow, column = cCol, padx=5, pady=5)
    Button(ParameterLoggingSelectionFrame, text="Close", width=chkBoxWidth, height = chkBoxHeight,command=ParameterLoggingSelectionFrame.destroy).grid(row = cRow + 2 , column = 1,  padx=5, pady=5)
    Button(ParameterLoggingSelectionFrame, text="Select All", width=chkBoxWidth, height = chkBoxHeight,command=selAllParams).grid(row=cRow + 2,column = 2, padx=5, pady=5)
    Button(ParameterLoggingSelectionFrame, text="De-Select All", width=chkBoxWidth, height = chkBoxHeight,command=deSelAllParams).grid(row= cRow + 2, column = 3, padx=5, pady=5)
    #UpdateAll()          # Always Update
    
def xxx(varv):
    print (varv)
    
    
    
def selAllParams():
    for checkers in range(len(ParameterListChk)):
        ParameterListChk[checkers].set(1)

def deSelAllParams():
    for checkers in range(len(ParameterListChk)):
        ParameterListChk[checkers].set(0)



def ChannelCouplingSet(event):
     scope.write(":CHAN" + str(CHANNEL) + ":COUP " + ChannelCouplinglist[cbChannelCoupling.current()]) 
     
def BToggleDataLogging():
    if(bL["text"] == "LOG OFF"):
        bL["text"] = "LOG ON"
    else:
        bL["text"] = "LOG OFF"

def BPopupFeaturedFrame():
    frameFeatured.place(x = 50, y = 50, width = 980  , height = 400)
                
def HideFeaturedFrame():
    #frameFeatured.grid_forget()
    frameFeatured.place_forget()
    
def BSTOREtrace():
    global STOREtrace
    global SIGNAL1
    global T2line
    
    if STOREtrace == False:
        T2line = SIGNAL1
        STOREtrace = True
    else:
        STOREtrace = False
    UpdateTrace()           # Always Update

def BSINGLEsweep():
    global SWEEPsingle
    global RUNstatus

    if (RUNstatus != 0):
        showwarning("WARNING","Stop sweep first")
        return()
    else:
        SWEEPsingle = True
        RUNstatus = 1       # we are stopped, start
    UpdateScreen()          # Always Update

def BStart():
    global RUNstatus

    if (RUNstatus == 0):
        RUNstatus = 1
    UpdateScreen()          # Always Update


def Blevel1():
    global CHANNEL
    
    scope.set_channel_scale(CHANNEL, scope.get_channel_scale(CHANNEL)/2, use_closest_match=True)

    if RUNstatus == 0:      # Update if stopped
        UpdateTrace()


def Blevel2():# Increase V/Div
    global CHANNEL
    
    scope.set_channel_scale(CHANNEL, scope.get_channel_scale(CHANNEL)*2, use_closest_match=True)

    if RUNstatus == 0:      # Update if stopped
        UpdateTrace()


def Blevel3():
    scope.timebase_scale /= 2
    if RUNstatus == 0:      # Update if stopped
        UpdateTrace()

def Blevel4():
    scope.timebase_scale *= 2

    if RUNstatus == 0:      # Update if stopped
        UpdateTrace()

def BStop():
    global RUNstatus

    if (RUNstatus == 1):
        RUNstatus = 0
    elif (RUNstatus == 2):
        RUNstatus = 3
    elif (RUNstatus == 3):
        RUNstatus = 3
    elif (RUNstatus == 4):
        RUNstatus = 3
    UpdateScreen()          # Always Update

def BReset():
   scope.write("*RST")
   sleep(10)

def BTriggerLevel():
    global triggerLevel
    global RUNstatus
    global CHANNEL
    triggerLevel = scope.query(":TRIGger:EDGe:LEVel?")
    prettyTrig = str(Quantity(triggerLevel,"V"))
    s = simpledialog.askstring("Trig","Enter New Level \n\n as a float eg 0.380 \n    or \n with units eg 380mV\n" ,initialvalue=prettyTrig)
    if (s == None):         # If Cancel pressed, then None
        return()

    try:                    # Error if for example no numeric characters or OK pressed without input (s = "")
        triggerV = Quantity(s)
        triggerVvalue = triggerV.as_tuple()[0]
    except:
        triggerVvalue = "error"
        print("Invalid Entry:" + s)

    if triggerVvalue != "error":
        triggerLevel = triggerVvalue
        vScale = float(scope.query(":CHANnel" + str(CHANNEL) + ":SCALe?"))
        vOffset = float(scope.query(":CHANnel" + str(CHANNEL) + ":OFFSet?"))
        if(  is_between(  ((-5 * vScale) - vOffset),     triggerLevel,      ((5 * vScale) - vOffset)    )  ):
            scope.write(":TRIGger:EDGe:LEVel "+str(triggerLevel))
        else:
            messagebox.showinfo("WARNING","Outside Current Valid rang of " + str((-5 * vScale) - vOffset) + " to " + str((5 * vScale) - vOffset))

    UpdateTrace()
    
def is_between(a, x, b):
    return min(a, b) < x < max(a, b)

def BShutdown():
    global shutdown
    shutdown = "yes"
    print("Shutting Down")
    scope.close()
    exit(0)

# ============================================ Main routine ====================================================

def Sweep():   # Read samples and store the data into the arrays
    global X0L          # Left top X value
    global Y0T          # Left top Y value
    global GRW          # Screenwidth
    global GRH          # Screenheight
    global VoltPerDiv
    global VoltsPeakPeak
    global TimebasePerDiv
    global YREFerence
    global XREFerence
    global YORigion
    global XORigion
    global SweepNo
    global SIGNAL1
    global RUNstatus
    global SWEEPsingle
    global SMPfftlist
    global SMPfftindex
    global SAMPLErate
    global SAMPLEsize
    global SAMPLEdepth
    global UPDATEspeed
    global triggerLevel
    global COLORred
    global COLORcanvas
    global COLORyellow
    global COLORgreen
    global COLORmagenta
    global scope
    global measFreq
    global measVMAX
    global measVMIN
    global measVTOP
    global measVBAS
    global CHANNEL

    while (True):                                           # Main loop

        # RUNstatus = 1 : Open Stream
        if (shutdown == "yes"):
            exit()
        if (RUNstatus == 1):
            TRACESopened = 1

            try:
                scope = DS1054Z('192.168.1.61')
                instrument_id = scope.idn  # ask for instrument ID
                print (instrument_id)
                # Check if instrument is set to accept LAN commands
                if instrument_id == "command error":
                    print ( instrument_id )
                    print ( "Check the powersupply settings." )
                    print ( "Utility -> IO Setting -> RemoteIO ->    be ON" )
                    sys.exit("ERROR")

                # Check if instrument is indeed a Rigol DP800 series
                id_fields = instrument_id.split(",")
                print (id_fields)
                if (id_fields[company] != "RIGOL TECHNOLOGIES") or \
                        (id_fields[model][:3] != "DS1"): 
                    print ( instrument_id )
                    print ( "ERROR: No Rigol from series DS1000 found at ", DS1054Z )
                    sys.exit("ERROR")

                print ( "Instrument ID:",instrument_id )

                setupChannel(CHANNEL)

                RUNstatus = 2
            except:                                         # If error in opening audio stream, show error
                RUNstatus = 0
                txt = "Sample rate: " + str(SAMPLErate) + ", try a lower sample rate.\nOr another audio device."
                print("VISA Error","Cannot open scope")

        # get metadata
        scope.run()
        
        VoltPerDiv = scope.get_channel_scale(CHANNEL)

        TimebasePerDiv = scope.timebase_scale
        
        VoltsPeakPeak = my_get_channel_measurement(CHANNEL, "VPP", type='CURRent')
        
        measFreq = my_get_channel_measurement(CHANNEL, "FREQ", type='CURRent')

        measVMAX = my_get_channel_measurement(CHANNEL, "VMAX", type='CURRent')

        measVMIN = my_get_channel_measurement(CHANNEL, "VMIN", type='CURRent')

        measVTOP = my_get_channel_measurement(CHANNEL, "VTOP", type='CURRent')

        measVBAS = my_get_channel_measurement(CHANNEL, "VBAS", type='CURRent')
        
        measF = my_get_channel_measurement(CHANNEL, ParameterList[cbF.current()], type='CURRent')
        
        measF = str(myQuantiphy(measF,ParameterUnitsList[cbF.current()]))
        ParameterList[cbF.current()]

        lFeaturedParameter.config(text=measF )
        
        lPopupFeaturedValue.config(text=measF )
        lPopupFeaturedParam.config(text=ParameterList[cbF.current()])
        
        cbChannelCoupling.set(scope.query(":CHAN"+str(CHANNEL) + ":COUP?"))
        
        logData()

        UpdateScreen()                                  # UpdateScreen() call

        # RUNstatus = 2: Reading audio data from soundcard
        if (RUNstatus == 2):
        # Grab the raw data from channel 1

            txt = "->Acquire"
            x = X0L + 275
            y = Y0T+GRH+32
            IDtxt  = ca.create_text (x, y, text=txt, anchor=W, fill=COLORgreen)
            root.update()       # update screen

            data_size = 0
            signals = scope.get_waveform_samples(CHANNEL, mode='RAW')
            data_size = len(signals)
            scope.run()
            
            SAMPLErate = scope.query("ACQ:SRAT?") 
            
            SAMPLErate = float(SAMPLErate)

            n = 0
            SIGNAL1 = []
            while n < len(signals):#12000 :
              SIGNAL1.append (translate((signals[n]), 4 * VoltPerDiv, -4 * VoltPerDiv, Y0T, Y0T+GRH))
              n += 1

            #UpdateAll()  #UpdateScreen()

            if SWEEPsingle == True:  # single sweep mode, sweep once then stop
                SWEEPsingle = False
                RUNstatus = 3

        # RUNstatus = 3: Stopnt
        # RUNstatus = 4: Stop and restart
        if (RUNstatus == 3) or (RUNstatus == 4):
            scope.write("KEY:FOR\n")
            sleep(0.2)
            scope.close()
            if RUNstatus == 3:
                RUNstatus = 0                               # Status is stopped
            if RUNstatus == 4:
                RUNstatus = 1                               # Status is (re)start
            UpdateScreen()                                  # UpdateScreen() call

        # Update tasks and screens by TKinter
        root.update_idletasks()
        root.update()                                       # update screens

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def logData():
    global filename
    global startLogTime
    global nextLogTime
    path_to_log = "captures\\"
    file_format = "csv"
    
    try:
        os.makedirs(path_to_log)
    except FileExistsError:
        pass

    if (bL["text"] =="LOG ON"):
        if(filename ==""):
            startLogTime = time.time()
            nextLogTime = startLogTime
            
            # Prepare filename as C:\MODEL_SERIAL_YYYY-MM-DD_HH.MM.SS
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = path_to_log  + timestamp

            NoOfParamsToLog = 0
            header = b"Timestamp" 
            
            for checkers in range(len(ParameterListChk)):
                if(ParameterListChk[checkers].get()):
                    header += ",".encode("utf-8") + ParameterList[checkers].encode("utf-8")
                    NoOfParamsToLog += 1
            header += "\n".encode("utf-8")
            if (NoOfParamsToLog == 0):
                messagebox.showinfo("No Params have been selected", "Use 'Sel Log Params' to select some values to Log")
                bL["text"] = "LOG OFF"
                return()

            file = open(filename +  "." + file_format, "ab")
            file.write(header) 
            file.close
        
        if (time.time() > nextLogTime ):
            nextLogTime += 10
            readings = b""
            readings += str(time.time() - startLogTime).encode("utf-8")
            for checkers in range(len(ParameterListChk)):
                if(ParameterListChk[checkers].get()):
                    reading = my_get_channel_measurement(CHANNEL, ParameterList[checkers], type='CURRent')
                    
                    readings += ",".encode("utf-8") + str(reading).encode("utf-8")
            readings += "\n".encode("utf-8")
            file = open(filename +  "." + file_format, "ab")
            print (readings)
            file.write(readings)
            file.close
    else:
        filename = ""

def setupChannel(CHANNEL):
    scope.run()
    scope.display_only_channel(CHANNEL)

    scope.write(":TRIGger:EDGe:SOURce CHANnel" + str(CHANNEL))

    cbChannelCoupling.set(scope.query(":CHAN" + str(CHANNEL) + ":COUP?")) 

    scope.set_channel_offset(CHANNEL, 0)

    scope.write(":WAV:SOUR CHAN" + str(CHANNEL) + " \n")

    scope.set_waveform_mode(mode='RAW')

    scope.set_waveform_mode(mode='BYTE')

    scope.memory_depth = 12000 # normal memory type

    scope.write(":WAV:STAR 1")
    scope.write(":WAV:STOP 12000")

def myQuantiphy(value,unit):
    if(value is None):
        return ("---")
    if(unit == "%"):
        return (str(value * 100) + "%")
    return Quantity(value,unit)

def UpdateTrace():      # Update trace and screen
    UpdateScreen()      # Update the screen


def UpdateScreen():     # Update screen with trace and text
    MakeScreen()        # Update the screen
    root.update()       # Activate updated screens


def MakeScreen():       # Update the screen with traces and text
    global VoltPerDiv
    global VoltsPeakPeak
    global TimebasePerDiv
    global SweepNo
    global measFreq
    global measVMAX
    global measVMIN
    global measVTOP
    global measVBAS
    global SIGNAL1
    global X0L          # Left top X value
    global Y0T          # Left top Y value
    global GRW          # Screenwidth
    global GRH          # Screenheight
    global T1line
    global T2line
    global STOREtrace
    global Vdiv         # Number of vertical divisions
    global RUNstatus    # 0 stopped, 1 start, 2 running, 3 stop now, 4 stop and restart
    global SAMPLEdepth  # 0 norm, 1 long
    global triggerLevel
    global SAMPLErate
    global SAMPLEsize
    global SIGNALlevel   # Level of signal input 0 to 1
    global COLORgrid    # The colors
    global COLORtrace1
    global COLORtrace2
    global COLORtext
    global COLORsignalband
    global COLORaudiobar
    global COLORaudiook
    global COLORaudiomax
    global CANVASwidth
    global CANVASheight


    SweepNo += 1
    # Delete all items on the screen
    ca.delete('all')

    # Draw horizontal grid lines
    i = 0
    x1 = X0L
    x2 = X0L + GRW
    x3 = x1+2     # db labels X location
    VPD = float(VoltPerDiv)
    VoltsDiv = VPD * 4
    while (i <= Vdiv):
        y = Y0T + i * GRH/Vdiv
        Dline = [x1,y,x2,y]
        ca.create_line(Dline, fill=COLORgrid)
        txt = str("{0:.2f}".format(VoltsDiv))+"V"#VoltPerDiv#) #str(db) # db labels
        idTXT = ca.create_text (x3, y-5, text=txt, anchor=W, fill=COLORtext)
        VoltsDiv =  VoltsDiv - VPD
        i = i + 1

    # Draw vertical grid lines
    i = 0
    y1 = Y0T
    y2 = Y0T + GRH
    SPD = float(TimebasePerDiv)
    TimeDiv = 0
    while (i < 11):
        x = X0L + i * GRW/10
        Dline = [x,y1,x,y2]
        ca.create_line(Dline, fill=COLORgrid)
        txt = str(myQuantiphy(TimeDiv,'S'))#str("{0:.6f}".format(TimeDiv))#SecPerDiv#str(freq/1000000) # freq labels in mhz
        idTXT = ca.create_text (x-10, y2+10, text=txt, anchor=W, fill=COLORtext)
        TimeDiv = TimeDiv + SPD
        i = i + 1
        
    # Draw traces
    if len(SIGNAL1) > 4: 
    # Avoid writing lines with 1 coordinate
        n = 0
        xpos = 20
        tt = []
        while n < 12000:#4098:#1024:
          tt.append(xpos)
          tt.append(SIGNAL1[n])
          n +=  1
          if (n % 12) == 0:
            xpos += 1
          #ca.create_line(T1line, fill=COLORtrace1)            # Write the trace 1
        ca.create_line(tt, fill=COLORtrace1)            # Write the trace 1
        #ca.create_line(SIGNAL1, fill=COLORtrace1)            # Write the trace 1
    if STOREtrace == True and len(T2line) > 4:              # Write the trace 2 if active
        n = 0
        ss = []
        xpos = 20
        while n < 12000:#4098:#1024:
          ss.append(xpos)
          ss.append(T2line[n])
          #print ( SIGNAL1[n] )
          n = n + 1#2
          #xpos += 1
          if (n % 12) == 0:
            xpos += 1
        ca.create_line(ss, fill=COLORtrace2)            # and avoid writing lines with 1 coordinate
 
    txt = "             Sample rate: " + str(SAMPLErate/1000000) +" MHz"
 
    if(len(SIGNAL1) != 0):
        Marker1yy0 = SIGNAL1[(Marker1x[0]-X0L)*12   ]
        Marker1yy1 = SIGNAL1[(Marker1x[1]-X0L)*12   ]
        ca.create_polygon([Marker1x[0],Marker1yy0-3,Marker1x[0]-3,Marker1yy0-15,Marker1x[0]+3,Marker1yy0-15], outline=COLORMarker1, fill=COLORMarker1, width=1)
        ca.create_polygon([Marker1x[1],Marker1yy1-3,Marker1x[1]-3,Marker1yy1-15,Marker1x[1]+3,Marker1yy1-15], outline=COLORMarker1, fill=COLORMarker1, width=1)
        txt = txt + "    Vert Cursor0:(" + str(Marker1x[0]) + "," + str(Marker1yy0) + ")"  
    #ca.create_line(Marker1x,GRWN,Marker1x,Y0T + GRH,fill=COLORMarker1)

    # General information on top of the grid

    x = X0L
    y = 12
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

    # Start and stop frequency and dB/div and trace mode
    txt = "Sweep No: " + str(SweepNo)
    txt = txt +  "    " + str(VoltPerDiv) + " V/div"
    txt = txt + "    Vpp: " + str(myQuantiphy(VoltsPeakPeak,'V')) 
    txt = txt + "     " + str(myQuantiphy(TimebasePerDiv,'S')) + "/div "

    x = X0L +500
    y = Y0T+GRH+32
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

    x = X0L +500
    y = Y0T+GRH+45
    txt = "Freq: " + str(myQuantiphy(measFreq,'Hz'))
    txt = txt + "    VMAX:" + str(myQuantiphy(measVMAX,'V')) 
    txt = txt + "    VMIN: " +  str(myQuantiphy(measVMIN,'V')) 
    txt = txt + "    VTOP:" +  str(myQuantiphy(measVTOP,'V')) 
    txt = txt + "    VBAS: " +  str(myQuantiphy(measVBAS,'V')) 
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)


    # Soundcard level bargraph
    txt1 = "||||||||||||||||||||"   # Bargraph
    le = len(txt1)                  # length of bargraph

    SIGNALlevel = 5
    t = int(math.sqrt(SIGNALlevel) * le)

    n = 0
    txt = ""
    while(n < t and n < le):
        txt = txt + "|"
        n = n + 1

    x = X0L
    y = Y0T+GRH+32

    IDtxt = ca.create_text (x, y, text=txt1, anchor=W, fill=COLORaudiobar)

    if SIGNALlevel >= 1.0:
        IDtxt = ca.create_text (x, y, text=txt, anchor=W, fill=COLORaudiomax)
    else:
        IDtxt = ca.create_text (x, y, text=txt, anchor=W, fill=COLORaudiook)


    # Runstatus and level information
    txt = "Run Status:" + str(RUNstatus)

    if (RUNstatus == 0) or (RUNstatus == 3):
        txt = txt + " Sweep stopped"
    else:
        txt = txt + " Sweep running"

    x = X0L + 100
    y = Y0T+GRH+32
    IDtxt  = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

# show the values at the mouse cursor
# note the magic numbers below were determined by looking at the cursor values
# not sure why they don't correspond to X0T and Y0T
    VPD = float(VoltPerDiv)
    VoltsDivOffset = VPD * 4
    #VoltsDiv =  VoltsDiv - VPD
    
    cursorx = ((root.winfo_pointerx()-root.winfo_rootx()-X0L-4)*10 )*float(TimebasePerDiv)/GRWN
    cursory = ((root.winfo_pointery()-root.winfo_rooty()-Y0T-50)*float(VoltPerDiv)*(-8)/GRH)+VoltsDivOffset
    cursorx = ("{0:.4f}".format(cursorx))
    txt = "Cursor " + str(Quantity(cursorx,"s"))   + "  " +  str(Quantity(cursory,"V")) 

    x = X0L+800
    y = 12
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)
    ca.create_line(Marker1x[0],Y0T,Marker1x[0],GRHN+Y0T,fill=COLORMarker1)
    ca.create_line(Marker1x[1],Y0T,Marker1x[1],GRHN+Y0T,fill=COLORMarker1)
    

# ================ Make Screen ==========================

root=Tk()

ParameterListChk = []
for i in range(len (ParameterList)):
    ParameterListChk.append(IntVar())

root.title("Rigol Trace Viewer Nov 2023 JPR")

root.minsize(100, 100)

frame1 = Frame(root, background=COLORframes, borderwidth=5, relief=RIDGE)
frame1.pack(side=TOP, expand=1, fill=X)

frame2 = Frame(root, background="black", borderwidth=5, relief=RIDGE)
frame2.pack(side=TOP, expand=1, fill=X)

frame3 = Frame(root, background=COLORframes, borderwidth=5, relief=RIDGE)
frame3.pack(side=TOP, expand=1, fill=X)

frameFeatured = LabelFrame(root, background=COLORlightgrey, borderwidth=5, relief=RIDGE, text="Featured Parameter",font=(60))

ca = Canvas(frame2, width=CANVASwidth, height=CANVASheight, background=COLORcanvas)
ca.bind("<Button-1>", Bmarker1)
ca.bind("<Button-3>", Bmarker2)
ca.pack(side=TOP)
ca.config(cursor="crosshair")

b = Button(frame1, text="Screenshot", width=Buttonwidth1, command=BgetScreenshot)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame1, text="Auto Scale", width=Buttonwidth1, command=BAutoScale)
b.pack(side=LEFT, padx=5, pady=5)

cbCh = ttk.Combobox(frame1, values=ChannelList,  width=Buttonwidth1)
cbCh.set(ChannelList[CHANNEL-1])
cbCh.pack(side=LEFT, padx=5, pady=5)
cbCh.bind("<<ComboboxSelected>>", CHANNELset)

b = Button(frame1, text="Sel Log Params", width=Buttonwidth1, command=BParamList)
b.pack(side=LEFT, padx=5, pady=5)

bL = Button(frame1, text="LOG OFF", width=Buttonwidth1, command=BToggleDataLogging)
bL.pack(side=LEFT, padx=5, pady=5)

cbChannelCoupling = ttk.Combobox(frame1, values=ChannelCouplinglist,  width=Buttonwidth1)
cbChannelCoupling.pack(side=LEFT, padx=5, pady=5)
cbChannelCoupling.bind("<<ComboboxSelected>>", ChannelCouplingSet)

cbF = ttk.Combobox(frame1, values=ParameterList,  width=Buttonwidth1)
cbF.set(ParameterList[7])
cbF.pack(side=LEFT, padx=5, pady=5)

lFeaturedParameter = Label(frame1, text="0", width=Buttonwidth1)
lFeaturedParameter.pack(side=LEFT, padx=5, pady=5)

b = Button(frame1, text="Popup Feat", width=Buttonwidth1, command=BPopupFeaturedFrame)
b.pack(side=LEFT, padx=5, pady=5)

lPopupFeaturedParam = Label(frameFeatured, text="000000", width=Buttonwidth1)#.grid(row = 1 , column = 1,  padx=5, pady=5)
lPopupFeaturedParam.config(font =("Courier", 84))
lPopupFeaturedParam.grid(row = 1 , columnspan = 5,  padx=5, pady=5)

lPopupFeaturedValue = Label(frameFeatured, text="000000", width=Buttonwidth1)#.grid(row = 1 , column = 1,  padx=5, pady=5)
lPopupFeaturedValue.config(font = ("none", 100))
lPopupFeaturedValue.grid(row = 2 , columnspan = 5,  padx=5, pady=5)

Button(frameFeatured, text="Close", width=Buttonwidth1, command=HideFeaturedFrame).grid(row = 8 , columnspan = 5,  padx=5, pady=5)

b = Button(frame1, text="Store trace", width=Buttonwidth1, command=BSTOREtrace)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="Start", width=Buttonwidth2, command=BStart)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="Stop", width=Buttonwidth2, command=BStop)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="Single", width=Buttonwidth1, command=BSINGLEsweep)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="Trigger", width=Buttonwidth2, command=BTriggerLevel)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="Shutdown", width=Buttonwidth2, command=BShutdown)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="RESET Scope", width=Buttonwidth1, command=BReset)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="s/div*2", width=Buttonwidth2, command=Blevel4)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="s/div/2", width=Buttonwidth2, command=Blevel3)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="V/div+", width=Buttonwidth2, command=Blevel2)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="V/div-", width=Buttonwidth2, command=Blevel1)
b.pack(side=RIGHT, padx=5, pady=5)

# ================ Call main routine ===============================
root.update()               # Activate updated screens
Sweep()