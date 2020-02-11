// TODO include SBUS library
#include "tsc-robot.h"

uint8_t state = STATE_WAITING;
bool isCharging = false;
bool isCharged = false;
bool isMoving = false;
long chargingStart = 0L;

void setup()
{
  pinMode(PIN_CHARGE, OUTPUT);
  pinMode(PIN_FIRE, OUTPUT);
  pinMode(PIN_LF, OUTPUT);
  pinMode(PIN_RF, OUTPUT);
  pinMode(PIN_LR, OUTPUT);
  pinMode(PIN_RR, OUTPUT);
}

void loop()
{
  // TODO check input for commands, set `state` appropriately

  switch (state)
  {
  case STATE_WAITING: // do nothing
    break;
  case STATE_MOVING: // set motor PWM and isMoving
    // TODO do mecanum calculations (trig)
    // TODO send input levels to motors
    // TODO if input is non-zero, isMoving = true
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
    }
    break;
  default: // reset
    state = STATE_WAITING;
    break;
  }
}
