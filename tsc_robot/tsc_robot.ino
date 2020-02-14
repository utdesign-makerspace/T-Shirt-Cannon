#include <SBUS.h>
#define DEBUG_SERIAL
#define DEBUG_OSCILLO
#include "tsc_robot.h"

SBUS sbus(Serial1);
uint16_t channels[16];
bool isFailSafe;
bool isLostFrame;
#ifdef DEBUG_SERIAL
char printbuf[20];
#endif

uint8_t state = STATE_WAITING;
bool isCharging = false;
bool isCharged = false;
bool isMoving = false;
unsigned long chargingStart = 0UL;

void setup()
{
#ifdef DEBUG_SERIAL
  Serial.begin(115200);
  while (!Serial)
    ;
#endif
  sbus.begin();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  pinMode(PIN_CHARGE, OUTPUT);
  pinMode(PIN_FIRE, OUTPUT);
  pinMode(PIN_LF, OUTPUT);
  pinMode(PIN_RF, OUTPUT);
  pinMode(PIN_LR, OUTPUT);
  pinMode(PIN_RR, OUTPUT);
  pinMode(PIN_DEBUG_OSCILLO, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop()
{
#ifdef DEBUG_SERIAL
  //Serial.println("loop start [slow]: " + millis()); // check how fast the loop is running
#endif
#ifdef DEBUG_OSCILLO
  digitalWrite(PIN_DEBUG_OSCILLO, !digitalRead(PIN_DEBUG_OSCILLO)); // connect pin to oscilloscope to see how fast loop runs
#endif
  uint8_t ch_move_fr = 127;
  uint8_t ch_move_lr = 127;
  // TODO check input for commands, set `state` appropriately
  if (sbus.read(&channels[0], &isFailSafe, &isLostFrame))
  {
#ifdef DEBUG_SERIAL
    for (uint16_t i = 0; i < 9; i++)
    {
      sprintf(printbuf, "Channel %hu\t%hu\r\n", i+1, channels[i]);
      Serial.print(printbuf);
    }
#endif
    ch_move_fr = sbusMap(channels[CHANNEL_MOVE_FR]);
    ch_move_lr = sbusMap(channels[CHANNEL_MOVE_LR]);
    if (!(ch_move_fr == 127 && ch_move_lr == 127))
    {
      state = STATE_MOVING;
      isMoving = true;
    }
    else
    {
      isMoving = false;
      state = STATE_WAITING; // TODO handle other channels (charging, firing)
    }
    // TODO check SBUS failsafe (transmitter out of range)
  }

  switch (state)
  {
  case STATE_WAITING: // do nothing
    break;
  case STATE_MOVING: // set motor PWM and isMoving
    // TODO do mecanum calculations (trig)
    // TODO send input levels to motors
    break;
  case STATE_CHARGING:
    if (isCharging)
    {
      if (millis() > chargingStart + CHARGE_TIME_MAX)
      {
        digitalWrite(PIN_CHARGE, LOW);
        isCharging = false;
        isCharged = true;
      }
    }
    else // !isCharging, i.e. start charging
    {
      digitalWrite(LED_BUILTIN, HIGH);
      isCharging = true;
      chargingStart = millis();
      digitalWrite(PIN_CHARGE, HIGH);
    }
    break;
  case STATE_FIRING:
    if (!isMoving)
    {
      digitalWrite(PIN_FIRE, HIGH);
      delay(500);
      digitalWrite(PIN_FIRE, LOW);
      isCharged = false;
      digitalWrite(LED_BUILTIN, LOW);
    }
    break;
  default: // reset
    state = STATE_WAITING;
    break;
  }
}
