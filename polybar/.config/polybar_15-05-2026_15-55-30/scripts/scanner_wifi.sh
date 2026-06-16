#!/bin/bash
# scanner_wifi.sh — Escaneia redes Wi-Fi e sugere o melhor canal (Linux)
# Uso: ./scanner_wifi.sh [--json] [--continuous [N]] [--csv]
# v2.0 — Refatorado: cache de chamadas, awk unificado, bugs corrigidos

# ── Cores ──────────────────────────────────────────────────────────────────────
GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'
BLUE='\033[1;34m';  CYAN='\033[1;36m';   BOLD='\033[1m'
DIM='\033[0;90m';   RESET='\033[0m'

# ── Temporários ────────────────────────────────────────────────────────────────
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT
PARSED_FILE="$TMPDIR_WORK/parsed.txt"

# ── Cache global (preenchido uma única vez em init_cache) ──────────────────────
_IFACE=""
_SSID=""
_BSSID=""
_CHANNEL=""
_SIGNAL=""
_SIGNAL_DBM=""   # sempre em dBm
_GATEWAY=""
_LOCAL_IP=""
_CHAN_WIDTH=""

# Array associativo: canal → contagem de redes
declare -A CHAN_COUNT

# ── Modos ──────────────────────────────────────────────────────────────────────
JSON_MODE=false; CONTINUOUS_MODE=false; CSV_MODE=false
CONTINUOUS_INTERVAL=5

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)       JSON_MODE=true;  shift ;;
        --continuous)
            CONTINUOUS_MODE=true
            if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                CONTINUOUS_INTERVAL="$2"; shift
            fi
            shift ;;
        --csv)        CSV_MODE=true;   shift ;;
        --help|-h)
            echo "Uso: $0 [opcoes]"
            echo "  --json              Saida em formato JSON"
            echo "  --continuous [N]    Modo contínuo (intervalo N segundos, padrão: 5)"
            echo "  --csv               Exportar para CSV"
            echo "  --help, -h          Esta ajuda"
            exit 0 ;;
        *) echo "Opção desconhecida: $1 (use --help)"; exit 1 ;;
    esac
done

# ══════════════════════════════════════════════════════════════════════════════
# CACHE — detecta tudo uma única vez, evitando subshells repetidos
# ══════════════════════════════════════════════════════════════════════════════
init_cache() {
    # Interface wireless
    if command -v iw &>/dev/null; then
        _IFACE=$(iw dev 2>/dev/null | awk '/Interface/{print $2; exit}')
    fi
    if [[ -z "$_IFACE" ]] && command -v ip &>/dev/null; then
        _IFACE=$(ip link show 2>/dev/null | grep -o 'w[lp][a-z0-9]*' | head -1)
    fi
    if [[ -z "$_IFACE" ]]; then
        _IFACE=$(ls /sys/class/net/ 2>/dev/null | while read -r d; do
            [[ -d "/sys/class/net/$d/wireless" ]] && { echo "$d"; break; }
        done)
    fi
    [[ -z "$_IFACE" ]] && _IFACE="wlan0"

    # Gateway e IP local (ip route — uma chamada só)
    if command -v ip &>/dev/null; then
        local route_info
        route_info=$(ip route 2>/dev/null)
        _GATEWAY=$(echo "$route_info" | awk '/default/{print $3; exit}')
        local iface_local
        iface_local=$(echo "$route_info" | awk '/default/{print $5; exit}')
        _LOCAL_IP=$(ip -4 addr show "$iface_local" 2>/dev/null \
                    | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
    elif command -v route &>/dev/null; then
        _GATEWAY=$(route -n 2>/dev/null | awk '/^0\.0\.0\.0/{print $2; exit}')
        local if2
        if2=$(route -n 2>/dev/null | awk '/^0\.0\.0\.0/{print $8; exit}')
        _LOCAL_IP=$(ifconfig "$if2" 2>/dev/null | awk '/inet /{print $2; exit}')
    fi

    # SSID / BSSID / Canal / Sinal — nmcli é mais confiável e faz tudo de uma vez
    if command -v nmcli &>/dev/null; then
        local wifi_info
        wifi_info=$(nmcli -t -f active,ssid,bssid,chan,signal dev wifi 2>/dev/null \
                    | grep '^yes:')
        if [[ -n "$wifi_info" ]]; then
            IFS=: read -r _ _SSID _BSSID _CHANNEL _SIGNAL <<< "$wifi_info"
            # nmcli 'signal' é 0-100 (percentual); converter para dBm aproximado
            # dBm ≈ (signal/2) - 100   [fórmula padrão RSSI Windows/nmcli]
            if [[ "$_SIGNAL" =~ ^[0-9]+$ ]]; then
                _SIGNAL_DBM=$(( (_SIGNAL / 2) - 100 ))
            fi
        fi
    fi

    # Fallback SSID
    if [[ -z "$_SSID" ]] && command -v iwgetid &>/dev/null; then
        _SSID=$(iwgetid -r 2>/dev/null)
    fi
    if [[ -z "$_SSID" ]] && command -v iw &>/dev/null; then
        _SSID=$(iw dev "$_IFACE" link 2>/dev/null | awk -F': ' '/SSID/{print $2}')
    fi

    # Fallback canal
    if [[ -z "$_CHANNEL" ]] && command -v iw &>/dev/null; then
        _CHANNEL=$(iw dev "$_IFACE" info 2>/dev/null | awk '/channel/{print $2; exit}')
    fi
    if [[ -z "$_CHANNEL" ]] && command -v iwconfig &>/dev/null; then
        _CHANNEL=$(iwconfig 2>/dev/null | grep -oP 'Channel:\K[0-9]+' | head -1)
    fi

    # Fallback sinal dBm
    if [[ -z "$_SIGNAL_DBM" ]]; then
        if command -v iwconfig &>/dev/null; then
            _SIGNAL_DBM=$(iwconfig 2>/dev/null | grep -oP 'Signal level=\K-[0-9]+' | head -1)
        fi
        if [[ -z "$_SIGNAL_DBM" ]] && command -v iw &>/dev/null; then
            _SIGNAL_DBM=$(iw dev "$_IFACE" station dump 2>/dev/null \
                          | awk '/signal:/{print $2; exit}')
        fi
        # Sinal percentual (0-100) vira dBm
        if [[ "$_SIGNAL_DBM" =~ ^[0-9]+$ ]]; then
            _SIGNAL_DBM=$(( (_SIGNAL_DBM / 2) - 100 ))
        fi
        # Percentual para exibição
        _SIGNAL="$_SIGNAL_DBM"
    fi

    # Largura do canal
    if command -v iw &>/dev/null; then
        _CHAN_WIDTH=$(iw dev "$_IFACE" info 2>/dev/null \
                     | grep -oP 'width: \K[0-9]+' | head -1)
    fi
    [[ -z "$_CHAN_WIDTH" ]] && _CHAN_WIDTH="20"
}

# ══════════════════════════════════════════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════════════════════════════════════════
scan_networks() {
    > "$PARSED_FILE"

    if command -v nmcli &>/dev/null; then
        echo -e "  ${DIM}(Realizando scan... não afeta sua conexão Wi-Fi)${RESET}" >&2
        nmcli -t -f SSID,CHAN,SIGNAL dev wifi list --rescan yes 2>/dev/null \
        | awk -F: 'NF>=3 && $1!="--" && $1!="" && $2~/^[0-9]+$/ {
            gsub(/ /,"",$2)
            print $2 "|" $1 "|" ($3+0)
          }' >> "$PARSED_FILE"

    elif command -v iwlist &>/dev/null; then
        local scan_out
        scan_out=$(sudo iwlist "$_IFACE" scan 2>/dev/null) || {
            echo -e "  ${RED}Erro ao escanear. Tente com sudo.${RESET}" >&2
            return 1
        }
        echo "$scan_out" | awk '
          BEGIN { ch=""; ss=""; sig=0 }
          /Cell/ {
              if (ch!="" && ss!="") print ch"|"ss"|"sig
              ch=""; ss=""; sig=0
          }
          /Channel:/ { gsub(/[^0-9]/,"",$0); ch=$0 }
          /ESSID:/   { gsub(/.*ESSID:"/,""); gsub(/".*$/,""); ss=$0 }
          /Signal level=/ { match($0,/Signal level=(-[0-9]+)/,a); sig=a[1] }
          END { if (ch!="" && ss!="") print ch"|"ss"|"sig }
        ' >> "$PARSED_FILE"
    else
        echo -e "  ${RED}Erro: nenhuma ferramenta de scan encontrada (nmcli/iwlist).${RESET}" >&2
        return 1
    fi

    # Deduplicar (maior sinal prevalece), ordenar por canal
    [[ -s "$PARSED_FILE" ]] && \
        sort -t'|' -k1,1n -k3,3rn "$PARSED_FILE" \
        | awk -F'|' '!seen[$1"|"$2]++' \
        > "$PARSED_FILE.tmp" && mv "$PARSED_FILE.tmp" "$PARSED_FILE"

    # Pré-computa contagem por canal (elimina awk repetitivo depois)
    CHAN_COUNT=()
    while IFS='|' read -r ch _ _; do
        (( CHAN_COUNT[$ch]++ )) || CHAN_COUNT[$ch]=1
    done < "$PARSED_FILE"

    return 0
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

# Interferência: soma de redes nos canais ch-2 .. ch+2
# Um único awk em vez de 5 subshells
calculate_interference() {
    local ch=$1
    local lo=$(( ch - 2 )); local hi=$(( ch + 2 ))
    [[ $lo -lt 1  ]] && lo=1
    [[ $hi -gt 13 ]] && hi=13
    local total=0
    for (( c=lo; c<=hi; c++ )); do
        (( total += ${CHAN_COUNT[$c]:-0} ))
    done
    echo "$total"
}

congestion_bar() {
    local count=$1 filled=$(( count * 8 / 20 )) bar=""
    [[ $filled -gt 8 ]] && filled=8
    for (( i=0; i<8; i++ )); do
        [[ $i -lt $filled ]] && bar+="█" || bar+="░"
    done
    echo "$bar"
}

# dBm → percentual (0–100), escala padrão: -100 dBm = 0%, -30 dBm = 100%
dbm_to_percent() {
    local dbm=$1
    [[ ! "$dbm" =~ ^-?[0-9]+$ ]] && echo 0 && return
    local pct=$(( (dbm + 100) * 100 / 70 ))
    (( pct < 0   )) && pct=0
    (( pct > 100 )) && pct=100
    echo "$pct"
}

signal_color() {
    local pct=$1
    if   (( pct >= 70 )); then echo "$GREEN"
    elif (( pct >= 40 )); then echo "$YELLOW"
    else                       echo "$RED"
    fi
}

test_gateway() {
    [[ -n "$1" ]] && ping -c1 -W2 "$1" &>/dev/null
}

# ══════════════════════════════════════════════════════════════════════════════
# SAÍDA JSON
# ══════════════════════════════════════════════════════════════════════════════
output_json() {
    local ts; ts=$(date -Iseconds)

    build_chan_json() {
        local -a chans=("$@")
        local first=true
        for ch in "${chans[@]}"; do
            local cnt=${CHAN_COUNT[$ch]:-0}
            $first || printf ","
            first=false
            local nets
            nets=$(awk -F'|' -v c="$ch" '$1==c {printf "{\"ssid\":\"%s\",\"signal\":%s},", $2, $3}' \
                   "$PARSED_FILE" 2>/dev/null | sed 's/,$//')
            printf '{"channel":%s,"networks_count":%s,"networks":[%s]}' "$ch" "$cnt" "$nets"
        done
    }

    # Melhor 2.4 GHz (canais não-sobrepostos: 1, 6, 11)
    local best24="" best24_int=9999
    for ch in 1 6 11; do
        local i; i=$(calculate_interference "$ch")
        if (( i < best24_int )); then best24_int=$i; best24=$ch; fi
    done

    # Melhor 5 GHz (menos redes)
    local best5="" best5_cnt=9999
    local chans5=( 36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165 )
    for ch in "${chans5[@]}"; do
        local cnt=${CHAN_COUNT[$ch]:-0}
        if (( cnt < best5_cnt )); then best5_cnt=$cnt; best5=$ch; fi
    done

    cat <<EOF
{
  "timestamp": "$ts",
  "current_network": {
    "ssid": "$_SSID",
    "bssid": "$_BSSID",
    "channel": "$_CHANNEL",
    "signal_dbm": ${_SIGNAL_DBM:-null}
  },
  "channels_24ghz": [$(build_chan_json {1..13})],
  "channels_5ghz": [$(build_chan_json "${chans5[@]}")],
  "recommendations": {
    "channel_24ghz": ${best24:-null},
    "interference_24ghz": $best24_int,
    "channel_5ghz": ${best5:-null},
    "congestion_5ghz": $best5_cnt
  }
}
EOF
}

# ══════════════════════════════════════════════════════════════════════════════
# SAÍDA CSV
# ══════════════════════════════════════════════════════════════════════════════
output_csv() {
    local ts; ts=$(date -Iseconds)
    echo "Timestamp,Channel,Band,Networks_Count,SSIDs,Signal_Strengths"

    process_band() {
        local band=$1; shift
        for ch in "$@"; do
            local cnt=${CHAN_COUNT[$ch]:-0}
            (( cnt == 0 )) && continue
            local ssids sigs
            ssids=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" | paste -sd';' -)
            sigs=$(awk  -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" | paste -sd';' -)
            echo "$ts,$ch,$band,$cnt,\"$ssids\",\"$sigs\""
        done
    }

    process_band "2.4" {1..13}
    process_band "5"   36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165
}

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISE DETALHADA (2.4 GHz — canais não-sobrepostos)
# ══════════════════════════════════════════════════════════════════════════════
show_detailed_analysis() {
    echo ""
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}Análise de interferência — 2.4 GHz (canais não-sobrepostos)${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    printf "  %-8s %-12s %-12s %-12s %s\n" "Canal" "Diretas" "Adjacentes" "Total" "Qualidade"
    printf "  %-8s %-12s %-12s %-12s %s\n" "──────" "───────" "──────────" "─────" "─────────"

    local best_ch="" best_int=9999
    for ch in 1 6 11; do
        local direct=${CHAN_COUNT[$ch]:-0}
        local total; total=$(calculate_interference "$ch")
        local adj=$(( total - direct ))
        local qual

        if   (( direct == 0 ));              then qual="${GREEN}EXCELENTE${RESET}"
        elif (( direct <= 2 && adj <= 2 ));  then qual="${GREEN}BOA${RESET}"
        elif (( direct <= 4 && adj <= 4 ));  then qual="${YELLOW}MODERADA${RESET}"
        else                                      qual="${RED}CONGESTIONADA${RESET}"
        fi

        printf "  %-8d %-12d %-12d %-12d %b\n" "$ch" "$direct" "$adj" "$total" "$qual"
        (( total < best_int )) && { best_int=$total; best_ch=$ch; }
    done

    echo ""
    echo -e "  ${CYAN}➜ Recomendação por interferência: Canal ${BOLD}${best_ch}${RESET}${CYAN} (${best_int} redes afetando)${RESET}"
    echo ""
}

# ══════════════════════════════════════════════════════════════════════════════
# INFO DO ROTEADOR
# ══════════════════════════════════════════════════════════════════════════════
show_router_info() {
    local ext_ip
    ext_ip=$(curl -s --max-time 3 https://ifconfig.me 2>/dev/null \
             || curl -s --max-time 3 https://api4.ipify.org 2>/dev/null)

    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}🌐 Informações de Rede${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    [[ -n "$_LOCAL_IP" ]] && echo -e "  IP Local:          ${CYAN}$_LOCAL_IP${RESET}"
    if [[ -n "$ext_ip" ]]; then
        echo -e "  IP Externo:        ${CYAN}${BOLD}$ext_ip${RESET}"
    else
        echo -e "  IP Externo:        ${RED}Não detectado${RESET}"
    fi
    [[ -n "$_IFACE"   ]] && echo -e "  Interface:         ${CYAN}$_IFACE${RESET}"
    if [[ -n "$_GATEWAY" ]]; then
        echo -e "  Gateway:           ${GREEN}${BOLD}$_GATEWAY${RESET}"
        test_gateway "$_GATEWAY" \
            && echo -e "  Status gateway:    ${GREEN}✓ Acessível${RESET}" \
            || echo -e "  Status gateway:    ${RED}✗ Inacessível${RESET}"
    fi
    echo ""
}

# ══════════════════════════════════════════════════════════════════════════════
# MODO INTERATIVO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
main_interactive() {
    local sig_pct; sig_pct=$(dbm_to_percent "$_SIGNAL_DBM")

    echo ""
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}Scanner de Canais Wi-Fi — Análise de Congestionamento${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""
    echo -e "  Escaneando redes Wi-Fi... (pode levar alguns segundos)"
    echo ""

    scan_networks || return 1

    local total_nets; total_nets=$(wc -l < "$PARSED_FILE")
    echo -e "  ${DIM}Total de redes detectadas: ${total_nets}${RESET}"
    echo ""

    # ── 2.4 GHz ──────────────────────────────────────────────────────────────
    echo -e "  ${BOLD}📡 Redes encontradas — 2.4 GHz${RESET}"
    echo ""
    printf "  %-6s %-6s %-10s %-32s %s\n" "Canal" "Redes" "Congest." "SSIDs" "Sinal(dBm)"
    printf "  %-6s %-6s %-10s %-32s %s\n" "─────" "─────" "────────" "────────────────────────────────" "──────────"

    local best24="" best24_int=9999

    for ch in {1..13}; do
        local cnt=${CHAN_COUNT[$ch]:-0}
        local interf; interf=$(calculate_interference "$ch")

        # Determinar melhor canal não-sobreposto
        if [[ $ch =~ ^(1|6|11)$ ]] && (( interf < best24_int )); then
            best24_int=$interf; best24=$ch
        fi

        # Omitir canais sem redes que não são os não-sobrepostos
        (( cnt == 0 )) && [[ ! $ch =~ ^(1|6|11)$ ]] && continue

        local bar; bar=$(congestion_bar "$cnt")
        local names sigs
        names=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" | head -3 | paste -sd', ' -)
        sigs=$(awk  -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" | head -3 | paste -sd', ' -)

        # Destacar SSID atual
        [[ -n "$_SSID" ]] && names=$(echo "$names" \
            | sed "s/${_SSID}/$(printf "${GREEN}${_SSID}${RESET}")/g")

        # Truncar
        (( ${#names} > 32 )) && names="${names:0:29}..."

        local color=""
        (( cnt >= 8 )) && color="$RED"
        (( cnt >= 4 && cnt < 8 )) && color="$YELLOW"

        printf "  ${color}%-6s %-6s %-10s${RESET} %-32s %s\n" \
               "$ch" "$cnt" "$bar" "$names" "$sigs"

        local extra=$(( cnt - 3 ))
        (( extra > 0 )) && \
            echo -e "  ${DIM}$(printf '%56s' '') ... e mais $extra rede(s)${RESET}"
    done

    echo ""

    # ── 5 GHz ────────────────────────────────────────────────────────────────
    local chans5=( 36 40 44 48 52 56 60 64 100 104 108 112 116 120 124 128 132 136 140 149 153 157 161 165 )
    local has5=false best5="" best5_cnt=9999

    for ch in "${chans5[@]}"; do
        (( ${CHAN_COUNT[$ch]:-0} > 0 )) && has5=true && break
    done

    if $has5; then
        echo -e "  ${BOLD}📡 Redes encontradas — 5 GHz${RESET}"
        echo ""
        printf "  %-6s %-6s %-10s %-32s %s\n" "Canal" "Redes" "Congest." "SSIDs" "Sinal(dBm)"
        printf "  %-6s %-6s %-10s %-32s %s\n" "─────" "─────" "────────" "────────────────────────────────" "──────────"

        for ch in "${chans5[@]}"; do
            local cnt=${CHAN_COUNT[$ch]:-0}

            # Bug corrigido: melhor canal é o com MENOS redes (incluindo 0)
            if (( cnt < best5_cnt )); then
                best5_cnt=$cnt; best5=$ch
            fi

            (( cnt == 0 )) && continue

            local bar; bar=$(congestion_bar "$cnt")
            local names sigs
            names=$(awk -F'|' -v c="$ch" '$1==c {print $2}' "$PARSED_FILE" | head -2 | paste -sd', ' -)
            sigs=$(awk  -F'|' -v c="$ch" '$1==c {print $3}' "$PARSED_FILE" | head -2 | paste -sd', ' -)

            [[ -n "$_SSID" ]] && names=$(echo "$names" \
                | sed "s/${_SSID}/$(printf "${GREEN}${_SSID}${RESET}")/g")
            (( ${#names} > 32 )) && names="${names:0:29}..."

            printf "  %-6s %-6s %-10s %-32s %s\n" "$ch" "$cnt" "$bar" "$names" "$sigs"
        done
        echo ""
    fi

    # ── Diagnóstico ──────────────────────────────────────────────────────────
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}📊 Diagnóstico da Rede Atual${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""

    if [[ -n "$_SSID" ]]; then
        local sc; sc=$(signal_color "$sig_pct")
        echo -e "  SSID:              ${GREEN}${BOLD}$_SSID${RESET}"
        echo -e "  Canal:             ${BOLD}${_CHANNEL:-N/D}${RESET}"
        echo -e "  Sinal:             ${sc}${_SIGNAL_DBM} dBm (${sig_pct}%)${RESET}"
        echo -e "  Largura do canal:  ${_CHAN_WIDTH} MHz"

        if [[ -n "$_CHANNEL" ]]; then
            local cur_cnt=${CHAN_COUNT[$_CHANNEL]:-0}
            local cur_interf; cur_interf=$(calculate_interference "$_CHANNEL")
            local cong_msg cong_color

            if   (( cur_cnt >= 8 )); then cong_color="$RED";    cong_msg="CRÍTICO"
            elif (( cur_cnt >= 4 )); then cong_color="$YELLOW";  cong_msg="ALTO"
            elif (( cur_cnt >= 2 )); then cong_color="$YELLOW";  cong_msg="MODERADO"
            else                          cong_color="$GREEN";   cong_msg="BAIXO"
            fi

            echo -e "  Congestionamento:  ${cong_color}${cong_msg} — ${cur_cnt} rede(s) no mesmo canal${RESET}"
            (( cur_interf > cur_cnt * 2 )) && \
                echo -e "  Interferência:     ${YELLOW}Alta interferência de canais adjacentes${RESET}"
        fi
    else
        echo -e "  ${YELLOW}⚠  Nenhuma rede Wi-Fi conectada detectada${RESET}"
        echo -e "  ${DIM}   (Ethernet ou Wi-Fi desligado — recomendações abaixo ainda são válidas)${RESET}"
    fi

    echo ""
    show_router_info

    # ── Recomendações ─────────────────────────────────────────────────────────
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "  ${BOLD}💡 Recomendações${RESET}"
    echo -e "  ${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo ""

    if [[ -n "$best24" ]]; then
        if (( ${CHAN_COUNT[$best24]:-0} == 0 )); then
            echo -e "  ✅ ${GREEN}Canal 2.4 GHz ideal: ${BOLD}${best24}${RESET}${GREEN} — COMPLETAMENTE LIVRE!${RESET}"
        else
            echo -e "  📶 ${GREEN}Canal 2.4 GHz recomendado: ${BOLD}${best24}${RESET}${GREEN} (interferência total: ${best24_int})${RESET}"
        fi
    fi

    if [[ -n "$best5" ]]; then
        if (( best5_cnt == 0 )); then
            echo -e "  ✅ ${GREEN}Canal 5 GHz ideal: ${BOLD}${best5}${RESET}${GREEN} — COMPLETAMENTE LIVRE!${RESET}"
        else
            echo -e "  📶 ${GREEN}Canal 5 GHz recomendado: ${BOLD}${best5}${RESET}${GREEN} (${best5_cnt} rede(s) no canal)${RESET}"
        fi
    fi

    echo ""
    show_detailed_analysis

    echo -e "  ${BOLD}───────────────────────────────────────────────────────────${RESET}"
    echo ""

    local gw_hint="${_GATEWAY:-[IP do roteador]}"
    echo -e "  ${DIM}📝 Para alterar o canal no roteador:${RESET}"
    if [[ -n "$_GATEWAY" ]]; then
        echo -e "  ${DIM}   1. Acesse: ${GREEN}http://$_GATEWAY${RESET}"
    else
        echo -e "  ${DIM}   1. Descubra o IP: ${GREEN}ip route | grep default${RESET}"
        echo -e "  ${DIM}      Depois acesse: http://[IP_DO_ROTEADOR]${RESET}"
    fi
    echo -e "  ${DIM}   2. Login (geralmente admin/admin ou ver etiqueta do roteador)${RESET}"
    echo -e "  ${DIM}   3. Configurações Wi-Fi → Canal → selecione o recomendado → Salvar${RESET}"
    echo ""
    echo -e "  ${DIM}💡 Dicas:${RESET}"
    echo -e "  ${DIM}   • Prefira 5 GHz — menor alcance, porém muito menos interferência${RESET}"
    echo -e "  ${DIM}   • Posicione o roteador em local elevado e centralizado${RESET}"
    echo -e "  ${DIM}   • Evite paredes grossas, microondas e telefones sem fio${RESET}"
    echo ""
}

# ══════════════════════════════════════════════════════════════════════════════
# MODO CONTÍNUO
# ══════════════════════════════════════════════════════════════════════════════
main_continuous() {
    echo -e "${BOLD}Modo contínuo — atualizando a cada ${CONTINUOUS_INTERVAL}s${RESET}"
    echo -e "${DIM}Ctrl+C para sair${RESET}"
    while true; do
        clear
        init_cache
        main_interactive
        echo -e "${DIM}Próxima atualização em ${CONTINUOUS_INTERVAL}s...${RESET}"
        sleep "$CONTINUOUS_INTERVAL"
    done
}

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
init_cache   # detecta interface, gateway, SSID, canal, sinal — uma única vez

if   $JSON_MODE;       then scan_networks >/dev/null 2>&1; output_json; exit 0
elif $CSV_MODE;        then scan_networks >/dev/null 2>&1; output_csv;  exit 0
elif $CONTINUOUS_MODE; then main_continuous
else
    main_interactive
    echo -e "  ${DIM}Pressione ENTER para sair...${RESET}"
    read -r
fi

exit 0
