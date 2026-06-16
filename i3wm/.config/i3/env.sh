#!/bin/bash

# ==========================
# Ambiente gráfico do i3wm
# ==========================

# Monitor
export FALLBACK_MONITOR="eDP1"

# Locale
export LANG=pt_BR.UTF-8

# Qt
export QT_QPA_PLATFORMTHEME=qt6ct
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# Mantenha o WPS usando Noto Sans - wrapper
export QT_FONT_OVERRIDE="Noto Sans,12,-1,5,50,0,0,0,0,0"

# IBUS
export GTK_IM_MODULE=ibus
export QT_IM_MODULE=ibus
export XMODIFIERS=@im=ibus
export SDL_IM_MODULE=ibus          

# Sessão e ambiente
export XDG_CURRENT_DESKTOP=i3
export XDG_SESSION_TYPE=x11
export XDG_SESSION_DESKTOP=i3
export DESKTOP_SESSION=i3
