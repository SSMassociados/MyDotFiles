#!/bin/bash
# scanner_wifi.sh — Escaneia redes Wi-Fi e sugere o melhor canal (Linux)
# Uso: ./scanner_wifi.sh [--json] [--continuous] [--csv]

# Cores
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
BOLD='\033[1m'
DIM='\033[0;90m'
RESET='\033[0m'

# Configurações
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

PARSED_FILE="$TMPDIR_WORK/parsed.txt"

# Modos de operação
JSON_MODE=false
CONTINUOUS_MODE=false
CSV_MODE=false
CONTINUOUS_INTERVAL=5

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_MODE=true
            shift
            ;;
        --continuous)
            CONTINUOUS_MODE=true
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                CONTINUOUS_INTERVAL="$2"
                shift
            fi
            shift
            ;;
        --csv)
            CSV_MODE=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [opcoes]"
            echo ""
            echo "Opcoes:"
            echo "  --json              Saida em formato JSON"
            echo "  --continuous [N]    Modo continuo (atualiza a cada N segundos, padrao: 5)"
            echo "  --csv               Exportar para CSV (modo unico)"
            echo "  --help, -h          Mostrar esta ajuda"
            echo ""
            exit 0
            ;;
        *)
            echo "Opcao desconhecida: $1"
            echo "Use --help para ajuda"
            exit 1
            ;;
    esac
done

# -- Funcoes auxiliares --

# Detectar o gateway padrão (IP do roteador)
get_default_gateway() {
    local gateway=""
    
    if command -v route &>/dev/null; then
        gateway=$(route -n 2>/dev/null | grep '^0.0.0.0' | awk '{print $2}' | head -1)
    fi
    
    if [ -z "$gateway" ] && command -v ip &>/dev/null; then
        gateway=$(ip route 2>/dev/null | grep 'default' | awk '{print $3}' | head -1)
    fi
    
    if [ -z "$gateway" ] && [ -f "/proc/net/route" ]; then
        gateway=$(awk '/^00000000/ {print $2}' /proc/net/route | while read hex; do
            echo "$hex" | sed 's/\(..\)\(..\)\(..\)\(..\)/\4.\3.\2.\1/' | sed 's/\.0\+/\./g'
        done | head -1)
    fi
    
    if [ -z "$gateway" ] && command -v nmcli &>/dev/null; then
        gateway=$(nmcli dev show 2>/dev/null | grep -i 'GATEWAY' | head -1 | awk '{print $2}')
    fi
    
    echo "$gateway"
}

get_default_interface() {
    local iface=""
    
    if command -v ip &>/dev/null; then
        iface=$(ip route 2>/dev/null | grep 'default' | awk '{print $5}' | head -1)
    elif command -v route &>/dev/null; then
        iface=$(route -n 2>/dev/null | grep '^0.0.0.0' | awk '{print $8}' | head -1)
    fi
    
    echo "$iface"
}

get_local_ip() {
    local local_ip=""
    local iface=$(get_default_interface)
    
    if [ -n "$iface" ]; then
        if command -v ip &>/dev/null; then
            local_ip=$(ip -4 addr show "$iface" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
        elif command -v ifconfig &>/dev/null; then
            local_ip=$(ifconfig "$iface" 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -1)
        fi
    fi
    
    echo "$local_ip"
}

test_gateway() {
    local gateway=$1
    if [ -n "$gateway" ]; then
        ping -c 1 -W 2 "$gateway" &>/dev/null
        return $?
    fi
    return 1
}

get_wireless_interface() {
    local iface=""
    
    if command -v iw &>/dev/null; then
        iface=$(iw dev 2>/dev/null | awk '/Interface/{print $2}' | head -1)
    fi
    
    if [ -z "$iface" ] && command -v ip &>/dev/null; then
        iface=$(ip link show 2>/dev/null | grep -o 'w[lp][a-z0-9]*' | head -1)
    fi
    
    if [ -z "$iface" ]; then
        iface=$(ls /sys/class/net/ 2>/dev/null | while read -r dev; do
            if [ -d "/sys/class/net/$dev/wireless" ]; then
                echo "$dev"
                break
            fi
        done)
    fi
    
    [ -z "$iface" ] && iface="wlan0"
    
    echo "$iface"
}

get_channel_width() {
    local iface=$(get_wireless_interface)
    
    if command -v iw &>/dev/null && [ -n "$iface" ]; then
        iw dev "$iface" info 2>/dev/null | grep -o "width: [0-9]*" | cut -d' ' -f2 | head -1
    else
        echo "20"
    fi
}

get_current_ssid() {
    local ssid=""
    
    if command -v nmcli &>/dev/null; then
        ssid=$(nmcli -t -f NAME,TYPE connection show --active 2>/dev/null | grep ':802-11-wireless' | cut -d: -f1 | head -1)
        
        if [ -z "$ssid" ]; then
            ssid=$(nmcli -t -f active,ssid dev wifi 2>/dev/null | grep '^yes' | cut -d: -f2 | head -1)
        fi
        
        if [ -z "$ssid" ]; then
            ssid=$(nmcli -t -f GENERAL.CONNECTION dev show 2>/dev/null | head -1 | cut -d: -f2)
        fi
    fi
    
    if [ -z "$ssid" ] && command -v iwgetid &>/dev/null; then
        ssid=$(iwgetid -r 2>/dev/null)
    fi
    
    if [ -z "$ssid" ] && command -v iw &>/dev/null; then
        local iface=$(get_wireless_interface)
        ssid=$(iw dev "$iface" link 2>/dev/null | grep 'SSID:' | cut -d: -f2 | sed 's/^[ \t]*//')
    fi
    
    echo "$ssid"
}

get_current_bssid() {
    local bssid=""
    
    if command -v nmcli &>/dev/null; then
        bssid=$(nmcli -t -f active,bssid dev wifi 2>/dev/null | grep '^yes' | cut -d: -f2 | head -1)
    fi
    
    if [ -z "$bssid" ] && command -v iw &>/dev/null; then
        local iface=$(get_wireless_interface)
        bssid=$(iw dev "$iface" link 2>/dev/null | grep 'Connected to' | awk '{print $3}')
    fi
    
    echo "$bssid"
}

get_current_channel() {
    local channel=""
    
    if command -v iwconfig &>/dev/null; then
        channel=$(iwconfig 2>/dev/null | grep -i 'channel' | head -1 | sed 's/.*Channel://' | awk '{print $1}')
    fi
    
    if [ -z "$channel" ] && command -v iw &>/dev/null; then
        local iface=$(get_wireless_interface)
        channel=$(iw dev "$iface" info 2>/dev/null | awk '/channel/{print $2}')
    fi
    
    if [ -z "$channel" ] && command -v nmcli &>/dev/null; then
        local ssid=$(get_current_ssid)
        if [ -n "$ssid" ]; then
            channel=$(nmcli -t -f SSID,CHAN dev wifi list 2>/dev/null | grep "^${ssid}:" | head -1 | cut -d: -f2)
        fi
    fi
    
    echo "$channel"
}

get_current_signal() {
    local signal=""
    
    if command -v nmcli &>/dev/null; then
        local ssid=$(get_current_ssid)
        if [ -n "$ssid" ]; then
            signal=$(nmcli -t -f SSID,SIGNAL dev wifi list 2>/dev/null | grep "^${ssid}:" | head -1 | cut -d: -f2)
        fi
    fi
    
    if [ -z "$signal" ] && command -v iwconfig &>/dev/null; then
        signal=$(iwconfig 2>/dev/null | grep -o "Signal level=-[0-9]*" | cut -d= -f2 | head -1)
    fi
    
    if [ -z "$signal" ] && command -v iw &>/dev/null; then
        local iface=$(get_wireless_interface)
        signal=$(iw dev "$iface" station dump 2>/dev/null | grep 'signal:' | awk '{print $2}')
    fi
    
    echo "$signal"
}

# Scan de redes
scan_networks() {
    > "$PARSED_FILE"
    
    if command -v nmcli &>/dev/null; then
        echo -e "  ${DIM}(Realizando scan... isso não afeta sua conexão Wi-Fi)${RESET}" >&2
        
        nmcli -t -f SSID,CHAN,SIGNAL dev wifi list --rescan yes 2>/dev/null | while IFS=: read -r ssid chan signal; do
            if [ -n "$chan" ] && [ "$ssid" != "--" ] && [ -n "$ssid" ]; then
                chan=$(echo "$chan" | tr -d ' ')
                echo "${chan}|${ssid}|${signal:-0}"
            fi
        done >> "$PARSED_FILE"
        
    elif command -v iwlist &>/dev/null; then
        local iface=$(get_wireless_interface)
        
        local scan_output
        scan_output=$(sudo iwlist "$iface" scan 2>/dev/null) || {
            echo -e "  ${RED}Erro ao escanear. Tente executar com sudo.${RESET}" >&2
            return 1
        }
        
        echo "$scan_output" | awk '
        BEGIN { chan=""; ssid=""; signal=0 }
        /Cell/ { 
            if (chan != "" && ssid != "") {
                print chan "|" ssid "|" signal
            }
            chan=""; ssid=""; signal=0
        }
        /Channel:/ { gsub(/[^0-9]/, "", $0); chan=$0 }
        /ESSID:/ { gsub(/.*ESSID:"/, ""); gsub(/".*/, ""); ssid=$0 }
        /Signal level=/ {
            match($0, /Signal level=(-[0-9]+)/, arr)
            signal = arr[1]
        }
        END {
            if (chan != "" && ssid != "") {
                print chan "|" ssid "|" signal
            }
        }
        ' >> "$PARSED_FILE"
    else
        echo -e "  ${RED}Erro: nenhuma ferramenta de scan Wi-Fi encontrada.${RESET}" >&2
        return 1
    fi
    
    if [ -s "$PARSED_FILE" ]; then
        sort -t'|' -k1,1 -k3,3nr "$PARSED_FILE" 2>/dev/null | awk -F'|' '!seen[$1"|"$2]++' > "$PARSED_FILE.tmp" 2>/dev/null
        mv "$PARSED_FILE.tmp" "$PARSED_FILE" 2>/dev/null
    fi
    
    return 0
}

# Calcular interferência
calculate_interference() {
    local channel=$1
    local interference=0
    
    for adj in $(seq $((channel - 2)) $((channel + 2))); do
        if [ $adj -ge 1 ] && [ $adj -le 11 ]; then
            local count=$(awk -F'|' -v c="$adj" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
            interference=$((interference + count))
        fi
    done
    
    echo "$interference"
}

congestion_bar() {
    local count=$1
    local bar=""
    local max_bars=8
    local filled=$((count * max_bars / 20))
    
    [ $filled -gt $max_bars ] && filled=$max_bars
    
    for ((i=0; i<max_bars; i++)); do
        if [ $i -lt $filled ]; then
            bar="${bar}█"
        else
            bar="${bar}░"
        fi
    done
    echo "$bar"
}

dbm_to_percent() {
    local dbm=$1
    if [[ ! "$dbm" =~ ^-?[0-9]+$ ]]; then
        echo "0"
        return
    fi
    
    local percent=$(( (dbm + 100) * 100 / 70 ))
    [ $percent -lt 0 ] && percent=0
    [ $percent -gt 100 ] && percent=100
    echo "$percent"
}

get_signal_color() {
    local signal=$1
    if [ $signal -ge 70 ]; then
        echo "${GREEN}"
    elif [ $signal -ge 40 ]; then
        echo "${YELLOW}"
    else
        echo "${RED}"
    fi
}

# Função para desenhar linha de separação da tabela
draw_table_line() {
    echo "  ┌────────┬────────┬────────────┬──────────────────────────────────┬─────────┐"
}

draw_table_header() {
    echo "  ├────────┼────────┼────────────┼──────────────────────────────────┼─────────┤"
}

draw_table_bottom() {
    echo "  └────────┴────────┴────────────┴──────────────────────────────────┴─────────┘"
}

# Modo JSON
output_json() {
    local timestamp=$(date -Iseconds)
    local channels_24=()
    local channels_5=()
    
    for ch in 1 2 3 4 5 6 7 8 9 10 11 12 13; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        local networks=$(awk -F'|' -v c="$ch" '$1==c {printf "{\"ssid\":\"%s\",\"signal\":%s},", $2, $3}' "$PARSED_FILE" 2>/dev/null | sed 's/,$//')
        [ -n "$networks" ] && networks="[$networks]" || networks="[]"
        channels_24+=("{\"channel\":$ch,\"networks_count\":$count,\"networks\":$networks}")
    done
    
    for ch in 36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            local networks=$(awk -F'|' -v c="$ch" '$1==c {printf "{\"ssid\":\"%s\",\"signal\":%s},", $2, $3}' "$PARSED_FILE" 2>/dev/null | sed 's/,$//')
            channels_5+=("{\"channel\":$ch,\"networks_count\":$count,\"networks\":[$networks]}")
        fi
    done
    
    local best_24=""
    local best_24_count=999
    for ch in 1 6 11; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        local interference=$(calculate_interference $ch)
        local total=$((count + interference/2))
        
        if [ $total -lt $best_24_count ]; then
            best_24_count=$total
            best_24=$ch
        fi
    done
    
    local best_5=""
    local best_5_count=999
    for ch in 36 40 44 48 52 56 60 64 149 153 157 161 165; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        if [ $count -lt $best_5_count ]; then
            best_5_count=$count
            best_5=$ch
        fi
    done
    
    cat <<EOF
{
  "timestamp": "$timestamp",
  "current_network": {
    "ssid": "$(get_current_ssid)",
    "bssid": "$(get_current_bssid)",
    "channel": "$(get_current_channel)",
    "signal": $(get_current_signal)
  },
  "channels_24ghz": [$(IFS=,; echo "${channels_24[*]}")],
  "channels_5ghz": [$(IFS=,; echo "${channels_5[*]}")],
  "recommendations": {
    "channel_24ghz": $best_24,
    "congestion_24ghz": $best_24_count,
    "channel_5ghz": ${best_5:-null},
    "congestion_5ghz": ${best_5_count:-0}
  }
}
EOF
}

# Modo CSV
output_csv() {
    echo "Timestamp,Channel,Band,Networks_Count,SSIDs,Signal_Strengths"
    
    local timestamp=$(date -Iseconds)
    
    for ch in 1 2 3 4 5 6 7 8 9 10 11 12 13; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            local ssids=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" 2>/dev/null | paste -sd ';' -)
            local signals=$(awk -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" 2>/dev/null | paste -sd ';' -)
            echo "$timestamp,$ch,2.4,$count,\"$ssids\",\"$signals\""
        fi
    done
    
    for ch in 36 40 44 48 52 56 60 64 149 153 157 161 165; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        if [ $count -gt 0 ]; then
            local ssids=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" 2>/dev/null | paste -sd ';' -)
            local signals=$(awk -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" 2>/dev/null | paste -sd ';' -)
            echo "$timestamp,$ch,5,$count,\"$ssids\",\"$signals\""
        fi
    done
}

show_detailed_analysis() {
    echo ""
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}Analise detalhada de interferencia (2.4 GHz)${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    printf "  %-8s %-12s %-12s %-12s %s\n" "Canal" "Redes" "Adjacentes" "Interf." "Qualidade"
    printf "  %-8s %-12s %-12s %-12s %s\n" "──────" "──────" "──────────" "──────" "─────────"
    
    for ch in 1 6 11; do
        local direct=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        local interference=$(calculate_interference $ch)
        local total_interference=$((interference - direct))
        local quality=""
        
        if [ $direct -eq 0 ]; then
            quality="${GREEN}EXCELENTE${RESET}"
        elif [ $direct -le 2 ] && [ $total_interference -le 2 ]; then
            quality="${GREEN}BOA${RESET}"
        elif [ $direct -le 4 ] && [ $total_interference -le 4 ]; then
            quality="${YELLOW}MODERADA${RESET}"
        else
            quality="${RED}CONGESTIONADA${RESET}"
        fi
        
        printf "  %-8d %-12d %-12d %-12d %b\n" "$ch" "$direct" "$((interference - direct))" "$interference" "$quality"
    done
    echo ""
    
    local best_interference=999
    local best_ch=""
    for ch in 1 6 11; do
        local interference=$(calculate_interference $ch)
        if [ $interference -lt $best_interference ]; then
            best_interference=$interference
            best_ch=$ch
        fi
    done
    
    echo -e "  ${CYAN}➜ Recomendacao baseada em interferencia: Canal ${BOLD}${best_ch}${RESET}${CYAN} (${best_interference} redes afetando)${RESET}"
    echo ""
}

show_router_info() {
    local gateway=$(get_default_gateway)
    local local_ip=$(get_local_ip)
    local interface=$(get_default_interface)
    local external_ip=$(curl -s --max-time 2 ifconfig.me 2>/dev/null)

    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}🌐 Informações de Rede${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""

    [ -n "$local_ip" ] && echo -e "  Seu IP Local:      ${CYAN}$local_ip${RESET}"
    if [ -n "$external_ip" ]; then
        echo -e "  Seu IP Externo:    ${CYAN}${BOLD}$external_ip${RESET}"
    else
        echo -e "  Seu IP Externo:    ${RED}Não detectado${RESET}"
    fi
    [ -n "$interface" ] && echo -e "  Interface:         ${CYAN}$interface${RESET}"

    if [ -n "$gateway" ]; then
        echo -e "  Gateway/Roteador:  ${GREEN}${BOLD}$gateway${RESET}"
        test_gateway "$gateway" && echo -e "  Status:            ${GREEN}✓ Acessível${RESET}" || echo -e "  Status:            ${RED}✗ Inacessível${RESET}"
    fi
    echo ""
}

wait_for_user() {
    echo ""
    echo -e "  ${DIM}Pressione ENTER para sair...${RESET}"
    read -r
}

# Função para imprimir tabela formatada
print_table_row() {
    local channel=$1
    local count=$2
    local bar=$3
    local names=$4
    local signals=$5
    local color=$6
    
    # Formatar cada coluna com largura fixa
    local ch_fmt=$(printf "%-6s" "$channel")
    local count_fmt=$(printf "%-6s" "$count")
    local bar_fmt=$(printf "%-10s" "$bar")
    local names_fmt=$(printf "%-32s" "$names")
    local signals_fmt=$(printf "%-7s" "$signals")
    
    printf "  ${color}%s  %s  %s  %s  %s${RESET}\n" "$ch_fmt" "$count_fmt" "$bar_fmt" "$names_fmt" "$signals_fmt"
}

# Modo principal interativo
main_interactive() {
    local current_ssid=$(get_current_ssid)
    local current_channel=$(get_current_channel)
    local current_signal=$(get_current_signal)
    local current_signal_percent=$(dbm_to_percent "$current_signal")
    local channel_width=$(get_channel_width)
    local gateway_ip=$(get_default_gateway)
    
    echo ""
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}Scanner de Canais Wi-Fi - Analise de Congestionamento${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    echo -e "  Escaneando redes Wi-Fi... (pode levar alguns segundos)"
    echo ""
    
    scan_networks
    local scan_result=$?
    
    if [ $scan_result -ne 0 ] || [ ! -s "$PARSED_FILE" ]; then
        echo -e "  ${RED}Nenhuma rede encontrada ou erro no scan.${RESET}"
        echo -e "  ${DIM}Verifique se o Wi-Fi esta ligado.${RESET}"
        return 1
    fi
    
    local total_networks=$(wc -l < "$PARSED_FILE" 2>/dev/null)
    echo -e "  ${DIM}Total de redes detectadas: ${total_networks}${RESET}"
    echo ""
    
    # -- Canais 2.4 GHz --
    echo -e "  ${BOLD}📡 Redes encontradas (2.4 GHz)${RESET}"
    echo ""
    
    # Cabeçalho da tabela com larguras fixas
    printf "  %-6s %-6s %-10s %-32s %-7s\n" "Canal" "Redes" "Congest." "SSIDs" "Sinal"
    printf "  %-6s %-6s %-10s %-32s %-7s\n" "─────" "─────" "────────" "────────────────────────────────" "─────"
    
    local best_24_ch=""
    local best_24_count=999
    local best_24_interference=999
    
    for ch in 1 2 3 4 5 6 7 8 9 10 11 12 13; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l | tr -d ' ')
        local interference=$(calculate_interference $ch)
        
        if [[ $ch =~ ^(1|6|11)$ ]]; then
            if [ $interference -lt $best_24_interference ]; then
                best_24_interference=$interference
                best_24_count=$count
                best_24_ch=$ch
            fi
        fi
        
        if [ "$count" -eq 0 ] && [[ ! $ch =~ ^(1|6|11)$ ]]; then
            continue
        fi
        
        local bar=$(congestion_bar "$count")
        local names=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" 2>/dev/null | head -3 | paste -sd ', ' -)
        local signals=$(awk -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" 2>/dev/null | head -3 | paste -sd ', ' -)
        
        # Destacar rede do usuário
        if [ -n "$current_ssid" ] && echo "$names" | grep -q "$current_ssid"; then
            names=$(echo "$names" | sed "s/$current_ssid/$(printf "${GREEN}${current_ssid}${RESET}")/")
        fi
        
        # Truncar nomes longos
        if [ ${#names} -gt 32 ]; then
            names="${names:0:29}..."
        fi
        
        # Definir cor baseada no congestionamento
        local color=""
        if [ "$count" -ge 8 ]; then
            color="${RED}"
        elif [ "$count" -ge 4 ]; then
            color="${YELLOW}"
        else
            color="${RESET}"
        fi
        
        # Imprimir linha formatada
        printf "  ${color}%-6s${RESET} ${color}%-6s${RESET} ${color}%-10s${RESET} %-32s %-7s\n" \
               "$ch" "$count" "$bar" "$names" "$signals"
        
        # Mostrar redes adicionais
        local extra_count=$((count - 3))
        if [ $extra_count -gt 0 ]; then
            echo -e "  ${DIM}                                          ... e mais $extra_count rede(s)${RESET}"
        fi
    done
    
    echo ""
    
    # -- Canais 5 GHz --
    local has_5ghz=false
    for ch in 36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165; do
        local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            has_5ghz=true
            break
        fi
    done
    
    if $has_5ghz; then
        echo -e "  ${BOLD}📡 Redes encontradas (5 GHz)${RESET}"
        echo ""
        printf "  %-6s %-6s %-10s %-32s %-7s\n" "Canal" "Redes" "Congest." "SSIDs" "Sinal"
        printf "  %-6s %-6s %-10s %-32s %-7s\n" "─────" "─────" "────────" "────────────────────────────────" "─────"
        
        local best_5_ch=""
        local best_5_count=999
        
        for ch in 36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165; do
            local count=$(awk -F'|' -v c="$ch" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
            
            if [ "$count" -eq 0 ]; then
                if [ -z "$best_5_ch" ] || [ 0 -lt $best_5_count ]; then
                    best_5_ch=$ch
                    best_5_count=0
                fi
                continue
            fi
            
            if [ "$count" -lt "$best_5_count" ] || [ -z "$best_5_ch" ]; then
                best_5_count=$count
                best_5_ch=$ch
            fi
            
            local bar=$(congestion_bar "$count")
            local names=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" 2>/dev/null | head -2 | paste -sd ', ' -)
            local signals=$(awk -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" 2>/dev/null | head -2 | paste -sd ', ' -)
            
            if [ -n "$current_ssid" ] && echo "$names" | grep -q "$current_ssid"; then
                names=$(echo "$names" | sed "s/$current_ssid/$(printf "${GREEN}${current_ssid}${RESET}")/")
            fi
            
            # Truncar nomes longos
            if [ ${#names} -gt 32 ]; then
                names="${names:0:29}..."
            fi
            
            printf "  %-6s %-6s %-10s %-32s %-7s\n" "$ch" "$count" "$bar" "$names" "$signals"
        done
        
        echo ""
    fi
    
    # -- Diagnóstico --
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}📊 Diagnóstico da Rede Atual${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    
    if [ -n "$current_ssid" ]; then
        local signal_color=$(get_signal_color "$current_signal_percent")
        echo -e "  SSID:            ${GREEN}${BOLD}$current_ssid${RESET}"
        echo -e "  Canal:           ${BOLD}$current_channel${RESET}"
        echo -e "  Sinal:           ${signal_color}${current_signal} dBm (${current_signal_percent}%)${RESET}"
        echo -e "  Largura do canal: ${channel_width} MHz"
        
        if [ -n "$current_channel" ]; then
            local current_count=$(awk -F'|' -v c="$current_channel" '$1==c' "$PARSED_FILE" 2>/dev/null | wc -l)
            local current_interference=$(calculate_interference "$current_channel")
            
            if [ "$current_count" -ge 8 ]; then
                echo -e "  Congestionamento: ${RED}CRITICO - ${current_count} redes no mesmo canal${RESET}"
            elif [ "$current_count" -ge 4 ]; then
                echo -e "  Congestionamento: ${YELLOW}ALTO - ${current_count} redes no mesmo canal${RESET}"
            elif [ "$current_count" -ge 2 ]; then
                echo -e "  Congestionamento: ${YELLOW}MODERADO - ${current_count} redes no mesmo canal${RESET}"
            else
                echo -e "  Congestionamento: ${GREEN}BAIXO - ${current_count} redes no mesmo canal${RESET}"
            fi
            
            if [ $current_interference -gt $((current_count * 2)) ]; then
                echo -e "  Interferência:    ${YELLOW}Alta interferência de canais adjacentes${RESET}"
            fi
        fi
    else
        echo -e "  ${YELLOW}⚠ Nenhuma rede Wi-Fi conectada detectada${RESET}"
        echo -e "  ${DIM}   (Você pode estar usando cabo Ethernet ou o Wi-Fi não está conectado)${RESET}"
        echo -e "  ${DIM}   As recomendacoes abaixo ainda são validas para configurar seu roteador${RESET}"
    fi
    
    echo ""
    
    show_router_info
    
    # -- Recomendações --
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}💡 Recomendações${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    
    if [ -n "$best_24_ch" ]; then
        if [ "$best_24_count" -eq 0 ]; then
            echo -e "  ✅ ${GREEN}Canal 2.4 GHz ideal: ${BOLD}${best_24_ch}${RESET}${GREEN} - COMPLETAMENTE LIVRE!${RESET}"
        else
            echo -e "  📶 ${GREEN}Canal 2.4 GHz recomendado: ${BOLD}${best_24_ch}${RESET}${GREEN} (${best_24_count} redes, ${best_24_interference} interferências)${RESET}"
        fi
    fi
    
    if [ -n "$best_5_ch" ]; then
        if [ "$best_5_count" -eq 0 ]; then
            echo -e "  ✅ ${GREEN}Canal 5 GHz ideal: ${BOLD}${best_5_ch}${RESET}${GREEN} - COMPLETAMENTE LIVRE!${RESET}"
        else
            echo -e "  📶 ${GREEN}Canal 5 GHz recomendado: ${BOLD}${best_5_ch}${RESET}${GREEN} (${best_5_count} redes)${RESET}"
        fi
    fi
    
    echo ""
    
    show_detailed_analysis
    
    echo -e "  ${BOLD}───────────────────────────────────────────────────────────${RESET}"
    echo ""
    
    if [ -n "$gateway_ip" ]; then
        echo -e "  ${DIM}📝 Para alterar o canal do roteador:${RESET}"
        echo -e "  ${DIM}   1. Abra o navegador e acesse: ${GREEN}http://$gateway_ip${RESET}"
        echo -e "  ${DIM}   2. Faça login (usuario/senha geralmente admin/admin ou ver etiqueta)${RESET}"
        echo -e "  ${DIM}   3. Vá em Configurações Wi-Fi → Canal${RESET}"
        echo -e "  ${DIM}   4. Selecione o canal recomendado e salve${RESET}"
    else
        echo -e "  ${DIM}📝 Para alterar o canal do roteador:${RESET}"
        echo -e "  ${DIM}   1. Descubra o IP do roteador com: ${GREEN}ip route | grep default${RESET}"
        echo -e "  ${DIM}   2. Acesse http://[IP_DO_ROTEADOR] no navegador${RESET}"
        echo -e "  ${DIM}   3. Faça login e vá em Configurações Wi-Fi → Canal${RESET}"
    fi
    
    echo ""
    echo -e "  ${DIM}💡 Dicas extras:${RESET}"
    echo -e "  ${DIM}   • Prefira 5 GHz se seus dispositivos suportarem${RESET}"
    echo -e "  ${DIM}   • Mantenha o roteador em local elevado e centralizado${RESET}"
    echo -e "  ${DIM}   • Evite obstáculos como paredes grossas e eletrodomésticos${RESET}"
    echo ""
}

# Modo contínuo
main_continuous() {
    echo -e "${BOLD}Modo contínuo - Atualizando a cada ${CONTINUOUS_INTERVAL} segundos${RESET}"
    echo -e "${DIM}Pressione Ctrl+C para sair${RESET}"
    echo ""
    
    while true; do
        clear
        main_interactive
        echo -e "${DIM}Próxima atualização em ${CONTINUOUS_INTERVAL} segundos...${RESET}"
        sleep "$CONTINUOUS_INTERVAL"
    done
}

# -- Main --
if [ "$JSON_MODE" = true ]; then
    scan_networks >/dev/null 2>&1
    output_json
    exit 0
fi

if [ "$CSV_MODE" = true ]; then
    scan_networks >/dev/null 2>&1
    output_csv
    exit 0
fi

if [ "$CONTINUOUS_MODE" = true ]; then
    main_continuous
else
    main_interactive
    wait_for_user
fi

exit 0
