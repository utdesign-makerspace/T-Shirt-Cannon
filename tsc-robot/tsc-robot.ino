#include <SBUS.h>
#include "tsc-robot.h"

SBUS sbus(Serial1);
uint16_t channels[16];
bool isFailSafe;
bool isLostFrame;

uint8_t state = STATE_WAITING;
bool isCharging = false;
bool isCharged = false;
bool isMoving = false;
unsigned long chargingStart = 0UL;

void setup()
{
  sbus.begin();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  pinMode(PIN_CHARGE, OUTPUT);
  pinMode(PIN_FIRE, OUTPUT);
  pinMode(PIN_LF, OUTPUT);
  pinMode(PIN_RF, OUTPUT);
  pinMode(PIN_LR, OUTPUT);
  pinMode(PIN_RR, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop()
{
  uint8_t ch1 = 127;
  uint8_t ch2 = 127;
  // TODO check input for commands, set `state` appropriately
  if (sbus.read(&channels[0], &isFailSafe, &isLostFrame))
  {
    ch1 = sbusMap(channels[0]);
    ch2 = sbusMap(channels[1]);
    if (!(ch1 == 127 && ch2 == 127))
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
