#!/bin/bash

# Função para verificar se o IP é IPv4 ou IPv6
check_ip_type() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "IPv4"
    elif [[ $ip =~ ^[0-9a-fA-F:]+$ ]] && [[ $(grep -o ":" <<< "$ip" | wc -l) -ge 2 ]]; then
        echo "IPv6"
    else
        echo "Invalid"
    fi
}

# Função para converter IP para número para comparação (IPv4)
ip_to_int() {
    local ip=$1
    IFS='.' read -r a b c d <<< "$ip"
    echo $(( (a<<24) + (b<<16) + (c<<8) + d ))
}

# Função para verificar se IPv4 está em uma faixa específica
in_range() {
    local ip=$1
    local start=$2
    local end=$3
    local ip_int=$(ip_to_int "$ip")
    local start_int=$(ip_to_int "$start")
    local end_int=$(ip_to_int "$end")
    [[ $ip_int -ge $start_int && $ip_int -le $end_int ]]
}

# Função para classificar IPv4
classify_ipv4() {
    local ip=$1

    # Faixas de IPs privados
    if in_range "$ip" "10.0.0.0" "10.255.255.255"; then
        echo "Private (RFC 1918 - Class A)"
    elif in_range "$ip" "172.16.0.0" "172.31.255.255"; then
        echo "Private (RFC 1918 - Class B)"
    elif in_range "$ip" "192.168.0.0" "192.168.255.255"; then
        echo "Private (RFC 1918 - Class C)"
    # Faixa APIPA
    elif in_range "$ip" "169.254.0.0" "169.254.255.255"; then
        echo "Private (APIPA - Link-Local)"
    # Faixa CGNAT
    elif in_range "$ip" "100.64.0.0" "100.127.255.255"; then
        echo "CGNAT (RFC 6598)"
    # Outros IPs reservados
    elif in_range "$ip" "127.0.0.0" "127.255.255.255"; then
        echo "Private (Loopback)"
    elif in_range "$ip" "0.0.0.0" "0.255.255.255"; then
        echo "Reserved (Invalid)"
    elif in_range "$ip" "224.0.0.0" "239.255.255.255"; then
        echo "Reserved (Multicast)"
    elif in_range "$ip" "240.0.0.0" "255.255.255.255"; then
        echo "Reserved (Future Use)"
    else
        echo "Public"
    fi
}

# Função para classificar IPv6
classify_ipv6() {
    local ip=$1
    # Normaliza o IP (expande abreviações)
    ip=$(ip -6 addr show 2>/dev/null | grep -oE "([0-9a-fA-F:]+/128)" | grep "$ip" | cut -d'/' -f1 || echo "$ip")

    # Faixas IPv6
    if [[ $ip =~ ^::1$ ]]; then
        echo "Private (Loopback)"
    elif [[ $ip =~ ^fe80: ]]; then
        echo "Private (Link-Local)"
    elif [[ $ip =~ ^fc00:|^fd ]]; then
        echo "Private (Unique Local Address)"
    elif [[ $ip =~ ^ff ]]; then
        echo "Reserved (Multicast)"
    elif [[ $ip =~ ^::/128$ ]]; then
        echo "Reserved (Unspecified)"
    else
        echo "Public"
    fi
}

# Main
if [ -z "$1" ]; then
    echo "Uso: $0 <endereço_IP>"
    exit 1
fi

ip=$1
ip_type=$(check_ip_type "$ip")

case $ip_type in
    "IPv4")
        if [[ ! $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            echo "Erro: IP IPv4 inválido."
            exit 1
        fi
        result=$(classify_ipv4 "$ip")
        echo "IP: $ip ($ip_type) - $result"
        ;;
    "IPv6")
        result=$(classify_ipv6 "$ip")
        echo "IP: $ip ($ip_type) - $result"
        ;;
    "Invalid")
        echo "Erro: Endereço IP inválido."
        exit 1
        ;;
esac

exit 0
