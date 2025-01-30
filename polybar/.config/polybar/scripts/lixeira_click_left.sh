#!/bin/bash

if pidof pcmanfm; then
	killall pcmanfm
else
	pcmanfm trash:/// 
fi

#pidof pcmanfm && killall pcmanfm; pcmanfm trash:///

#if pidof pcmanfm >/tmp/pid; then kill $(</tmp/pid); else { nohup pcmanfm trash:/// &>/dev/null & }; fi
