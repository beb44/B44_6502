import argparse
##
## parse argument
##
def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument('-fn',action='store',default=None)
  parser.add_argument('-dev',action='store',default='/dev/ttyUSB0')
  parser.add_argument('-b',action='store',default=0)
  args = parser.parse_args()
  return [args.fn,args.dev,args.b]


##
## hexadecimal conversion routines
##
def FNib(c):
  if (c<10):
    return chr(ord('0')+c)
  else:
    return chr(ord('A')+(c-10))
    
def Fbyte(c):
  return FNib(ord(c)/16)+FNib(ord(c)%16)

##
## main program
##  
if (__name__ == "__main__"):
  fn,de,base = parse()
  if (fn == None):
    print "No filename specified"
    exit(0)
  try:     
    fi = open(fn,'rb')
  except:
    print "Unable to open"+fn
    exit(0)
    
    
  rstr = "S000"
  Addr = int(base,0)  
  for n in fi.read():
    if ((Addr%16) == 0):
      print rstr+"00"
      rstr="S113"+Fbyte(chr(Addr/256))+Fbyte(chr(Addr%256))+Fbyte(n)
    else:
      rstr =rstr+Fbyte(n)  
    Addr+=1  
  print rstr+"00"  
