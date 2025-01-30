#!/bin/sh
# SPDX-License-Identifier: 0BSD
# dependencias: upower, ffplay ou paplay, notify-send, dbus

while true
do
	  BATERIA="$(upower -d | awk '/percentage/ { print $2 }' | uniq | cut -c1-2)"
      ESTADO="$(upower -d | awk '/state/ { print $2}' | uniq)"

	if [ "$BATERIA" -ge 95 ] && [ "$ESTADO" = 'charging' ]; then
		paplay /usr/share/sounds/freedesktop/stereo/bell.oga && \
		notify-send --urgency=normal \
		--icon=/usr/share/icons/Adwaita/16x16/status/battery-level-90-symbolic.symbolic.png \
		"Bateria carregada ${BATERIA}%" 'No talo'

	elif [ "$BATERIA" -lt 20 ] && [ "$ESTADO" = 'discharging' ]; then
		paplay /usr/share/sounds/freedesktop/stereo/bell.oga && \
		notify-send --urgency=critical \
		--icon=/usr/share/icons/Adwaita/16x16/status/battery-level-20-charging-symbolic.symbolic.png \
		"Bateria baixa ${BATERIA}%" 'Descarregando'
	fi

	sleep 10
done


