#!/bin/bash

if pidof gnome-calculator; then
	killall gnome-calculator
else
	gnome-calculator
fi

#if pidof gnome-calculator >/tmp/pid ; then kill $(</tmp/pid) ; else { nohup gnome-calculator &>/dev/null & }; fi

