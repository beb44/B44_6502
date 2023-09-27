const byte KEYINT = 2;
const byte DISPINT = 3;
//------------------------
// Keyboard driver section
//------------------------
//
// physical pin definition
const byte DATA_OUT   = 4;
const byte CLOCK_OUT  = 5;
const byte STROBE_OUT = 6;
//
// internal buffer definition
//
#define KEYBBUFLEN 128
char keybBuf[KEYBBUFLEN];
byte keybBufReadP;
byte keybBufWriteP;
byte keybBufLen;
bool keybRegFree;

//----------------------  -
// display driver section
//-----------------------
//
// physical pin definition
//
const byte DATA_IN    = 7;   // ATmega328P PD7
const byte CLOCK_IN   = 8;   // ATmega328P PB0
const byte LATCH_IN   = 9;   // ATmega328P PB1
const byte KEYSTROBE  = 10;  // ATmega328P PB2
const byte DISP_READY = 11;  // ATmega328P PB3

char  inchar;




// int detection variables
int keyIntCount;       // last Key interrupt detected
int dispIntCount;      // last Disp interrupt detected
int keyIntHandled;     // last Key interrupt treated
int dispIntHandled;    // last Disp interrupt treated

void setup() {
  keyIntCount    = 0;
  dispIntCount   = 0;
  keyIntHandled  = 0;
  dispIntHandled = 0;
  
  // attach inteerupt pin on rising edge
  pinMode(KEYINT, INPUT);
  attachInterrupt(digitalPinToInterrupt(KEYINT), keyint, FALLING);

  pinMode(DISPINT, INPUT);
  attachInterrupt(digitalPinToInterrupt(DISPINT),dispint, FALLING);

  
  // Keyboard data register control
  digitalWrite(DATA_OUT,LOW);
  digitalWrite(CLOCK_OUT,HIGH);
  digitalWrite(STROBE_OUT,HIGH);
  pinMode(CLOCK_OUT,OUTPUT);
  pinMode(DATA_OUT,OUTPUT);
  pinMode(STROBE_OUT,OUTPUT);

  // no character available
  // keyboard buffer variable
  keybBufLen = 0;
  keybBufReadP = 0;
  keybBufWriteP = 0;
  keybRegFree = true;

  // display section
  pinMode(DATA_IN,INPUT);
  digitalWrite(CLOCK_IN,LOW);
  digitalWrite(LATCH_IN,HIGH); // make sure incorrect data are not latched
  pinMode(CLOCK_IN,OUTPUT);
  pinMode(LATCH_IN,OUTPUT);
  
  digitalWrite(DISP_READY,LOW);
  pinMode(DISP_READY,OUTPUT);

  digitalWrite(KEYSTROBE,LOW);
  pinMode(KEYSTROBE,OUTPUT);

  // initialise serial port
  Serial.begin(9600);
  Serial.println("Session started");
}

void dispint()
{
  // register incomming interrupt only
  // all treatement will be done in the
  // background task
  dispIntCount++;
}

void keyint()
{
  // register incomming interrupt only
  // all treatement will be done in the
  // background task
  //Serial.println("KEYINT");
  keyIntCount++;
}

//
// get display character
// use direct part acces to speed up process
//
char dataIn()
{
  // latch data bus content in
  digitalWrite(LATCH_IN,LOW);  //D9//PB1;    // allow parallel latch
  digitalWrite(CLOCK_IN,HIGH);  //D8/PB0;   // generate a Rising pulse
  digitalWrite(CLOCK_IN,LOW);  //D8/PB0;
  digitalWrite(LATCH_IN,HIGH); //D9/PB1
  // retreive the 8 data bits
  for (byte count=0;count<8;count++)
  {
    inchar = (inchar<<1)+((digitalRead(DATA_IN)==HIGH)?1:0);
    digitalWrite(CLOCK_IN,HIGH);//D7//PD7
    digitalWrite(CLOCK_IN,LOW);//D7//PD7
  }
  return (char)(inchar &0x7F);
}

//
// send data to the keyboard port
//
void dataOut(byte output_val)
{
  //Serial.print("DataOut ");
  //Serial.println(output_val,HEX);
  output_val |= 0x80;
  digitalWrite(STROBE_OUT,LOW);

  digitalWrite(CLOCK_OUT,LOW);
  shiftOut(DATA_OUT,CLOCK_OUT,MSBFIRST,output_val|0x80);

  digitalWrite(STROBE_OUT,HIGH);

  // generate keyboard strobe
  digitalWrite(KEYSTROBE,HIGH);
  delayMicroseconds(100);
  digitalWrite(KEYSTROBE,LOW);
   
}

//
// check incoming characters
//
void checkKeybIn()
{
  if (Serial.available() == true)
  {
    char c = Serial.read();
    if (keybRegFree)
  //if (true)
    {
      // no character in the queue, output it
      // directly
      dataOut(c);
      keybRegFree = false;
    }
    else
    {
      // already one char in the 4094 chip, add it to the queue
      if (keybBufLen < KEYBBUFLEN) 
      {
        //Serial.println("QUEUE CHAR");
        keybBuf[keybBufWriteP] = c;
        keybBufWriteP = (++keybBufWriteP & (KEYBBUFLEN-1)); 
        keybBufLen++;
      }
    } 
  }
  
}

//
// background task
//
void loop() {
  checkKeybIn();
  if (keyIntCount != keyIntHandled)
  {
    //Serial.println("dequeue");
    // keyboard read interruption detected
    keyIntHandled++;  // acknowledge interrupt
    if (keybBufLen != 0)
    {
      // a character is available
      // latch it in the 4094 chip
      dataOut(keybBuf[keybBufReadP++] );
      // check wrap around
      if (keybBufReadP == KEYBBUFLEN) keybBufReadP = 0;
      keybBufLen--;
      if (keybBufLen == 0) keybRegFree = true;
    }
    else
    {
      // indicate the buffer is empty
      keybRegFree = true;
    }
  }  
  if (dispIntCount != dispIntHandled)
  {
    
    char c =  dataIn();
    if (c == '\r')
    {
      Serial.println("");
      
    }
    else 
      Serial.print(c);
    Serial.flush();
    // make display ready
    // generate RDA
    digitalWrite(DISP_READY,LOW);
    delayMicroseconds(3);
    digitalWrite(DISP_READY,HIGH);
    delayMicroseconds(3);
    digitalWrite(DISP_READY,LOW);
    
    dispIntHandled++;  // acknowledge interrupt
  }
}
