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

// y is forward/reverse, x is left/right
void calculateSpeed(motors *toRet, uint16_t x, uint16_t y, uint16_t yaw)
{
#ifdef DEBUG_MECANUM
    char printbuf[30];
    sprintf(printbuf, "x %hd\ty %hd\tyaw %hd\n", x, y, yaw);
    Serial.print(printbuf);
#endif

    toRet->leftFront = (uint8_t)map(x + y + yaw, -3 * SBUS_RANGE, 3 * SBUS_RANGE, 0, 255);
    toRet->rightFront = (uint8_t)map(-x + y - yaw, -3 * SBUS_RANGE, 3 * SBUS_RANGE, 0, 255);
    toRet->rightRear = (uint8_t)map(-x + y + yaw, -3 * SBUS_RANGE, 3 * SBUS_RANGE, 0, 255);
    toRet->leftRear = (uint8_t)map(x + y - yaw, -3 * SBUS_RANGE, 3 * SBUS_RANGE, 0, 255);

#ifdef DEBUG_MECANUM
    sprintf(printbuf, "FR %hhu\tFL %hhu\tBR %hhu\tBL %hhu\n", toRet->rightFront, toRet->leftFront, toRet->rightRear, toRet->leftRear);
    Serial.print(printbuf);
#endif
}
} // namespace mecanum
