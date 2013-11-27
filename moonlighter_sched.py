#!/usr/bin/env python3
#
## Import classes/modules
import getopt, sys, imp, datetime, time, ephem, os, subprocess
from Adafruit_I2C import Adafruit_I2C

## User Defined Variables
# Night time Start: Hour
onhour="21"
# Night time Start: Mins
onmin="59"
# Night time End: Hour
offhour="09"
# Night time End: Mins
offmin="59"

# Frequency to run loop checks (s)
checkfreq = 30
# Maximum Power output. Lunar Calcs are set proportionately.
max_power = 100
# Default run_state
run_state = "Stale"
# LED (Servod) PWN ID
srv_id = 0

## Detect early on that we're running with root permissions!
#if not os.geteuid() == 0:
#        sys.exit('Script must run as root')

#####################
# My Functions - Moonlighter
#####################

def usage():
    print("Usage: ", sys.argv[0], " [-v|--verbose] [-m|--moonphase] [-h|--help] [-p=XX|--power=XX] [-o|--once] [-f|--force]")

def check_time(timenow, onhour, onmin, offhour, offmin, verbose):
    now = datetime.datetime.now()
    now_time = now.time()
    # If we're actually moonlighting at night:
    if int(offhour) < int(onhour):
        # Check to see if we're in daylight mode
        if datetime.time(int(offhour),int(offmin)) <= now_time <= datetime.time(int(onhour),int(onmin)):
            if verbose == True:
                print("Day Time detected.")
            return False
        else:
            if verbose == True:
                print("Night Time detected.")
            return True
    else:
        if datetime.time(int(onhour),int(onmin)) <= now_time <= datetime.time(int(offhour),int(offmin)):
            if verbose == True:
                print("Night Time detected.")
            return True
        else:
            if verbose == True:
                print("Day Time detected.")
            return False

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

def set_power_level(power, verbose, max_power, srv_id):
    if verbose == True:
        print("Setting Moonlight Power to: ", power, "%")
    # Apply max_threshold value:
    power = int(( power / 100 ) * max_power)
    # Max pulse width is "2000" = 20ms. work out percentage to pulsewidth conv.
    if power == 0:
        pulsewidth = int(0)
    else:
        pulsewidth = int(20 * power)
    out = None
    err = None
    set_power_cmd = str('echo ') + str(srv_id) + str('=1 >/dev/servoblaster; ') + str('echo ')+ str(srv_id) + str('=') + str(pulsewidth) + str(' > /dev/servoblaster')
    if verbose == True:
        print("Servoblaster Command: " + str(set_power_cmd))
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

def do_run(verbose, force, run_state, onhour, onmin, offhour, offmin, srv_id):
    timenow = datetime.datetime.now().time()
    # If Force is defined, then ignore whatever timediff returns :)
    if force == True:
        nighttime = True
    else:
        nighttime = check_time(timenow, onhour, onmin, offhour, offmin, verbose)
    # If it's within the scheduled nighttime, and the moonlights aren't on
    # yet, turn them on.
    if ( run_state == "Stale" or run_state == "Off" ) and nighttime == True:
        pwrlvl = get_moon_phase()
        set_power_level(pwrlvl, verbose, max_power, srv_id)
        run_state = "On"
        return run_state
    elif ( run_state == "Stale" or run_state == "On" ) and nighttime == False:
        pwrlvl = 0
        set_power_level(pwrlvl, verbose, max_power, srv_id)
        run_state = "Off"
        return run_state
    else:
        if verbose == True:
            print("No lighting change required.")

def main(run_state, max_power, onhour, onmin, offhour, offmin, srv_id, checkfreq):
    try:
        # v= versbose w/set, m=moon_phase + quit,
        # h=help, p=set_on_power_level
        # o=once_only f=force
        opts, args = getopt.getopt(sys.argv[1:], "vmhp:of", ["verbose", "moonphase", "help", "power", "once", "force" ])
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
            print("Maximum LED Power: " + str(max_power) + str("%"))
            print("Delay between constant checks is: " + str(checkfreq) + "s")
            print("Night Time Start: " + str(onhour) + str(':') + str(onmin))
            print("Night Time End:   " + str(offhour) + str(':') + str(offmin))
            print("")
        elif o in ("-m", "--moonphase"):
            print("Moon_Phase_Brightness: ", get_moon_phase(), "%")
            run = False
        elif o in ("-p", "--power"):
            pwrlvl = int(a)
            set_power_level(pwrlvl, verbose, max_power, srv_id)
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
            run_state = do_run(verbose, force, run_state, onhour, onmin, offhour, offmin, srv_id)
            sys.exit()
        else:
            if verbose == True:
                print("Running normal loop")
            try:
                while True:
                    print(datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
                    run_state = do_run(verbose, force, run_state, onhour, onmin, offhour, offmin, srv_id)
                    if verbose == True:
                        print("Sleeping for " + str(checkfreq) + "s")
                    time.sleep(int(checkfreq))
            except KeyboardInterrupt:
                print("Keyboard Interrupt. Quitting...")
                sys.exit()

if __name__ == "__main__":
    main(run_state, max_power, onhour, onmin, offhour, offmin, srv_id, checkfreq)
