// Nano Every has A0-7, D0-13 but D0 and D1 are serial, D{3,5,6,9,10} PWM, D13 LED
#define PIN_CHARGE 7
#define PIN_FIRE 8
#define PIN_LF 5
#define PIN_RF 6
#define PIN_LR 9
#define PIN_RR 10

#define CHARGE_TIME_MAX 5000

#define digitalPWMWrite(X, Y) analogWrite(X, Y)

#define STATE_WAITING 0
#define STATE_MOVING 1
#define STATE_CHARGING 2
#define STATE_FIRING 3
