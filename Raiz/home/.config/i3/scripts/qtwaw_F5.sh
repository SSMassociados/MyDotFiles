#!/bin/bash

until WID=$(xdotool search --onlyvisible --class qtwaw|head -1) && [ "$WID" ]; do
  sleep 1
done
xdotool windowactivate $WID && xdotool key F5

#WID=$(xdotool search --onlyvisible --class qtwaw|head -1)
#xdotool windowactivate ${WID}
#xdotool key F5

