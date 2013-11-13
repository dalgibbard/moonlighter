#!/usr/bin/env python3
#
# PROCESS:
#
# If manual on; Set on to 
# Check lux levels; if lower than "OFF" threshold:
#   -> Validate lunar phase online
#     --> FAIL: calculate internally.
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
import getopt, sys, time, imp, datetime, ephem

## User Defined Variables
# Ambient Lux Level at DUSK
dusk = 20
# Ambient Lux Level at DAWN -- NOTE: MAKE THIS HIGHER THAN dusk
dawn = 50
# Frequency to run loop checks (s)
checkfreq = 30
tmpfile = '/tmp/ml_timestamp'

def usage():
    print("Usage: ", sys.argv[0], " [-v|--verbose] [-l|--lux] [-m|--moonphase] [-h|--help] [-s|--state] [-p=XX|--power=XX] [-o|--once] [-f|--force]")

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
    ### Code to get current lux levels
    # NOTE
    luxlevel = 10
    return luxlevel

def get_state():
    ### Code to read current power output level // on/off
    # NOTE
    lightstatus = 0
    return lightstatus

def fileout(tmpfile, timestamp):
    # Function to write timestamp to file
    with open(tmpfile, "w") as myfile:
        myfile.write("ts = " + str(timestamp))

def set_power_level(power, verbose):
    if verbose == True:
        print("Setting Moonlight Power to: ", power, "%")
    ### Code to set power level!

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
    

def do_run(verbose, force):
    luxlevel = get_lux()
    cur_state = get_state()
    # Use a default delay of 30mins//1800s...
    timenow = time.time()
    # If Force is defined, then ignore whatever timediff returns :)
    if force == True:
        timediff = True
    else:
        timediff = check_timestamp(timenow, 1800, verbose)
    # If it's getting dark, and the moonlights aren't on yet,
    # and we haven't switched this in the past 30mins, turn lights on!
    if luxlevel < dusk and cur_state == 0 and timediff == True:
        pwrlvl = get_moon_phase()
        set_power_level(pwrlvl, verbose)
        fileout(tmpfile, timenow)
    elif luxlevel > dawn and cur_state != 0 and timediff == True:
        pwrlvl = 0
        set_power_level(pwrlvl, verbose)
        fileout(tmpfile, timenow)
    else:
        if verbose == True:
            print("No lighting change required.")

def main():
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
            print("Dusk Lux Level is: " + str(dusk))
            print("Dawn Lux Level is: " + str(dawn))
            print("Delay between constant checks is: " + str(checkfreq) + "s")
            print("Tmpfile is: " + tmpfile)
            print("")
        elif o in ("-l", "--lux"):
            print("Ambient_Lux_Level: ", get_lux(), "Lux")
            run = False
        elif o in ("-m", "--moonphase"):
            print("Moon_Phase_Brightness: ", get_moon_phase(), "%")
            run = False
        elif o in ("-s", "--state"):
            print("Current_State: ", get_state(), "%")
            run = False
        elif o in ("-p", "--power"):
            pwrlvl = int(a)
            set_power_level(pwrlvl, verbose)
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
            do_run(verbose, force)
            sys.exit()
        else:
            if verbose == True:
                print("Running normal loop")
            try:
                while True:
                    do_run(verbose, force)
                    if verbose == True:
                        print("Sleeping for " + str(checkfreq) + "s")
                    time.sleep(checkfreq)
            except KeyboardInterrupt:
                print("Keyboard Interrupt. Quitting...")
                sys.exit()

if __name__ == "__main__":
    main()
