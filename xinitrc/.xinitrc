#!/bin/sh

# === Variáveis de ambiente ===

## Locale
#export LANG=pt_BR.UTF-8

## Qt
#export QT_QPA_PLATFORMTHEME=qt5ct
#export QT_QPA_PLATFORMTHEME_QT6=qt6ct
#export QT_AUTO_SCREEN_SCALE_FACTOR=1

## GTK (opcional)
#export GTK_THEME=Adwaita
#export GTK_CSD=0
#export GTK_CLIENT_SIDE_DECORATIONS=0

## Cursor
#export XCURSOR_THEME=Bibata-Modern-Ice
#export XCURSOR_SIZE=24

# Sessão
#export XDG_CURRENT_DESKTOP=i3
#export XDG_SESSION_DESKTOP=i3
#export XDG_SESSION_TYPE=x11

## DPI
#export GDK_SCALE=1
#export GDK_DPI_SCALE=1.0

# === Recursos do X e teclas ===
userresources=$HOME/.Xresources
usermodmap=$HOME/.Xmodmap
sysresources=/etc/X11/xinit/.Xresources
sysmodmap=/etc/X11/xinit/.Xmodmap

if [ -f $sysresources ]; then
    xrdb -merge $sysresources
fi

if [ -f $sysmodmap ]; then
    xmodmap $sysmodmap
fi

if [ -f "$userresources" ]; then
    xrdb -merge "$userresources"
fi

if [ -f "$usermodmap" ]; then
    xmodmap "$usermodmap"
fi

# === Scripts do sistema ===
if [ -d /etc/X11/xinit/xinitrc.d ] ; then
 for f in /etc/X11/xinit/xinitrc.d/?*.sh ; do
  [ -x "$f" ] && . "$f"
 done
 unset f
fi

# === Inicia o i3 ===
exec i3

