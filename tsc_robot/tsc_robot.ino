#include <stdint.h>
#include <SBUS.h>
#define DEBUG_SERIAL
//#define DEBUG_OSCILLO
#define DEBUG_MECANUM
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
mecanum::motors *motors;

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
  motors = mecanum::init_motors();
}

void loop()
{
#ifdef DEBUG_OSCILLO
  digitalWrite(PIN_DEBUG_OSCILLO, !digitalRead(PIN_DEBUG_OSCILLO)); // connect pin to oscilloscope to see how fast loop runs
#endif
  /**************************************
 * Input section
 *************************************/
  if (sbus.read(&channels[0], &isFailSafe, &isLostFrame))
  {
#ifdef DEBUG_SERIAL
    for (uint16_t i = 0; i < 9; i++)
    {
      sprintf(printbuf, "Channel %hu\t%hu\r\n", i + 1, channels[i]);
      Serial.print(printbuf);
    }
#endif
    mecanum::calculateSpeed(motors,
                            (int16_t)(channels[CHANNEL_MOVE_LR]) - SBUS_MID,
                            (int16_t)(channels[CHANNEL_MOVE_FR]) - SBUS_MID,
                            (int16_t)(channels[CHANNEL_YAW]) - SBUS_MID);

    if (!(*((uint64_t *)motors) == 0UL)) // check all 4 values at once TODO: imprecision makes this difficult
    {
      state = STATE_MOVING;
      isMoving = true;
    }
    else
    {
      isMoving = false;
      if (channels[CHANNEL_CHARGE_CARM] == SBUS_MID)
      {
        state = STATE_CHARGING;
      }
      else if (channels[CHANNEL_FIRE] == SBUS_MAX) // cannon arm is checked inside STATE_FIRING handler
      {
        state = STATE_FIRING;
      }
      else
      {
        state = STATE_WAITING;
      }
    }
    // TODO check SBUS failsafe (transmitter out of range)
  }

  /**************************************
 * Action section
 *************************************/
#ifdef DEBUG_SERIAL
  sprintf(printbuf, "Acting in state %d\n", state);
  Serial.print(printbuf);
#endif
  if (channels[CHANNEL_ARM] > 1800)
  {
    digitalWrite(PIN_LED_ARM, HIGH);
    switch (state)
    {
    case STATE_WAITING: // do nothing
      break;
    case STATE_MOVING: // set motor PWM
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
      if (!isMoving && channels[CHANNEL_CHARGE_CARM] == SBUS_MAX)
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
  else
  {
    digitalWrite(PIN_LED_ARM, LOW);
#error "does not stop charging if disarmed while charging. should write all output pins LOW when disarmed"
  }
  
}
