#!/bin/bash
#
# Script to get the current "Brightness" of the lunar phase.
#   Returns between 0 and 100 (%) of total brightness.
#
if [ "`which pi-blaster | grep -c .`" = 0 ];then
	echo "Pi Blaster not found. Please install that first!"
fi
if [ ! -e /dev/pi-blaster ]; then
	sudo pi-blaster
	if [ ! $? = 0 ]; then
		echo "Failed to start Pi Blaster. Please debug. Exiting..."
		exit 1
	fi
fi

# OUTPUT PIN (PIN2 = GPIO18//ONBOARD PIN12)
PIN=2

if [[ "x$1" =~ off ]]|[[ "x$1" =~ stop ]]; then
	echo "${PIN}=0" > /dev/pi-blaster
	exit 0
elif [ ! "x$1" = "x" ]; then
	if [[ "$1" =~ ^[0-9]{1,2}$ ]]; then
		echo "${PIN}=0.`printf '%02d' $1`" > /dev/pi-blaster
		exit 0
	elif [ "$1" = "100" ];then
		echo "${PIN}=1.00" > /dev/pi-blaster
		exit 0
	elif [ "$1" = '-v' ]; then
		VERBOSE=1
	elif [ "$1" = '-h' ]; then
		echo "Usage: $0 [power%|off|stop|-v|-h]"
		echo "     - No args will set the output to current Lunar Power"
		exit 1
	else
		echo "Invalid value: $1"
		echo "Setting by lunar value instead."
	fi
fi

VALUE=$(curl http://www.die.net/moon/ 2>/dev/null| egrep -o "[0-9]{1,3}(\.[0-9]{1})?% lit" | awk -F'%' '{print$1}')
if [[ ! $VALUE =~ ^[0-9]{1,3} ]]; then
	echo "Error Retrieving Value"
	exit 1
else
	POWER=$(printf "%0.f\n" ${VALUE})
	if [ "x$VERBOSE" = "x1" ]; then
		echo "Lunar Power: ${POWER}%"
	fi
fi
if [ $POWER = "100" ]; then
	POWERVAR=1.00
else
	POWERVAR=0.`printf '%02d' ${POWER}`
fi
# Set the power output on pi-blaster Pin2 (Pin12 on board//GPIO18)
echo "${PIN}=${POWERVAR}" > /dev/pi-blaster
