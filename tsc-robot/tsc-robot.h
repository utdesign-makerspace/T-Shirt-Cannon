#pragma region pins
#ifdef AVR_MEGA2560
// Mega 2560 has A0-15, D0-53 but D0 and D1 are serial, D2-13 PWM, D13 LED
#define PIN_CHARGE 50
#define PIN_FIRE 52
#define PIN_LF 2
#define PIN_RF 3
#define PIN_LR 4
#define PIN_RR 5
#define PIN_SBUS 19
#else
#error "Define pins for this board in tsc-robot.h"
#endif
#pragma endregion pins

#pragma region channels
// FrSky XM PLUS delivers 16 channels, with the last one being RSSI
// TODO: figure out channel architecture and allocation
// TODO: maybe channels are LR movement, FR movement, charge, and fire
#pragma endregion channels

#pragma region constants
#define CHARGE_TIME_MAX 5000

#define STATE_WAITING 0
#define STATE_MOVING 1
#define STATE_CHARGING 2
#define STATE_FIRING 3
#pragma endregion constants

#define digitalPWMWrite(X, Y) analogWrite(X, Y)

#pragma region tests
// make sure all necessary pins were defined
#ifndef PIN_CHARGE
#error "Please define PIN_CHARGE in tsc-robot.h"
#endif
#ifndef PIN_FIRE
#error "Please define PIN_FIRE in tsc-robot.h"
#endif
#ifndef PIN_LF
#error "Please define PIN_LF in tsc-robot.h"
#endif
#ifndef PIN_RF
#error "Please define PIN_RF in tsc-robot.h"
#endif
#ifndef PIN_LR
#error "Please define PIN_LR in tsc-robot.h"
#endif
#ifndef PIN_RR
#error "Please define PIN_RR in tsc-robot.h"
#endif
#ifndef PIN_SBUS
#error "Please define PIN_SBUS in tsc-robot.h"
#endif
// TODO: verify PIN_SBUS is a serial pin using the Arduino platform #define stuff
#pragma endregion tests
