#!/bin/bash

if pidof spotify; then
	killall spotify
else
	spotify 
fi
