#!/bin/bash

# ==========================
# Ambiente gráfico do i3wm
# ==========================

# Locale
export LANG=pt_BR.UTF-8

# Qt
export QT_QPA_PLATFORMTHEME=qt5ct
export QT_QPA_PLATFORMTHEME_QT6=qt6ct
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# GTK (opcional)
# export GTK_THEME=Adwaita
# export GTK_CSD=0
# export GTK_CLIENT_SIDE_DECORATIONS=0

# Cursor
# export XCURSOR_THEME=Bibata-Modern-Ice
# export XCURSOR_SIZE=24

# Sessão e ambiente
export XDG_CURRENT_DESKTOP=i3
export XDG_SESSION_DESKTOP=i3
export XDG_SESSION_TYPE=x11

# Escala / DPI (opcional, útil em HiDPI)
# export GDK_SCALE=1
# export GDK_DPI_SCALE=1.0

# Input method (descomente se usar IBus)
# export GTK_IM_MODULE=ibus
# export QT_IM_MODULE=ibus
# export XMODIFIERS=@im=ibus
# ibus-daemon -drx &
