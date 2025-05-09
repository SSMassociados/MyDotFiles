#!/bin/sh

# Verifica dependências
check_dependencies() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "ERROR: jq não instalado"
        exit 1
    fi
    
    if ! command -v udisksctl >/dev/null 2>&1; then
        echo "ERROR: udisks2 não instalado"
        exit 1
    fi
    
    if ! command -v udevadm >/dev/null 2>&1; then
        echo "ERROR: udev não disponível"
        exit 1
    fi
}

# Mostra notificação
show_notification() {
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -t 3000 "Polybar USB" "$1"
    fi
}

# Fecha gerenciador de arquivos
close_file_manager() {
    mount_point="$1"
    
    for fm in nautilus thunar dolphin pcmanfm caja; do
        if command -v "$fm" >/dev/null 2>&1; then
            case "$fm" in
                nautilus) nautilus -q ;;
                thunar) pkill -f "thunar $mount_point" ;;
                dolphin) qdbus org.kde.dolphin-$(pgrep -o dolphin) /MainApplication quit ;;
                pcmanfm) pkill -f "pcmanfm $mount_point" ;;
                caja) pkill -f "caja $mount_point" ;;
            esac
        fi
    done
}

# Abre gerenciador de arquivos
open_file_manager() {
    mount_point="$1"
    
    if [ -n "$mount_point" ] && [ -d "$mount_point" ]; then
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$mount_point" &
        else
            for fm in nautilus thunar dolphin pcmanfm caja; do
                if command -v "$fm" >/dev/null 2>&1; then
                    "$fm" "$mount_point" &
                    break
                fi
            done
        fi
    fi
}

# Processa dispositivos USB
usb_print() {
    devices=$(lsblk -Jplno NAME,TYPE,RM,SIZE,MOUNTPOINT,VENDOR,LABEL 2>/dev/null)
    
    if [ -z "$devices" ]; then
        echo ""
        return
    fi
    
    output=""
    counter=0
    
    # Dispositivos não montados
    while IFS= read -r unmounted; do
        [ -z "$unmounted" ] && continue
        
        vendor=$(echo "$devices" | jq -r --arg dev "$unmounted" '.blockdevices[] | select(.name == $dev) | .vendor // "Dispositivo"')
        label=$(echo "$devices" | jq -r --arg dev "$unmounted" '.blockdevices[] | select(.name == $dev) | .label // ""')
        
        if [ -n "$label" ]; then
            ident="$label"
        else
            ident=$(echo "$vendor" | tr -d ' ' | cut -c1-15)
        fi
        
        [ $counter -gt 0 ] && output="$output   "
        output="$output#1 $ident"
        counter=$((counter + 1))
    done <<< "$(echo "$devices" | jq -r '.blockdevices[] | select(.type == "part") | select(.rm == true) | select(.mountpoint == null) | .name')"
    
    # Dispositivos montados
    while IFS= read -r mounted; do
        [ -z "$mounted" ] && continue
        
        size=$(echo "$devices" | jq -r --arg dev "$mounted" '.blockdevices[] | select(.name == $dev) | .size')
        label=$(echo "$devices" | jq -r --arg dev "$mounted" '.blockdevices[] | select(.name == $dev) | .label // ""')
        
        ident="${label:-$size}"
        
        [ $counter -gt 0 ] && output="$output   "
        output="$output#2 $ident"
        counter=$((counter + 1))
    done <<< "$(echo "$devices" | jq -r '.blockdevices[] | select(.type == "part") | select(.rm == true) | select(.mountpoint != null) | .name')"
    
    echo "$output"
}

# Monta dispositivo USB
usb_mount() {
    devices=$(lsblk -Jplno NAME,TYPE,RM,MOUNTPOINT,LABEL 2>/dev/null)
    unmounted=$(echo "$devices" | jq -r '.blockdevices[] | select(.type == "part") | select(.rm == true) | select(.mountpoint == null) | .name' | head -n 1)
    
    if [ -z "$unmounted" ]; then
        show_notification "Nenhum dispositivo USB para montar"
        return
    fi
    
    label=$(echo "$devices" | jq -r --arg dev "$unmounted" '.blockdevices[] | select(.name == $dev) | .label // "Dispositivo USB"')
    
    if udisksctl mount -b "$unmounted" >/dev/null 2>&1; then
        mounted_point=$(lsblk -Jplno NAME,MOUNTPOINT | jq -r --arg dev "$unmounted" '.blockdevices[] | select(.name == $dev) | .mountpoint')
        show_notification "$label montado em $mounted_point"
        sleep 0.5
        open_file_manager "$mounted_point"
    else
        show_notification "Erro ao montar $label"
    fi
    
    usb_update
}

# Desmonta dispositivo USB
usb_unmount() {
    devices=$(lsblk -Jplno NAME,TYPE,RM,MOUNTPOINT,LABEL 2>/dev/null)
    mounted=$(echo "$devices" | jq -r '.blockdevices[] | select(.type == "part") | select(.rm == true) | select(.mountpoint != null) | .name' | head -n 1)
    
    if [ -z "$mounted" ]; then
        show_notification "Nenhum dispositivo USB montado"
        return
    fi
    
    mount_point=$(echo "$devices" | jq -r --arg dev "$mounted" '.blockdevices[] | select(.name == $dev) | .mountpoint')
    label=$(echo "$devices" | jq -r --arg dev "$mounted" '.blockdevices[] | select(.name == $dev) | .label // "Dispositivo USB"')
    
    close_file_manager "$mount_point"
    
    if udisksctl unmount -b "$mounted" >/dev/null 2>&1; then
        show_notification "$label desmontado"
        udisksctl power-off -b "${mounted%%[0-9]*}" >/dev/null 2>&1
    else
        show_notification "Erro ao desmontar $label"
    fi
    
    usb_update
}

# Atualiza o módulo
usb_update() {
    pid=$(cat /tmp/polybar-usb-udev.pid 2>/dev/null)
    [ -n "$pid" ] && kill -USR1 "$pid" 2>/dev/null
}

# Monitora eventos udev
monitor_udev() {
    udevadm monitor --kernel --subsystem-match=block --property | while read -r line; do
        case "$line" in
            *ACTION=add*|*ACTION=remove*|*ACTION=change*)
                usb_update
                ;;
        esac
    done
}

# Main
case "$1" in
    --mount)
        usb_mount
        ;;
    --mount-notify)
        usb_mount
        ;;
    --unmount)
        usb_unmount
        ;;
    --unmount-notify)
        usb_unmount
        ;;
    --monitor)
        monitor_udev
        ;;
    --update)
        usb_print
        ;;
    *)
        echo $$ > /tmp/polybar-usb-udev.pid
        usb_print
        
        # Inicia monitor udev em segundo plano
        ~/.config/polybar/scripts/system-usb-udev.sh --monitor &
        
        # Loop principal com intervalo menor
        while true; do
            sleep 5 &
            wait $!
            usb_print
        done
        ;;
esac


#Crie uma regra udev (opcional, mas recomendado):

#Crie um arquivo em /etc/udev/rules.d/99-polybar-usb.rules com:

#ACTION=="add|remove", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", RUN+="/bin/su SEU_USUARIO -c '/bin/sh -c \"~/.config/polybar/scripts/system-usb-udev.sh --update\"'"

#Substitua SEU_USUARIO pelo seu nome de usuário.

#Recarregue as regras udev:
#sudo udevadm control --reload-rules
#sudo udevadm trigger



