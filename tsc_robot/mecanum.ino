namespace mecanum
{
struct motors
{
    uint8_t rightFront;
    uint8_t leftFront;
    uint8_t rightRear;
    uint8_t leftRear;
};

motors *init_motors()
{
    motors *mots = (motors *)malloc(sizeof(motors));
    *mots = {0, 0, 0, 0};
    return mots;
}

// y is forward/reverse, x is left/right, input range is [-127, 127], output is [0, 255]
void calculateSpeed(motors *toRet, uint16_t x, uint16_t y, uint16_t yaw)
{
    if (abs(x) < 10)
    {
        x = 0;
    }
    if (abs(y) < 10)
    {
        y = 0;
    }
    if (abs(yaw) < 10)
    {
        yaw = 0;
    }
#ifdef DEBUG_MECANUM
    char printbuf[30];
    sprintf(printbuf, "x %hd\ty %hd\tyaw %hd\n", x, y, yaw);
    Serial.print(printbuf);
#endif

    toRet->rightFront = mapEsc(-x + y - yaw);
    toRet->leftFront = mapEsc(x + y + yaw);
    toRet->rightRear = mapEsc(x + y - yaw);
    toRet->leftRear = mapEsc(-x + y + yaw);

#ifdef DEBUG_MECANUM
    sprintf(printbuf, "FR %hhu\tFL %hhu\tBR %hhu\tBL %hhu\n", toRet->rightFront, toRet->leftFront, toRet->rightRear, toRet->leftRear);
    Serial.print(printbuf);
#endif
}

uint8_t mapEsc(int8_t in)
{
    if (in < -10)
    {
        return (uint8_t)map(-in % -128, -127, 0, 70, 127);
    }
    else if (in > 10)
    {
        return (uint8_t)map(in % 128, 0, 127, 195, 254);
    }
    else
    {
        return (uint8_t)0;
    }
}
} // namespace mecanum
