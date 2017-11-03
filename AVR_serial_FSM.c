// MOTOR SETP CONTROL
// future:
// update the STOP state to let inductive current flow
#define STEPS 10
#define PINS 10
#define BUAD 2000000
uint8_t pow2i(uint8_t exponent){
    uint8_t out=1;
    for (size_t i = 0; i < exponent; i++) {
        out*=2;
    }
    return out;
}




const int pin[PINS] = { 2, 3, 4, 5, 6, 8, 9, 11, 12, 13}; //set output pin
int order[STEPS][PINS] = {{1, 0, 0, 0, 0, 0, 0, 1, 1, 0}, //step 0
                          {1, 1, 0, 0, 0, 0, 0, 0, 1, 0}, //step 1
                          {0, 1, 0, 0, 0, 0, 0, 0, 1, 1}, //step 2
                          {0, 1, 1, 0, 0, 0, 0, 0, 0, 1}, //step 3
                          {0, 0, 1, 0, 0, 1, 0, 0, 0, 1}, //step 4
                          {0, 0, 1, 1, 0, 1, 0, 0, 0, 0}, //step 5
                          {0, 0, 0, 1, 0, 1, 1, 0, 0, 0}, //step 6
                          {0, 0, 0, 1, 1, 0, 1, 0, 0, 0}, //step 7
                          {0, 0, 0, 0, 1, 0, 1, 1, 0, 0}, //step 8
                          {1, 0, 0, 0, 1, 0, 0, 1, 0, 0}  //step 9
                           };//full step excitation seqience
//PORT REGISTERS
typedef struct DIGITAL_PORT{
        uint8_t DATA_DIRECTION; // for configuring output pins of all steps
        uint8_t DATA[STEPS];    // for storing register state of each step converted from 'order'
    } PORT;
PORT OUTPORTB={0},OUTPORTD={0};
//==========================================================================
//time, rotation control
//unsigned long dtime, timer;
byte STATE;
byte rotation = 0;
#define FORWORD B11111111;  // +-- prev: const byte FORWORD = B11111111
#define BACKWARD B00000000; // |
#define READY B00000000;    // |
#define STOP B01010101;     // +
//=============


void setup() {
  Serial.begin(BUAD);
  //=========================== configure output pins from pin array
  for (size_t i = 0; i < PINS; i++) {
      if (pin[i] >= 0 && pin[i] <= 7) { //OUTPORTD
          OUTPORTD.DATA_DIRECTION |= pow2i(pin[i]);

      }else if (pin[i] >= 8 && pin[i] <= 13) { // OUTPORTB
          OUTPORTB.DATA_DIRECTION |= pow2i(pin[i]-8);

      }else{
          Serial.println("port configuration error");
          return;
      }
  }
  //==========================
  for (size_t i = 0; i < STEPS; i++) {// map to output register
      for (size_t j = 0; j < PINS; j++) {
          if (order[i][j] == 1) {//output => high on ith step at jth pin, actual pin is at pin[j]
              if (pin[j] >= 0 && pin[j] <= 7) {//OUTPORTD
                  OUTPORTD.DATA[i] |= pow2i(pin[j]);
              }else if (pin[j] >= 8 && pin[j] <= 13) {//OUTPORTB
                  OUTPORTB.DATA[i] |= pow2i(pin[j]-8);
              }
          }
      }
  }
  DDRD = OUTPORTD.DATA_DIRECTION;
  DDRB = OUTPORTB.DATA_DIRECTION;

  PORTD = OUTPORTD.DATA[0];

  PORTB = OUTPORTB.DATA[0];
  Serial.write(READY);// tell controller motor is ready
}

void loop(){
  while (Serial.available() == 0);
  // // DEBUG
  // timer = micros();
  // // DEBUG
  STATE = Serial.read();
  // // DEBUG
  // Serial.write(STATE)
  // // DEBUG
  switch (STATE) {
    case FORWORD:
      rotation = (rotation+1) % 10 // prev: rotation+1 > 9 ? 0:rotation+1;
      break;
    case BACKWARD:
      rotation = rotation-1 < 0 ? 9:rotation-1; // should be simplified
      break;
    case STOP:
      PORTD = 0;
      PORTB = 0;
      while (STATE == STOP) {
        while (Serial.available() == 0);// wait for any other signal to resume
        STATE = Serial.read();
      }
      break;
    default://unrecognized inputs
      PORTD = 0;
      PORTB = 0;
      while (true);
  }
  PORTD = OUTPORTD.DATA[rotation];//-|
  PORTB = OUTPORTB.DATA[rotation];//-+--- 4~12 microsec
  // // DEBUG
  // dtime = micros() - timer;
  // Serial.write((byte *) &dtime, 4);
  // // DEBUG
}
