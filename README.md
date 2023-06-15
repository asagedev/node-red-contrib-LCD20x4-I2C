This node is a driver for 20x4 HD44780 LCD Display connected via I2C PCF8574

Dependencies: SMBus, enable i2c in raspi-config
```
sudo apt-get install python3-smbus
sudo raspi-config
    Interfacing Options>I2C>Enable
```

This node will accept an object `msg.payload.msgs`.  If the object passed does not contain 4 lines, the difference is filled with blank lines.

Line data structure:

* msg must be a string.
  * If msg is more than 20 characters the node will handle scrolling.
* pos (position) is optional and must be a number with any value between 1-20.  This value is used for offsetting text, but you can also insert spaces in to msg instead of supplying pos.
  * If pos is not supplied it will default to 1.
* center is optional and must be a boolean value passed as a string
  * If pos and center are both set, center will override pos.

If there is an error it will be logged to Node-RED and display an error on the LCD screen.

Object format:
```
msg.payload = {
    msgs: [
        {
            msg: "string",
            pos: number,
            center: "boolean"
        },
        {
            msg: "string",
            pos: number,
            center: "boolean"
        },
        {
            msg: "string",
            pos: number,
            center: "boolean"
        },
        {
            msg: "string",
            pos: number,
            center: "boolean"
        }
    ]
};
```