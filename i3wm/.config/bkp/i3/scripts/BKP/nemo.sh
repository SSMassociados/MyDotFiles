#!/bin/bash

if pidof nemo; then
	killall nemo
else
	nemo 
fi
