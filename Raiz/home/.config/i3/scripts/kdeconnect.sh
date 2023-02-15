#!/bin/bash

if pidof kdeconnect-indicator; then
	killall kdeconnect-indicator
else
	kdeconnect-indicator
fi


