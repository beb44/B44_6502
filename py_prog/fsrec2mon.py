import sys,serial
import argparse
import time

##
## parse input line
##
## -fn <filename> is the file where data are read
##                or write
## -dev <dev>     is the USB port connected to serial
##                interface
## -w             selects reception mode (SAVE from
##                Apple II perspective
## -s <addr>      start address
## -t <addr>      end address
def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument('-fn',action='store',default=None)
  parser.add_argument('-dev',action='store',default='/dev/ttyUSB0')
  args = parser.parse_args()
  return [args.fn,args.dev];

def getSTST(fi):
  n = fi.readline()
  if (n[1] == "0"):
    print "Begining of section found"
  n = fi.readline()
  print "len ",n[2:4]
  print "addr ",n[4:8]
  start = n[4:8]
  SS = "****"
  while (n[1]=="1"):
    l =n[2:4]
    SS = SS+  n[8:8+(int(l,16)-3)*2]
    stop = n[4:8]
    n = fi.readline()
  return [int(start,16),int(stop,16)+int(l,16)-4,SS]
def putFile(fn):
  print fn
  try:
    fi = open(fn,"r")
  except:
    print "Unable to open "+fn+" in write mode"
    return -1
  start,stop,SS = getSTST(fi)
  return hex(start)[2:],hex(stop)[2:],SS

if (__name__=="__main__"):
  fn,dev  =  parse()
  ##
  ## open device
  ##
  try:
    ser =serial.Serial(dev,9600);
  except:
    print "unable to open device "+dev
    exit(0)

  ##
  ## open device
  ##
  start,stop,ss = putFile(fn)
  
  ser.write(start+"."+stop+"r\n\r")
  ser.write(ss)


