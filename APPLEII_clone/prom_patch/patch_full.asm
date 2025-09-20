;
; use APPLE ][ compatible location
;
KBD             EQ     $C000           ;PIA.A keyboard input
KBDCR           EQ     $C010           ;PIA.A keyboard control register
DSP             EQ     $C001           ;PIA.B display output register
DSPCR           EQ     $C011           ;PIA.B display control register


;
; prom hacked routines
;
INIT		EQ	$FB2F
KEYIN		EQ	$FD1B
;
; page 0 location
;	
;
;       monitor routines
;
REGDSP  =       $FADA
PRBYTE  =       $FDDA
PRNTXY  =       $F940
NXTA1   =       $FCBA
PRA1    =       $FD92
COUT    =       $FDED
CROUT   =       $FD8E
YSAV    =       $34
A1L     =       $3C
A1H     =       $3D
TMP     =       $30
YSAV1		EQ	$35
;
;-----------------------------
; 'free' zone (read write to 
; tape origin routines
; FECD..FEF5
; FEFD..FF2A
; FCC9..FD0B
;----------------------------
;
; define safeguard
;
	*=$FCC9
;-----------------------------
;  PIA Init Sequence
;-----------------------------
INITPIA LDY     #%01111111     	;Mask for DSP data direction reg
        STY     DSP            	; (DDR mode is assumed after reset)
        LDA     #%10100111     	;KBD and DSP control register mask
        STA     KBDCR          	;Enable interrupts, set CA1, CB1 for
        STA     DSPCR          	; positive edge sense/output mode.
	JMP	INIT		; resume init
ECHO    BIT     DSP
        BMI     ECHO
ECHO1   STA     DSP             ; output char
        BIT     DSP             ; test output OK
        BPL     ECHO1           ; no resend char
	LDY	YSAV1
	RTS	
READBYTE
        JSR     RNIBBLE
        CLC
        ASL
        ASL
        ASL
        ASL
        STA     (A1L,X)
        STA     TMP
        JSR     KEYIN
        JSR     RNIBBLE
        ORA     (A1L,X)
        STA     (A1L,X)
        RTS 

;-----------------------------
;  Hack init sequence
;-----------------------------
	*=$FF5C
	JSR	INITPIA
	
;-----------------------------
;  Hack COUT1 sequence
;-----------------------------
	*=$FDFD
	JMP	ECHO
	
; replace original KEYIN2 routine
        *=$FD21
KEYIN2  LDA     KBDCR
        BPL     KEYIN
	*=$FD28
	LDA	KBD
        RTS

        *=$FECD
WRITE:
        LDA     #$40
        JSR     HEAD
        LDY     #$27
WR1     LDX     #$00
        LDA     (A1L,X)
        JSR     PRBYTE
        JSR     NXTA1
        BCC     WR1
	RTS
RNIBBLE
        EOR     #$B0            ; check digit
        CMP     #10
        BCC     DIG
        ADC     #$88
DIG     AND     #$0F            ; get value
        RTS
	*=$FEFD
READ    JSR     KEYIN           ; wait for preambule start
        CMP     #"*"+$80
        BNE     READ
READ1   JSR     KEYIN           ; wait for preambule stop
        CMP     #"*"+$80
        BEQ     READ1
        LDX     #$00
READ2   JSR     READBYTE
        JSR     NXTA1
        BCS     READ3
        JSR     KEYIN
        BNE     READ2
READ3   RTS
HEAD:
        ROR
        ROR
        ROR
        AND     #$0F
        TAY
        LDA     #"*"
HEAD1   JSR     COUT
        DEY
        BNE     HEAD1
        RTS

