#!/bin/bash

if pidof pcmanfm; then
	killall pcmanfm
else
	pcmanfm menu://applications/ 
fi

#pidof pcmanfm && killall pcmanfm; pcmanfm menu://applications/

#if pidof pcmanfm >/tmp/pid; then kill $(</tmp/pid); else { nohup pcmanfm menu://applications/ &>/dev/null & }; fi



