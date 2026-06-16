#!/bin/sh

# sudo nano /etc/udev/rules.d/99-polybar-usb.rules
# ACTION=="add", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", RUN+="/bin/su sidiclei -c '/home/sidiclei/.config/polybar/scripts/system_usb_udev.sh --update'"
# ACTION=="remove", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", RUN+="/bin/su sidiclei -c '/home/sidiclei/.config/polybar/scripts/system_usb_udev.sh --update'"

# sudo udevadm control --reload-rules
# sudo udevadm trigger

# Verifica dependências
check_dependencies() {
    for cmd in jq udisksctl udevadm lsblk; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo "ERROR: $cmd não instalado"
            exit 1
        fi
    done
}

# Mostra notificação
show_notification() {
    command -v notify-send >/dev/null 2>&1 && \
        notify-send -t 3000 "Polybar USB" "$1"
}

# Fecha thunar no ponto de montagem
close_file_manager() {
    pkill -f "thunar $1" 2>/dev/null
}

## 1 - Abre thunar no ponto de montagem
#open_file_manager() {
    #[ -n "$1" ] && [ -d "$1" ] && thunar "$1" &
#}

## 2 - Lista partições USB removíveis — flat (sem children no Arch)
## Saída: NAME\tMOUNTPOINT\tLABEL\tSIZE\tVENDOR  (uma por linha)
#list_usb_parts() {
    #lsblk -Jplno NAME,TYPE,RM,SIZE,MOUNTPOINT,VENDOR,LABEL 2>/dev/null | \
    #jq -r '
      #.blockdevices[]
      #| select(.type == "part" and .rm == true)
      #| [.name, (.mountpoint // ""), (.label // ""), .size, (.vendor // "")]
      #| @tsv
    #'
#}

# 1 - Abre thunar só se tiver permissão de leitura
open_file_manager() {
    mount_point="$1"
    if [ -n "$mount_point" ] && [ -d "$mount_point" ] && [ -r "$mount_point" ]; then
        thunar "$mount_point" &
    fi
}

# 2 - Filtra partições EFI/BIOS pela label e pelo tipo
list_usb_parts() {
    lsblk -Jplno NAME,TYPE,RM,SIZE,MOUNTPOINT,VENDOR,LABEL,PARTTYPE 2>/dev/null | \
    jq -r '
      .blockdevices[]
      | select(.type == "part" and .rm == true)
      | select(
          (.label // "" | ascii_downcase) | 
          test("efi|vtoyefi|bios|boot") | not
        )
      | [.name, (.mountpoint // ""), (.label // ""), .size, (.vendor // "")]
      | @tsv
    '
}

# Imprime estado atual para a polybar
usb_print() {
    output=""
    counter=0

    while IFS=$(printf '\t') read -r name mountpoint label size vendor; do
        [ -z "$name" ] && continue

        if [ -z "$mountpoint" ]; then
            # Não montado — ícone cinza
            if [ -n "$label" ]; then
                ident="$label"
            else
                ident=$(printf '%s' "$vendor" | tr -d ' \t' | cut -c1-15)
                [ -z "$ident" ] && ident="USB"
            fi
            icon=" "
        else
            # Montado — ícone verde
            ident="${label:-$size}"
            icon=" "
        fi

        [ "$counter" -gt 0 ] && output="$output  "
        output="${output}${icon}${ident}"
        counter=$((counter + 1))
    done << EOF
$(list_usb_parts)
EOF

    printf '%s\n' "$output"
}

# Monta o primeiro dispositivo não montado
usb_mount() {
    unmounted=$(list_usb_parts | awk -F'\t' '$2 == "" { print $1; exit }')

    if [ -z "$unmounted" ]; then
        show_notification "Nenhum dispositivo USB para montar"
        return
    fi

    label=$(list_usb_parts | awk -F'\t' -v d="$unmounted" '$1 == d { print $3; exit }')
    [ -z "$label" ] && label="Dispositivo USB"

    result=$(udisksctl mount -b "$unmounted" 2>&1)
    if [ $? -eq 0 ]; then
        mounted_point=$(printf '%s' "$result" | grep -oP '(?<=at ).*' | tr -d '.')
        [ -z "$mounted_point" ] && \
            mounted_point=$(lsblk -no MOUNTPOINT "$unmounted" 2>/dev/null | head -n1)
        show_notification "$label montado em $mounted_point"
        sleep 0.3
        open_file_manager "$mounted_point"
    else
        show_notification "Erro ao montar $label"
    fi

    usb_update
}

# Desmonta o primeiro dispositivo montado
usb_unmount() {
    mounted=$(list_usb_parts | awk -F'\t' '$2 != "" { print $1; exit }')

    if [ -z "$mounted" ]; then
        show_notification "Nenhum dispositivo USB montado"
        return
    fi

    mount_point=$(list_usb_parts | awk -F'\t' -v d="$mounted" '$1 == d { print $2; exit }')
    label=$(list_usb_parts | awk -F'\t' -v d="$mounted" '$1 == d { print $3; exit }')
    [ -z "$label" ] && label="Dispositivo USB"

    close_file_manager "$mount_point"

    if udisksctl unmount -b "$mounted" >/dev/null 2>&1; then
        show_notification "$label desmontado com segurança"
        parent=$(lsblk -no PKNAME "$mounted" 2>/dev/null | head -n1)
        [ -n "$parent" ] && udisksctl power-off -b "/dev/$parent" >/dev/null 2>&1
    else
        show_notification "Erro ao desmontar $label (feche arquivos abertos)"
    fi

    usb_update
}

# Acorda o loop principal via USR1
usb_update() {
    pid=$(cat /tmp/polybar-usb.pid 2>/dev/null)
    [ -n "$pid" ] && kill -USR1 "$pid" 2>/dev/null
    return 0
}

# Monitora eventos udev e chama usb_update
monitor_udev() {
    udevadm monitor --udev --subsystem-match=block 2>/dev/null | \
    while IFS= read -r line; do
        case "$line" in
            *add*|*remove*|*change*)
                usb_update
                ;;
        esac
    done
}

# ─── Main ─────────────────────────────────────────────────────────────────────
case "$1" in
    --mount|--mount-notify)
        usb_mount
        ;;
    --unmount|--unmount-notify)
        usb_unmount
        ;;
    --monitor)
        monitor_udev
        ;;
    --update)
        usb_print
        ;;
    *)
        check_dependencies

        # Grava PID deste processo (o que a polybar mantém vivo)
        echo $$ > /tmp/polybar-usb.pid

        # Flag para controlar o loop sem depender do exit status do wait
        _need_print=0
        trap '_need_print=1' USR1

        # Mata monitor anterior se existir
        old_mon=$(cat /tmp/polybar-usb-monitor.pid 2>/dev/null)
        [ -n "$old_mon" ] && kill "$old_mon" 2>/dev/null

        # Inicia monitor udev em segundo plano
        "$0" --monitor &
        echo $! > /tmp/polybar-usb-monitor.pid

        # Imprime estado inicial
        usb_print

        # Loop principal — nunca termina
        while true; do
            # Dorme 5s em background; wait é interrompível por USR1
            sleep 5 &
            _sleep_pid=$!
            wait $_sleep_pid 2>/dev/null

            # Seja por USR1 ou por timeout, imprime
            usb_print
            _need_print=0
        done
        ;;
esac
