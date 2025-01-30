#!/bin/bash

pidof pcmanfm && killall pcmanfm || pcmanfm

#if pidof pcmanfm; then
	#killall pcmanfm
#else
	#pcmanfm 
#fi


#if=se then=então,caso sim  else=senão, outro(a) 

#if pidof pcmanfm >/tmp/pid; then kill $(</tmp/pid); else { nohup pcmanfm &>/dev/null & }; fi
