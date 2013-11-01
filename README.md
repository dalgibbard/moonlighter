# moonlighter

Raspberry Pi driven Marine Aquarium Moonlighting

## Description
This page and associated code is a work in progress.

## Thanks to:
* schwabbbel / Mario on the Adafruit Forums for porting the Adafruit C Class (http://forums.adafruit.com/viewtopic.php?f=8&t=34922&p=227280#p222877)
* Bernhard Renz for fixing the python-smbus code for Python3 (http://www.spinics.net/lists/linux-i2c/msg08427.html)
* catmaker on the RasPi Forums for simplifying the smbus install details! (http://www.raspberrypi.org/phpBB3/viewtopic.php?p=229682#p229682)
* sarfata for Pi-Blaster, and Richard Hirst for the original ServoBlaster
* The Raspberry Pi Foundation for creating a lovely bit of kit
* Adafruit for making some really nice boards and libraries!
* The wife for putting up with me.
* Anyone i may have missed... :(

## To Do:
* Create documentation on http://dgunix.com on board/box creation and wiring
* Upload svg + stl design files
* Validate documentation

## Required Hardware:
The hardware i've used for this project is:
* A Revision 2 Raspberry Pi (any Revision is fine though!)
* WiPi Wireless Adapter for Raspberry Pi (Optional)
* Adafruit Luminosity Sensor
* 12v White LEDs, ideally the Wide-Angle type (flat top) with an in-line 470ohm resistor.
* 12v Power Supply
* 12v to 5v DC/DC Stepdown.
* 1x LN2803A Darlington Array IC
* Moonlighter Board (link to follow) [Optional - this can be done on a breadboard or whatever too]
* Lots of cable... AWG26 is fine.
* Internet Access ;)

## Configuring the Raspberry Pi
### Enabling I2C
* Edit /etc/modules to include:
```
i2c-bcm2708
i2c-dev
```
* Edit /etc/modprobe.d/raspi-blacklist.conf to read:
```
blacklist spi-bcm2708
#blacklist i2c-bcm2708
```

* Update your Raspberry Pi (write this in a terminal):
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo rpi-update
sudo reboot
```
### Enable pi-blaster
~info here~

## Check out the Git code
git clone https://github.com/dalgibbard/moonlighter.git

## Hardware Setup Notes
### Luminosity Sensor
* The Adafruit board should be connected as follows:
```
PI     |  Adafruit
-------------------
PIN1  ->  VCC
PIN3  ->  SDA
PIN5  ->  SCL
PIN6  ->  GND
```

### Power

### Darlington + LEDs
Although the Darlington allows for control of eight seperate channels, I only really needed for one SET of LEDs, so they're all wired up in Parallel on the first channel (GPIO to Darlington_Pin1, LED Grounds to Darlington_Pin18). So you end up with:
```
            _______
RPI_P12 -> 1|  o  |18 --> ALL_LED_GND                            __
            |  L  |           \----> LED_1 -- 470ohn Resistor -->||
            |  N  |            \----> LED_N -- 470ohm Resistor ->||
            |  2  |                  etc.                        ||
            |  8  |                                              ||
            |  0  |                                              ||
            |  3  |                                              ||
            |  A  |                                              \/  ___
RPI_GND -> 9|_____|10 ========================================> 12v+ |X| 12v_GND
        |\                                                                 /|
          \---------------------------------------------------------------/
            (GND Link possibly optional, It didn't work for me otherwise!)
```

## Run the Code
### Check current Lux Levels
The script lux.py provides the current Lux reading from the Adafruit Luminosity Sensor board.

Examples on how to use:
```
# Using default python version, print current Lux level.
$ python lux.py
428

# Using default python version, continuously print current Lux level until interrupted.
$ python lux.py loop
428
427
427
428
...
```

### Power the LEDs
The "lunar_power.sh" script will power up the LEDs between 0 and 100% of their power, depending on the current, real-world Lunar cycle. Fullmoon = 100%, Halfmoon = 50% etc.

*NOTE:* By default, the script assumes that the darlington array is connected to Physical PIN12.

Examples on how to use:
```
# Get lunar value, and power up the LEDs to that. No output.
./lunar_power.sh

# Same as above, but with output details:
./lunar_power.sh -v

# Define a custom power value, example below powers the LEDs to 64% power:
./lunar_power.sh 64

# Stop/turn off the LEDs:
./lunar_power.sh off
```
