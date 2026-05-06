#!/bin/bash

# ==========================
# Ambiente gráfico do i3wm
# ==========================

# Locale
export LANG=pt_BR.UTF-8

# Link simbólico para o GTK4 herdar as configurações do GTK3
# Criar link simbólico apenas se não existir
if [ ! -e ~/.config/gtk-4.0/settings.ini ]; then
    mkdir -p ~/.config/gtk-4.0
    ln -sf ~/.config/gtk-3.0/settings.ini ~/.config/gtk-4.0/settings.ini
fi

# Qt
export QT_QPA_PLATFORMTHEME=qt6ct
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# Mantenha o WPS usando Noto Sans - wrapper
export QT_FONT_OVERRIDE="Noto Sans,12,-1,5,50,0,0,0,0,0"

# Sessão e ambiente
export XDG_CURRENT_DESKTOP=i3
export XDG_SESSION_TYPE=x11
