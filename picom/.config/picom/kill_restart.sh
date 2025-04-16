#!/bin/bash

# Termine instâncias do Picom em execução
killall -q picom

# Espere até que os processos em execução sejam terminados
while pgrep -u $UID -x picom >/dev/null; do sleep 1; done

# execute a Picom, usando a configuração padrão ~/.config/picom/picom.conf
picom --config ~/.config/picom/picom.conf &

echo "Picom relaunched..."
