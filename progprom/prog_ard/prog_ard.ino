// les 8 leds sont connectées aux port D5 a D12
// soit respectivement les ports PD5 à PD8
// puis les ports PB0 à PB4

#define portd_mask  0b11100000
#define portb_mask  0b00011111

// Port D2 -> data D3 -> clock D4 -> strobe
#define data_mask   0b00000100
#define clock_mask  0b00001000
#define strobe_mask 0b00010000
// short commands
#define delay125ns      {asm volatile("nop"); asm volatile("nop");}
#define toggleclk       { PORTD |= clock_mask;PORTD &= ~clock_mask;}
#define strboff         {PORTD &= ~strobe_mask;}
#define strbon          {PORTD |= strobe_mask; }
#define databusRead     {DDRB &= ~portb_mask; DDRD &= ~portd_mask;}
#define databusWrite    {DDRB |= portb_mask;  DDRD |= portd_mask;}
#define RWB    13
byte  OE = HIGH;
byte lastData = 0xFF;
// Identifiers
#define VERSION         "1.1"
#define IDENT           "EEPROM Programmer"

//  interface section
char buff[100];    // reception buffer
char *cptr;        // current char


void setup() {
  // set databus in read mode
  databusRead;
  // set 4094 port as outout
  DDRD = (data_mask | clock_mask | strobe_mask); 
  // set R/W as output port
  digitalWrite(RWB,HIGH);
  pinMode(RWB,OUTPUT);  
  Serial.begin(9600);
}

void setData(byte value)
{
  PORTD = (PORTD & ~portd_mask) | (value << 5 );
  PORTB = (PORTB & ~portb_mask) | (value >> 3);
}

byte getData()
{
  return (PIND >> 5) | (PINB << 3);
}

void setAddr(unsigned int Addr,int OE)

{
  Addr = (OE==HIGH?(Addr | 0x8000):(Addr & 0x7FFF));
  strboff;
  // shift data MSB first
  for (int i=0;i<16;i++)
  {
    if (Addr & 0x8000)
      PORTD |= data_mask;
    else
      PORTD &= ~data_mask;
    toggleclk;
    Addr = Addr << 1;     
  }
  strbon;
}

void writeData(unsigned int Addr,byte val)
{
  setAddr(Addr,HIGH);  // disable OUTPUT
  setData(val);
  databusWrite;
  delayMicroseconds(5); // wait effective data output disable
  digitalWrite(RWB,LOW); // set RWB to low to trigger write
  delayMicroseconds(2);  // Let the chip copy
  digitalWrite(RWB,HIGH);// Perform write
  delay(1); // rest time
}

byte readData(unsigned int Addr)
{
  databusRead;
  setAddr(Addr,LOW); // enable OUTPUT
  delay(1);          // wait for output to stabalise
  return getData();
}

byte asciiToHex(char c)
{
  return ((c<='9')?(byte)(c-'0'):(byte)(c-'A'+10));
}
byte getByte(char *buff)
{
  byte val;
  val = asciiToHex(*buff);
  buff++;
  val = (val << 4)+asciiToHex(*buff);
  return val;
}

char hexToAscii(byte val)
{
  return (val<=9?'0'+val:'A'+val-10);
}
void setByte(char *buff,byte val)
{
  *buff++ = hexToAscii(val>>4);
  *buff   = hexToAscii(val &0x0f);
}

void processWrite(char *buff)
{
byte data;

  buff++;   // skip to next chartacter
  
  if (*buff == '9')
  {
    return;
  }
  
  if (*buff != '1')
  {
    Serial.println("Only S18 format allowed");
    return;
  }
  buff++;
  byte len = getByte(buff);  // get record len
  byte checksum = 0;
  buff += 2;
  byte lenH = getByte(buff); // get address MSB
  checksum += lenH;
  buff += 2;
  byte lenL = getByte(buff); // get address LSB
  checksum += lenL;
  buff += 2;
  
  unsigned int Addr = (lenH<<8)+lenL;
  byte nbbytes = len-3;
  for (int i=0;i<nbbytes;i++)
  {
    data = getByte(buff);
    writeData(Addr,data);
    checksum += data;
    buff += 2;
    Addr++;   
  }
  checksum += getByte(buff);
}
void processRead(char *buff)
{
byte data;

  buff++;   // skip to next chartacter
  if (*buff != '1')
  {
    Serial.println("Only S18 format allowed");
    return;
  }
  buff++;
  byte len = getByte(buff);  // get record len
  byte checksum = 0;
  buff += 2;
  byte lenH = getByte(buff); // get address MSB
  checksum += lenH;
  buff += 2;
  byte lenL = getByte(buff); // get address LSB
  checksum += lenL;
  buff += 2;
  
  unsigned int Addr = (lenH<<8)+lenL;
  byte nbbytes = len-3;
  for (int i=0;i<nbbytes;i++)
  {
    data = readData(Addr);
    setByte(buff,data);
    checksum += data;
    buff += 2;
    Addr++;   
  }
  *buff = 0;
    
}
void processCommand(char *buff)
{
  switch (*buff)
  {
    case 'S' : processWrite(buff); break;
    case 'R' : processRead(buff); Serial.println(buff); break;
    case 'I' : Serial.println(IDENT); break;
    case 'V' : Serial.println(VERSION); break;
    default:   break;
  }
}
void loop() {
  Serial.print(">");  // send prompt (ready to get next command)
  cptr =buff;
  while (true)
  {
    if (Serial.available() > 0)
    {
      *cptr = Serial.read();
      if (*cptr == 0xd) break;
      if (*cptr == 0) break;
      cptr++;
    }  
  }
  *++cptr='\0';
  // interpet received command
  processCommand(buff);
}
void loop_test() 
{
  // put your main code here, to run repeatedly:
  for (unsigned int i=0;i<=0x7FFF;i++)
  {
    writeData(i,(i&0xff));
    if (readData(i) != (i& 0xff))
    {
      Serial.print("Write or read error addr=");
      Serial.print(i,HEX);
      Serial.print(" expected value=");
      Serial.print((i&0xff),HEX);
      Serial.print(" Effective value=");
      Serial.println(readData(i));
      delay(10000);   // wait 10 seconds before next operation
    }
    else
    {
      Serial.print("Operation at address ");
      Serial.print(i,HEX);
      Serial.println(" OK");
    }
  }  
}
