#ifndef TSC_ROBOT_H
#define TSC_ROBOT_H
#pragma GCC diagnostic ignored "-Wunknown-pragmas"
#pragma region pins
#ifdef ARDUINO_AVR_MEGA2560
// Mega 2560 has A0-15, D0-53 but D0 and D1 are serial, D2-13 PWM, D13 LED
#define PIN_CHARGE 50
#define PIN_FIRE 52
#define PIN_LF 2
#define PIN_RF 3
#define PIN_LR 4
#define PIN_RR 5
#define PIN_SBUS 19
#define PIN_DEBUG_OSCILLO 12
#else
#error "Define pins for this board in tsc-robot.h"
#endif
#pragma endregion pins

#pragma region channels
// FrSky XM PLUS delivers 16 channels, with the last one being RSSI
// remember array indexes (here) are transmitter channel - 1
#define CHANNEL_MOVE_FR 2
#define CHANNEL_MOVE_LR 1
//#define CHANNEL_TILT 0 // not currently implemented in robot hardware
#define CHANNEL_YAW 3
#define CHANNEL_ARM 4
#define CHANNEL_CHARGE_CARM 7
#define CHANNEL_FIRE 8
#pragma endregion channels

#pragma region constants
#define CHARGE_TIME_MAX 5000

#define STATE_WAITING 0
#define STATE_MOVING 1
#define STATE_CHARGING 2
#define STATE_FIRING 3

#define SBUS_MIN 172
#define SBUS_MID 992
#define SBUS_MAX 1811
#define SBUS_RANGE SBUS_MAX - SBUS_MIN
#pragma endregion constants

// more readable when writing PWM to digital pins
#define digitalPWMWrite(X, Y) analogWrite(X, Y)
// convert the sbus channel short into a byte range. default limits on transmitter channels are 172 and 1811 (992 is midpoint),
// #define sbusMap(X) (uint16_t)(map(X, SBUS_MIN, SBUS_MAX, INT8_MIN, INT8_MAX)) // not currently in use

#ifdef DEBUG_MECANUM
#define DEBUG_SERIAL
#endif

namespace mecanum
{
struct motors;
motors *init_motors();
void calculateSpeed(motors *toRet, uint16_t x, uint16_t y, uint16_t yaw);
} // namespace mecanum

#endif
