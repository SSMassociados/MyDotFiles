#!/usr/bin/env bash
ID=$(xinput list | grep -i touchpad | grep -oP 'id=\K\d+')

# Adicionar no ~/.config/i3/config: $exe ~/.config/i3/scripts/touchpad.sh
# Nomes exatos das propriedades disponíveis no seu touchpad: xinput list-props 7

#!/usr/bin/env bash
ID=$(xinput list | grep -i touchpad | grep -oP 'id=\K\d+')

# Habilita toque para clicar (1 toque = clique esquerdo)
xinput set-prop "$ID" "libinput Tapping Enabled" 1

# Habilita arrastar com toque (segurar após toque para arrastar)
xinput set-prop "$ID" "libinput Tapping Drag Enabled" 1

# Desabilita bloqueio de arraste (solta o arraste ao levantar o dedo)
# xinput set-prop "$ID" "libinput Tapping Drag Lock Enabled" 0

# Mapeamento de toques: lmr=(0,1) | lrm=(1,0)
xinput set-prop "$ID" "libinput Tapping Button Mapping Enabled" 0 1

# Desabilita rolagem natural (direção tradicional: scroll para baixo = conteúdo sobe)
xinput set-prop "$ID" "libinput Natural Scrolling Enabled" 0

# ⚠️ edge NÃO é suportado pelo seu touchpad (Scroll Methods Available: 1, 1, 0)
# Métodos disponíveis: twofinger=(1,0,0) | twofinger-alt=(0,1,0) | desativado=(0,0,0)
xinput set-prop "$ID" "libinput Scroll Method Enabled" 0 1 0

# Habilita rolagem horizontal
# xinput set-prop "$ID" "libinput Horizontal Scroll Enabled" 1

# Define distância de pixels por tick de rolagem (10-30, padrão=15)
# xinput set-prop "$ID" "libinput Scrolling Pixel Distance" 15

# Método de clique físico: buttonareas=(1,0) | clickfinger=(0,1)
# xinput set-prop "$ID" "libinput Click Method Enabled" 1 0

# Desabilita emulação do botão do meio
# xinput set-prop "$ID" "libinput Middle Emulation Enabled" 0

# Define velocidade do cursor (intervalo: -1.0 a 1.0)
xinput set-prop "$ID" "libinput Accel Speed" 0.5

# Define perfil de aceleração: adaptive=(1,0,0) | flat=(0,1,0) | custom=(0,0,1)
xinput set-prop "$ID" "libinput Accel Profile Enabled" 1 0 0

# Desabilita o touchpad enquanto digita (evita cliques acidentais)
# xinput set-prop "$ID" "libinput Disable While Typing Enabled" 1

# Mantém botão esquerdo como principal (left handed: 0=desabilitado)
# xinput set-prop "$ID" "libinput Left Handed Enabled" 0

# Desabilita touchpad ao conectar mouse externo: normal=(0,0) | com-mouse=(0,1)
# xinput set-prop "$ID" "libinput Send Events Mode Enabled" 0 1
