#!/bin/bash

# Carrega cor do Pywal
source "${HOME}/.cache/wal/colors.sh"
primary="${color1}"

# Ícones com cor
ICON_ROOT="%{F$primary}濫%{F-}"
ICON_HOME="%{F$primary}%{F-}"

# Obtem uso das partições
ROOT_USAGE=$(df -h / | awk 'NR==2 {print $5}')
HOME_USAGE=$(df -h /home | awk 'NR==2 {print $5}')

# Exibe com separador
echo "${ICON_ROOT}  ${ROOT_USAGE}  |  ${ICON_HOME}  ${HOME_USAGE}"




