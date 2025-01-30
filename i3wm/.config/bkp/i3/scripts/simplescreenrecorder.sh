#!/bin/bash

if pidof simplescreenrecorder; then
	killall simplescreenrecorder
else
	simplescreenrecorder --start-hidden 
fi
