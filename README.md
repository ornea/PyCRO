# PyCRO
Rigol ds1054z traceviewer. Python3 W10 using the ds1054z py package based on https://github.com/rheslip/PyDSA using TCP/IP

Inspiration: I wanted to view RPM of various machines in the workshop.  Instead of buying RPM meter I used line following sensor 
    connected to scope via long flying lead and black and white tape on the spinning part to detect rotation.
    Initial tests worked but I could not see the frequency and I had to continually convert to RPM.

Features :
1. Screenshot save
2. Autoscale
3. Channel Select
4. RESET
5. Log selected parameter to file
6. Adjust Timebase
7. Adjust Vertical scale
8. Select Coupling
9. Large display popup for a featured paramteter See Below.
To Do:

1. continue implementing verticle and horizontal cursors that provide useful measurements

There appears to be many python based ds1054z apps but most were tested on linux.  This offering was developed on W10

Main window looks like this
![image](https://github.com/ornea/PyCRO/assets/15388230/cd69f031-4088-4964-addd-24543ee86608)

and Parameter select frame for logging looks like this

![image](https://github.com/ornea/PyCRO/assets/15388230/9259286b-5bd1-41a7-b192-46781ea63ab5)

and Featured Parameter Popup Window looks like this (useful when viewing from across the workshop)

![image](https://github.com/ornea/PyCRO/assets/15388230/9b0d0d41-7d5e-4fe2-8fb3-d39b597beb6b)


I needed a remote viewer and logger so took Rich Heslip VE3MKC PDSA code and badly butchered it.  I am not familiar with licenses but his blog stated 
![image](https://github.com/ornea/PyCRO/assets/15388230/fdde96d4-5cc6-406a-9990-3d14dbd92d9b)
