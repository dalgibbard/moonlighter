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
* Internet Access (For the initial install anyway!)

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

### Install Dependancies
The moonlighter code utilises python3. To use it, and to install the required dependancies, do the following:
```
sudo apt-get update
sudo apt-get install python3 python3-dev python3-setuptools python3-pip
```

### Obtain PyEphem Library
The PyEphem is a scientific computational library which offers various
precise calculations for lunar cycles/patterns etc.

To install it, do the following:
```
sudo pip-3.2 install pyephem
```

### Enable pi-blaster /// UNDER-REVIEW for ServoBlaster
~info here~
#### ServoBlaster Install
Whilst still in the moonlighter folder (just for simplicities sake really), pull do the latest ServoBlaster code
which is used to control the brightness of the Moonlight LEDs.

```
git clone https://github.com/richardghirst/PiBits
cd PiBits/ServoBlaster/user
make
sudo make install
## Replace the original ServoBlaster init script with this one (somewhat optional):
cd ../../..
sudo cp servoblaster-init /etc/init.d/servoblaster
```

### Check out the Git code
```
git clone https://github.com/dalgibbard/moonlighter.git
cd moonlighter
```

### Install a patched version of py-smbus
py-smbus is required in order to interface with the i2c bus
(and therefore, the luminosity sensor). However, at the time
of writing, it's not compatible with Python3.

Therefore, follow these steps to fix!
```
wget http://ftp.de.debian.org/debian/pool/main/i/i2c-tools/i2c-tools_3.1.0.orig.tar.bz2
tar xf i2c-tools_3.1.0.orig.tar.bz2
rm -f i2c-tools_3.1.0.orig.tar.bz2
cd i2c-tools-3.1.0/py-smbus
# patch over smbusmodule.c
mv ../../pysmbus-patch/smbusmodule.c .
python3 setup.py build
sudo python3 setup.py install
```

## Hardware Setup Notes
### Luminosity Sensor
* The Adafruit board should be connected as follows:

```
PI      Adafruit
PIN1 -> VCC
PIN3 -> SDA
PIN5 -> SCL
PIN6 -> GND
```

### Power
Power for my kit is being powered by a cheapo, chinese made 12v to 5v inverter,
spliced with a MicroUSB cable.
This allows me to power the Pi from 5v and the 12v LEDs, all from a single
12v Source. You could use 5v LEDs (with a sufficient PSU) or other similar
transform options for supply.

### Darlington + LEDs
Although the Darlington allows for control of eight seperate channels, I only really needed for one SET of LEDs, so they're all wired up in Parallel on the first channel (GPIO to Darlington_Pin1, LED Grounds to Darlington_Pin18). So you end up with:
```
            ______
RPI_P12 -> 1|  ^  |18 --> ALL_LED_GND                            __
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

## NEW: Run the Code
TBC
Run the following for more info:
```
./moonlighter.py -h
```

## LEGACY: Run the Code
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
