# TSC Robot Code
This is the code running on the robot.

## Hardware
Currently targeting the Arduino Nano Every microcontroller. R/C hardware TBD.

### Pins
They are defined in [tsc-robot.h](./tsc-robot.h) as:   
- 5: left front motor (PWM)
- 6: right front motor (PWM)
- 7: charge pressure
- 8: fire
- 9: left rear motor (PWM)
- 10: right rear motor (PWM)

## Program Architecture
`setup()` is straightforward.

The `loop()` is designed to return to the top of the loop at a high frequency. The functions of the robot are divided into states, each with its own `case`.

We want to be able to process incoming commands very quickly (>60Hz), so each `case` should be non-blocking and break very soon. This means they need to be resumable, and store their state outside the `loop()` scope. This enables us to cancel a pressure charge in-progress (safety!).

The exception to this fast-`case` rule is the firing state, where there is never going to be anything else to do besides rapidly discharging the pressure via the muzzle.
