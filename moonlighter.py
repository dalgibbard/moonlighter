#!/usr/bin/env python3
#
# PROCESS:
#
# If manual on; Set on to 
# Check lux levels; if lower than "OFF" threshold:
#   --> calculate internally.
#   --> Set timer to go.
#   --> Turn lights on to phase value
#   --> Wait for ambient light levels to rise again
#   --> Turn lights off *IF* lights_on for >30mins//Threshold
#
# ARGS:
#
#
#
#
#
#
#
## Import classes/modules
import getopt, sys, time, imp, datetime, ephem, os, subprocess
from Adafruit_I2C import Adafruit_I2C

## User Defined Variables
# Ambient Lux Level at DUSK
dusk = 20
# Ambient Lux Level at DAWN -- NOTE: MAKE THIS HIGHER THAN dusk
dawn = 50
# Frequency to run loop checks (s)
checkfreq = 30
# Maximum Power output. Lunar Calcs are set proportionately.
max_power = 50
# Tempfile location
tmpfile = '/var/tmp/ml_timestamp'
# Default run_state
run_state = "Stale"
# LED (Servod) PWN ID
ser_id = 0

## Detect early on that we're running with root permissions!
if not os.geteuid() == 0:
        sys.exit('Script must run as root')


#####################
# Borrowed i2c / Lux Class/Functions
#####################
class Adafruit_TSL2651(Adafruit_I2C):
    TSL2561_VISIBLE           =2       # channel 0 - channel 1
    TSL2561_INFRARED          =1       # channel 1
    TSL2561_FULLSPECTRUM      =0       # channel 0

    # I2C address options
    TSL2561_ADDR_LOW          =0x29
    TSL2561_ADDR_FLOAT        =0x39    # Default address (pin left floating)
    TSL2561_ADDR_HIGH         =0x49

    # Lux calculations differ slightly for CS package
    TSL2561_PACKAGE_CS        =0
    TSL2561_PACKAGE_T_FN_CL   =1

    TSL2561_COMMAND_BIT       =0x80    # Must be 1
    TSL2561_CLEAR_BIT         =0x40    # Clears any pending interrupt (write 1 to clear)
    TSL2561_WORD_BIT          =0x20    # 1 = read/write word (rather than byte)
    TSL2561_BLOCK_BIT         =0x10    # 1 = using block read/write

    TSL2561_CONTROL_POWERON   =0x03
    TSL2561_CONTROL_POWEROFF  =0x00

    TSL2561_LUX_LUXSCALE      =14      # Scale by 2^14
    TSL2561_LUX_RATIOSCALE    =9       # Scale ratio by 2^9
    TSL2561_LUX_CHSCALE       =10      # Scale channel values by 2^10
    TSL2561_LUX_CHSCALE_TINT0 =0x7517  # 322/11 * 2^TSL2561_LUX_CHSCALE
    TSL2561_LUX_CHSCALE_TINT1 =0x0FE7  # 322/81 * 2^TSL2561_LUX_CHSCALE

    # T, FN and CL package values
    TSL2561_LUX_K1T           =0x0040  # 0.125 * 2^RATIO_SCALE
    TSL2561_LUX_B1T           =0x01f2  # 0.0304 * 2^LUX_SCALE
    TSL2561_LUX_M1T           =0x01be  # 0.0272 * 2^LUX_SCALE
    TSL2561_LUX_K2T           =0x0080  # 0.250 * 2^RATIO_SCALE
    TSL2561_LUX_B2T           =0x0214  # 0.0325 * 2^LUX_SCALE
    TSL2561_LUX_M2T           =0x02d1  # 0.0440 * 2^LUX_SCALE
    TSL2561_LUX_K3T           =0x00c0  # 0.375 * 2^RATIO_SCALE
    TSL2561_LUX_B3T           =0x023f  # 0.0351 * 2^LUX_SCALE
    TSL2561_LUX_M3T           =0x037b  # 0.0544 * 2^LUX_SCALE
    TSL2561_LUX_K4T           =0x0100  # 0.50 * 2^RATIO_SCALE
    TSL2561_LUX_B4T           =0x0270  # 0.0381 * 2^LUX_SCALE
    TSL2561_LUX_M4T           =0x03fe  # 0.0624 * 2^LUX_SCALE
    TSL2561_LUX_K5T           =0x0138  # 0.61 * 2^RATIO_SCALE
    TSL2561_LUX_B5T           =0x016f  # 0.0224 * 2^LUX_SCALE
    TSL2561_LUX_M5T           =0x01fc  # 0.0310 * 2^LUX_SCALE
    TSL2561_LUX_K6T           =0x019a  # 0.80 * 2^RATIO_SCALE
    TSL2561_LUX_B6T           =0x00d2  # 0.0128 * 2^LUX_SCALE
    TSL2561_LUX_M6T           =0x00fb  # 0.0153 * 2^LUX_SCALE
    TSL2561_LUX_K7T           =0x029a  # 1.3 * 2^RATIO_SCALE
    TSL2561_LUX_B7T           =0x0018  # 0.00146 * 2^LUX_SCALE
    TSL2561_LUX_M7T           =0x0012  # 0.00112 * 2^LUX_SCALE
    TSL2561_LUX_K8T           =0x029a  # 1.3 * 2^RATIO_SCALE
    TSL2561_LUX_B8T           =0x0000  # 0.000 * 2^LUX_SCALE
    TSL2561_LUX_M8T           =0x0000  # 0.000 * 2^LUX_SCALE

    # CS package values
    TSL2561_LUX_K1C           =0x0043  # 0.130 * 2^RATIO_SCALE
    TSL2561_LUX_B1C           =0x0204  # 0.0315 * 2^LUX_SCALE
    TSL2561_LUX_M1C           =0x01ad  # 0.0262 * 2^LUX_SCALE
    TSL2561_LUX_K2C           =0x0085  # 0.260 * 2^RATIO_SCALE
    TSL2561_LUX_B2C           =0x0228  # 0.0337 * 2^LUX_SCALE
    TSL2561_LUX_M2C           =0x02c1  # 0.0430 * 2^LUX_SCALE
    TSL2561_LUX_K3C           =0x00c8  # 0.390 * 2^RATIO_SCALE
    TSL2561_LUX_B3C           =0x0253  # 0.0363 * 2^LUX_SCALE
    TSL2561_LUX_M3C           =0x0363  # 0.0529 * 2^LUX_SCALE
    TSL2561_LUX_K4C           =0x010a  # 0.520 * 2^RATIO_SCALE
    TSL2561_LUX_B4C           =0x0282  # 0.0392 * 2^LUX_SCALE
    TSL2561_LUX_M4C           =0x03df  # 0.0605 * 2^LUX_SCALE
    TSL2561_LUX_K5C           =0x014d  # 0.65 * 2^RATIO_SCALE
    TSL2561_LUX_B5C           =0x0177  # 0.0229 * 2^LUX_SCALE
    TSL2561_LUX_M5C           =0x01dd  # 0.0291 * 2^LUX_SCALE
    TSL2561_LUX_K6C           =0x019a  # 0.80 * 2^RATIO_SCALE
    TSL2561_LUX_B6C           =0x0101  # 0.0157 * 2^LUX_SCALE
    TSL2561_LUX_M6C           =0x0127  # 0.0180 * 2^LUX_SCALE
    TSL2561_LUX_K7C           =0x029a  # 1.3 * 2^RATIO_SCALE
    TSL2561_LUX_B7C           =0x0037  # 0.00338 * 2^LUX_SCALE
    TSL2561_LUX_M7C           =0x002b  # 0.00260 * 2^LUX_SCALE
    TSL2561_LUX_K8C           =0x029a  # 1.3 * 2^RATIO_SCALE
    TSL2561_LUX_B8C           =0x0000  # 0.000 * 2^LUX_SCALE
    TSL2561_LUX_M8C           =0x0000  # 0.000 * 2^LUX_SCALE

    # Auto-gain thresholds
    TSL2561_AGC_THI_13MS      =4850    # Max value at Ti 13ms = 5047
    TSL2561_AGC_TLO_13MS      =100
    TSL2561_AGC_THI_101MS     =36000   # Max value at Ti 101ms = 37177
    TSL2561_AGC_TLO_101MS     =200
    TSL2561_AGC_THI_402MS     =63000   # Max value at Ti 402ms = 65535
    TSL2561_AGC_TLO_402MS     =500

    # Clipping thresholds
    TSL2561_CLIPPING_13MS     =4900
    TSL2561_CLIPPING_101MS    =37000
    TSL2561_CLIPPING_402MS    =65000
    TSL2561_REGISTER_CONTROL          = 0x00
    TSL2561_REGISTER_TIMING           = 0x01
    TSL2561_REGISTER_THRESHHOLDL_LOW  = 0x02
    TSL2561_REGISTER_THRESHHOLDL_HIGH = 0x03
    TSL2561_REGISTER_THRESHHOLDH_LOW  = 0x04
    TSL2561_REGISTER_THRESHHOLDH_HIGH = 0x05
    TSL2561_REGISTER_INTERRUPT        = 0x06
    TSL2561_REGISTER_CRC              = 0x08
    TSL2561_REGISTER_ID               = 0x0A
    TSL2561_REGISTER_CHAN0_LOW        = 0x0C
    TSL2561_REGISTER_CHAN0_HIGH       = 0x0D
    TSL2561_REGISTER_CHAN1_LOW        = 0x0E
    TSL2561_REGISTER_CHAN1_HIGH       = 0x0F

    TSL2561_INTEGRATIONTIME_13MS      = 0x00    # 13.7ms
    TSL2561_INTEGRATIONTIME_101MS     = 0x01    # 101ms
    TSL2561_INTEGRATIONTIME_402MS     = 0x02    # 402ms

    TSL2561_GAIN_1X                   = 0x00    # No gain
    TSL2561_GAIN_16X                  = 0x10    # 16x gain




#**************************************************************************/
#    Writes a register and an 8 bit value over I2C
#**************************************************************************/
    def write8 (self, reg, value):
        if (self._debug == True): print ("write8")
        self._i2c.write8(reg, value)
        if (self._debug == True): print ("write8_end")

#**************************************************************************/
#    Reads an 8 bit value over I2C
#**************************************************************************/
    def read8(self, reg):
        if (self._debug == True): print ("read8")
        return self._i2c.readS8(reg)
        if (self._debug == True): print ("read8_end")

#**************************************************************************/
#   Reads a 16 bit values over I2C
#**************************************************************************/
    def read16(self, reg):
        if (self._debug == True): print ("read16")
        return self._i2c.readS16(reg)
        if (self._debug == True): print ("read16_end")

#**************************************************************************/
#    Enables the device
#**************************************************************************/
    def enable(self):
        if (self._debug == True): print ("enable")
        # Enable the device by setting the control bit to 0x03 */
        self._i2c.write8(self.TSL2561_COMMAND_BIT | self.TSL2561_REGISTER_CONTROL, self.TSL2561_CONTROL_POWERON)
        if (self._debug == True): print ("enable_end")

#**************************************************************************/
#   Disables the device (putting it in lower power sleep mode)
#**************************************************************************/
    def disable(self):
        if (self._debug == True): print ("disable")
        # Turn the device off to save power */
        self._i2c.write8(self.TSL2561_COMMAND_BIT | self.TSL2561_REGISTER_CONTROL, self.TSL2561_CONTROL_POWEROFF)
        if (self._debug == True): print ("disable_end")

#**************************************************************************/
#   Private function to read luminosity on both channels
#**************************************************************************/
    def getData (self):
        if (self._debug == True): print ("getData")
        # Enable the device by setting the control bit to 0x03 */
        self.enable();

        # Wait x ms for ADC to complete */
        if self._tsl2561IntegrationTime == self.TSL2561_INTEGRATIONTIME_13MS:
            time.sleep(0.014)
        elif self._tsl2561IntegrationTime == self.TSL2561_INTEGRATIONTIME_101MS:
          time.sleep(0.102)
        else:
          time.sleep(0.403)


        # Reads a two byte value from channel 0 (visible + infrared) */
        self._broadband = self.read16(self.TSL2561_COMMAND_BIT | self.TSL2561_WORD_BIT | self.TSL2561_REGISTER_CHAN0_LOW);

        # Reads a two byte value from channel 1 (infrared) */
        self._ir = self.read16(self.TSL2561_COMMAND_BIT | self.TSL2561_WORD_BIT | self.TSL2561_REGISTER_CHAN1_LOW);

        # Turn the device off to save power */
        self.disable();
        if (self._debug == True): print ("getData_end")

#**************************************************************************/
#   Constructor
#**************************************************************************/
    def __init__(self, addr=0x39, debug=False):
        self._debug = debug
        if (self._debug == True): print ("__init__")
        self._addr = addr
        self._tsl2561Initialised = False
        self._tsl2561AutoGain = False
        self._tsl2561IntegrationTime = self.TSL2561_INTEGRATIONTIME_13MS
        self._tsl2561Gain = self.TSL2561_GAIN_1X
        self._i2c = Adafruit_I2C(self._addr)
        self._luminosity = 0
        self._broadband = 0
        self._ir = 0
        if (self._debug == True): print ("__init___end")

#**************************************************************************/
#   Initializes I2C and configures the sensor (call this function before
#   doing anything else)
#**************************************************************************/
    def begin(self):
        if (self._debug == True): print ("begin")
        # Make sure we're actually connected */
        x = self.read8(self.TSL2561_REGISTER_ID);
        if not(x & 0x0A):
            return False
        self._tsl2561Initialised = True

        # Set default integration time and gain */
        self.setIntegrationTime(self._tsl2561IntegrationTime)
        self.setGain(self._tsl2561Gain)

        # Note: by default, the device is in power down mode on bootup */
        self.disable()
        if (self._debug == True): print ("begin_end")

        return True

#**************************************************************************/
#   Enables or disables the auto-gain settings when reading
#   data from the sensor
#**************************************************************************/
    def enableAutoGain(self, enable):
        if (self._debug == True): print ("enableAutoGain")
        self._tsl2561AutoGain = enable if True else False
        if (enable == True):
            self._tsl2561AutoGain = enable
        else:
            self._tsl2561AutoGain = False
        if (self._debug == True): print ("enableAutoGain_end")

#**************************************************************************/
#   Sets the integration time for the TSL2561
#**************************************************************************/
    def setIntegrationTime(self, time):
        if (self._debug == True): print ("setIntegrationTime")
        if (not self._tsl2561Initialised):
            self.begin()

        # Enable the device by setting the control bit to 0x03 */
        self.enable();

        # Update the timing register */
        self.write8(self.TSL2561_COMMAND_BIT | self.TSL2561_REGISTER_TIMING, time | self._tsl2561Gain)

        # Update value placeholders */
        self._tsl2561IntegrationTime = time

        # Turn the device off to save power */
        self.disable()
        if (self._debug == True): print ("setIntegrationTime_end")

#**************************************************************************/
#    Adjusts the gain on the TSL2561 (adjusts the sensitivity to light)
#**************************************************************************/
    def setGain(self, gain):
        if (self._debug == True): print ("setGain")
        if (not self._tsl2561Initialised):
            begin()

        # Enable the device by setting the control bit to 0x03 */
        self.enable()

        # Update the timing register */
        self.write8(self.TSL2561_COMMAND_BIT | self.TSL2561_REGISTER_TIMING, self._tsl2561IntegrationTime | gain)

        # Update value placeholders */
        self._tsl2561Gain = gain

        # Turn the device off to save power */
        self.disable()
        if (self._debug == True): print ("setGain_end")

#**************************************************************************/
#   Gets the broadband (mixed lighting) and IR only values from
#   the TSL2561, adjusting gain if auto-gain is enabled
#**************************************************************************/
    def getLuminosity (self):
        if (self._debug == True): print ("getLuminosity")
        valid = False

        if (not self._tsl2561Initialised):
             self.begin()

        # If Auto gain disabled get a single reading and continue */
        if(not self._tsl2561AutoGain):
            self.getData()
            return

        # Read data until we find a valid range */
        _agcCheck = False
        while (not valid):
            _it = self._tsl2561IntegrationTime;

            # Get the hi/low threshold for the current integration time */
            if _it==self.TSL2561_INTEGRATIONTIME_13MS:
                _hi = self.TSL2561_AGC_THI_13MS
                _lo = self.TSL2561_AGC_TLO_13MS
            elif _it==self.TSL2561_INTEGRATIONTIME_101MS:
                _hi = self.TSL2561_AGC_THI_101MS
                _lo = self.TSL2561_AGC_TLO_101MS
            else:
                _hi = self.TSL2561_AGC_THI_402MS
                _lo = self.TSL2561_AGC_TLO_402MS

            self.getData()

            # Run an auto-gain check if we haven't already done so ... */
            if (not _agcCheck):
                if ((self._broadband < _lo) and (self._tsl2561Gain == self.TSL2561_GAIN_1X)):
                    # Increase the gain and try again */
                    self.setGain(self.TSL2561_GAIN_16X)
                    # Drop the previous conversion results */
                    self.getData()
                    # Set a flag to indicate we've adjusted the gain */
                    _agcCheck = True
                elif ((self._broadband > _hi) and (self._tsl2561Gain == self.TSL2561_GAIN_16X)):
                    # Drop gain to 1x and try again */
                    self.setGain(self.TSL2561_GAIN_1X)
                    # Drop the previous conversion results */
                    self.getData()
                    # Set a flag to indicate we've adjusted the gain */
                    _agcCheck = True
                else:
                    # Nothing to look at here, keep moving ....
                    # Reading is either valid, or we're already at the chips limits */
                    valid = True
            else:
                # If we've already adjusted the gain once, just return the new results.
                # This avoids endless loops where a value is at one extreme pre-gain,
                # and the the other extreme post-gain */
                valid = True
        if (self._debug == True): print ("getLuminosity_end")

#**************************************************************************/
#    Converts the raw sensor values to the standard SI lux equivalent.
#    Returns 0 if the sensor is saturated and the values are unreliable.
#**************************************************************************/
    def calculateLux(self):
        if (self._debug == True): print ("calculateLux")
        self.getLuminosity()
        # Make sure the sensor isn't saturated! */
        if (self._tsl2561IntegrationTime == self.TSL2561_INTEGRATIONTIME_13MS):
            clipThreshold = self.TSL2561_CLIPPING_13MS
        elif (self._tsl2561IntegrationTime == self.TSL2561_INTEGRATIONTIME_101MS):
            clipThreshold = self.TSL2561_CLIPPING_101MS
        else:
            clipThreshold = self.TSL2561_CLIPPING_402MS

        # Return 0 lux if the sensor is saturated */
        if ((self._broadband > clipThreshold) or (self._ir > clipThreshold)):
            return 0

        # Get the correct scale depending on the intergration time */
        if (self._tsl2561IntegrationTime ==self.TSL2561_INTEGRATIONTIME_13MS):
            chScale = self.TSL2561_LUX_CHSCALE_TINT0
        elif (self._tsl2561IntegrationTime ==self.TSL2561_INTEGRATIONTIME_101MS):
            chScale = self.TSL2561_LUX_CHSCALE_TINT1
        else:
            chScale = (1 << self.TSL2561_LUX_CHSCALE)

        # Scale for gain (1x or 16x) */
        if (not self._tsl2561Gain):
            chScale = chScale << 4

        # Scale the channel values */
        channel0 = (self._broadband * chScale) >> self.TSL2561_LUX_CHSCALE
        channel1 = (self._ir * chScale) >> self.TSL2561_LUX_CHSCALE

        # Find the ratio of the channel values (Channel1/Channel0) */
        ratio1 = 0;
        if (channel0 != 0):
            ratio1 = (channel1 << (self.TSL2561_LUX_RATIOSCALE+1)) / channel0

        # round the ratio value */
        ratio = (int(ratio1) + 1) >> 1

        if (self.TSL2561_PACKAGE_CS == 1):
            if ((ratio >= 0) and (ratio <= self.TSL2561_LUX_K1C)):
                b=self.TSL2561_LUX_B1C
                m=self.TSL2561_LUX_M1C
            elif (ratio <= self.TSL2561_LUX_K2C):
                b=self.TSL2561_LUX_B2C
                m=self.TSL2561_LUX_M2C
            elif (ratio <= self.TSL2561_LUX_K3C):
                b=self.TSL2561_LUX_B3C
                m=self.TSL2561_LUX_M3C
            elif (ratio <= self.TSL2561_LUX_K4C):
                b=self.TSL2561_LUX_B4C
                m=self.TSL2561_LUX_M4C
            elif (ratio <= self.TSL2561_LUX_K5C):
                b=self.TSL2561_LUX_B5C
                m=self.TSL2561_LUX_M5C
            elif (ratio <= self.TSL2561_LUX_K6C):
                b=self.TSL2561_LUX_B6C
                m=self.TSL2561_LUX_M6C
            elif (ratio <= self.TSL2561_LUX_K7C):
                b=self.TSL2561_LUX_B7C
                m=self.TSL2561_LUX_M7C
            elif (ratio > self.TSL2561_LUX_K8C):
                b=self.TSL2561_LUX_B8C
                m=self.TSL2561_LUX_M8C
        elif (self.TSL2561_PACKAGE_T_FN_CL == 1):
            if ((ratio >= 0) and (ratio <= self.TSL2561_LUX_K1T)):
                b=self.TSL2561_LUX_B1T
                m=self.TSL2561_LUX_M1T
            elif (ratio <= self.TSL2561_LUX_K2T):
                b=self.TSL2561_LUX_B2T
                m=self.TSL2561_LUX_M2T
            elif (ratio <= self.TSL2561_LUX_K3T):
                b=self.TSL2561_LUX_B3T
                m=self.TSL2561_LUX_M3T
            elif (ratio <= self.TSL2561_LUX_K4T):
                b=self.TSL2561_LUX_B4T
                m=self.TSL2561_LUX_M4T
            elif (ratio <= self.TSL2561_LUX_K5T):
                b=self.TSL2561_LUX_B5T
                m=self.TSL2561_LUX_M5T
            elif (ratio <= self.TSL2561_LUX_K6T):
                b=self.TSL2561_LUX_B6T
                m=self.TSL2561_LUX_M6T
            elif (ratio <= self.TSL2561_LUX_K7T):
                b=self.TSL2561_LUX_B7T
                m=self.TSL2561_LUX_M7T
            elif (ratio > self.TSL2561_LUX_K8T):
                b=self.TSL2561_LUX_B8T
                m=self.TSL2561_LUX_M8T
        #endif

        temp = ((channel0 * b) - (channel1 * m))

        # Do not allow negative lux value */
        if (temp < 0):
            temp = 0

        # Round lsb (2^(LUX_SCALE-1)) */
        temp += (1 << (self.TSL2561_LUX_LUXSCALE-1))

        # Strip off fractional portion */
        lux = temp >> self.TSL2561_LUX_LUXSCALE;


        # Signal I2C had no errors */
        if (self._debug == True): print ("calculateLux_end")
        return lux


#####################
# My Functions - Moonlighter
#####################

def usage():
    print("Usage: ", sys.argv[0], " [-v|--verbose] [-l|--lux] [-m|--moonphase] [-h|--help] [-p=XX|--power=XX] [-o|--once] [-f|--force]")

def get_moon_phase():
    # Set the observer point
    g = ephem.Observer()
    # Set the 'body'
    m = ephem.Moon()
    # Set date w/ localisation (ie. GMT+1)
    g.date = datetime.date.today()
    # Correct to UTC
    g.date -= ephem.hour
    # Do initial Computations
    m.compute(g)
    # Get the moon-phase: val between 0.0 and 1.0; round to
    # 2 decimals, multiply by 100 to get a percentage, and
    # Set as an integer to drop the end ".0"
    moonperc = int(round(m.moon_phase, 2) * 100)
    return moonperc

def get_lux():
    LightSensor = Adafruit_TSL2651()
    LightSensor.enableAutoGain(True)
    # Set initial vars
    count = 0
    luxavgtotal = 0
    # Number of tests to average over
    testavg = int(100)
    # Create a cumulative total of values for 'testavg' tests
    while True:
        capture = LightSensor.calculateLux()
        luxavgtotal = capture + luxavgtotal
        count += 1
        # Once we reach the number of required tests, work out the average
        if ( count >= testavg ):
            luxavg = round(luxavgtotal / testavg)
            ## Must set the print value as int(), else Python2.X
            ## prints <value>.0 instead of just <value>
            luxlevel = int(luxavg)
            break
    return luxlevel

def fileout(tmpfile, timestamp):
    # Function to write timestamp to file
    with open(tmpfile, "w") as myfile:
        myfile.write("ts = " + str(timestamp))

def set_power_level(power, verbose, max_power):
    if verbose == True:
        print("Setting Moonlight Power to: ", power, "%")
    # Apply max_threshold value:
    power = ( power / 100 ) * max_power
    # Max pulse width is "2000" = 20ms. work out percentage to pulsewidth conv.
    if power == 0:
        pulsewidth = 0
    else:
        pulsewidth = 20 * power
    out = None
    err = None
    set_power_cmd = str("echo ")+ srv_id + str("=") + str(pulsewidth) + str(" > /dev/servoblaster")
    if os.path.exists("/dev/servoblaster"):
        do_set_power = subprocess.Popen([set_power_cmd], stdout=subprocess.PIPE, shell=True)
        (out, err) = do_set_power.communicate()
        if err == None:
            if verbose == True:
                print("Power set successfully")
        else:
            print("ERROR SETTING SERVOBLASTER LEVEL")
    else:
        print("SERVOBLASTER SPECIAL FILE NOT AVAILABLE")

def check_timestamp(curtime, delay, verbose):
    try:
        # Try and get data.ts from the tmpfile.
        f = open(tmpfile)
        global data
        data = imp.load_source('data', '', f)
        f.close()
        if data.ts:
            if verbose == True:
                print("Got last run time of: ", data.ts)
                print("Which was:            ", datetime.datetime.fromtimestamp(int(data.ts)))
            nextrun = int(data.ts) + int(delay)
            if nextrun < curtime:
                if verbose == True:
                    print("Current Time is larger than required delay.")
                    print("Timestamp check is True.")
                return True
            else:
                if verbose == True:
                    print("Time since last switch is less than Delay.")
                    print("Timestamp check is False.")
                return False
        else:
            print("ERR: Last timestamp not found in tmpfile.")
            # Assume it's OK...
            return True
#    except IO.Error as err:
    except Exception as err:
        if verbose == True:
            print("ERR: ", err)
            print("No previous run timestamp found")
        return True
    

def do_run(verbose, force, run_state):
    luxlevel = get_lux()
    # Use a default delay of 30mins//1800s...
    timenow = time.time()
    # If Force is defined, then ignore whatever timediff returns :)
    if force == True:
        timediff = True
    else:
        timediff = check_timestamp(timenow, 1800, verbose)
    # If it's getting dark, and the moonlights aren't on yet,
    # and we haven't switched this in the past 30mins, turn lights on!
    if luxlevel < dusk and ( run_state == "Stale" or run_state == "Off" ) and timediff == True:
        pwrlvl = get_moon_phase()
        set_power_level(pwrlvl, verbose, max_power)
        fileout(tmpfile, timenow)
        run_state = "On"
        return run_state
    elif luxlevel > dawn and ( run_state == "Stale" or run_state == "On" ) and timediff == True:
        pwrlvl = 0
        set_power_level(pwrlvl, verbose, max_power)
        fileout(tmpfile, timenow)
        run_state = "Off"
        return run_state
    else:
        if verbose == True:
            print("No lighting change required.")

def main(run_state, max_power):
    lux = get_lux()
    try:
        # v= versbose w/set, l=current_lux + quit, m=moon_phase + quit,
        # h=help, s=current_light_state + Lux level, p=set_on_power_level
        # o=once_only
        opts, args = getopt.getopt(sys.argv[1:], "vlmhsp:of", ["verbose", "lux", "moonphase", "help", "state", "power", "once", "force" ])
    except getopt.GetoptError as err:
        # Print Help info and exit:
        print(str(err))
        usage()
        sys.exit(1)
    verbose = False
    runOnce = False
    force = False
    run = True
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-v", "--verbose"):
            verbose = True          
            print("Verbosity Enabled.")
            print("Dusk Lux Level is: " + str(dusk) + str("lux"))
            print("Dawn Lux Level is: " + str(dawn) + str("lux"))
            print("Maximum LED Power: " + str(max_power) + str("%"))
            print("Delay between constant checks is: " + str(checkfreq) + "s")
            print("Tmpfile is: " + tmpfile)
            print("")
        elif o in ("-l", "--lux"):
            print("Ambient_Lux_Level: ", get_lux(), "Lux")
            run = False
        elif o in ("-m", "--moonphase"):
            print("Moon_Phase_Brightness: ", get_moon_phase(), "%")
            run = False
        elif o in ("-p", "--power"):
            pwrlvl = int(a)
            set_power_level(pwrlvl, verbose, max_power)
            run = False
        elif o in ("-o", "--once"):
            runOnce = True
        elif o in ("-f", "--force"):
            force = True
        else:
            assert False, "unhandled option"
    # Code run
    if run == True:
        if runOnce == True:
            if verbose == True:
                print("Running once only...")
            run_state = do_run(verbose, force)
            sys.exit()
        else:
            if verbose == True:
                print("Running normal loop")
            try:
                while True:
                    run_state = do_run(verbose, force, run_state)
                    if verbose == True:
                        print("Sleeping for " + str(checkfreq) + "s")
                    time.sleep(checkfreq)
            except KeyboardInterrupt:
                print("Keyboard Interrupt. Quitting...")
                sys.exit()

if __name__ == "__main__":
    main(run_state, max_power)
