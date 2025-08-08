#!/bin/bash

# Função para verificar o tipo de IP
check_ip_type() {
    local ip="$1"
    local ip_type="$2"

    # Faixas de IPs privados
    local -a ipv4_private=(
        "10.0.0.0/8" "172.16.0.0/12" "192.168.0.0/16" 
        "100.64.0.0/10" "169.254.0.0/16"
    )
    
    local -a ipv6_private=(
        "fc00::/7" "fe80::/10" "::1/128"
    )

    # Verifica IPv4
    if [[ "$ip_type" == "ipv4" ]]; then
        if [[ ! "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "❌ IPv4 inválido"
            return 1
        fi

        for range in "${ipv4_private[@]}"; do
            local network=${range%/*}
            local mask=${range#*/}
            
            if [[ $(ipcalc -n "$ip/$mask" | cut -d'=' -f2) == "$network" ]]; then
                case "$range" in
                    "100.64.0.0/10") echo "🔵 CGNAT" ;;
                    "169.254.0.0/16") echo "🟡 Link-local" ;;
                    *) echo "🟢 Privado" ;;
                esac
                return 0
            fi
        done
        echo "🌍 Público"

    # Verifica IPv6
    elif [[ "$ip_type" == "ipv6" ]]; then
        if [[ ! "$ip" =~ ^[0-9a-fA-F:]+$ ]]; then
            echo "❌ IPv6 inválido"
            return 1
        fi

        for range in "${ipv6_private[@]}"; do
            local network=${range%/*}
            if [[ "$ip" == "$network"* ]]; then
                case "$range" in
                    "fc00::/7") echo "🟢 ULA" ;;
                    "fe80::/10") echo "🟡 Link-local" ;;
                    "::1/128") echo "🔴 Loopback" ;;
                esac
                return 0
            fi
        done
        echo "🌍 Público"
    fi
}

# Verifica dependências
check_deps() {
    local missing=()
    for cmd in ip grep awk cut curl; do
        if ! command -v $cmd &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "❌ Dependências faltando: ${missing[*]}"
        echo "Instale com: sudo pacman -S ${missing[*]}"
        exit 1
    fi
}

# Main
clear
check_deps

echo -e "\n🔎 IPs Locais:"

# IPv4
ipv4=$(ip -4 a | grep -w 'inet' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -n1)
if [[ -n "$ipv4" ]]; then
    echo -e "- IPv4: $ipv4 \t→ $(check_ip_type "$ipv4" "ipv4")"
else
    echo "❌ IPv4 não detectado"
fi

# IPv6 (mostra todos os não-link-local)
echo -e "\n🔦 IPv6 Detectados:"
ip -6 a | grep -w 'inet6' | awk '{print $2}' | cut -d'/' -f1 | while read ipv6; do
    if [[ "$ipv6" != "::1" ]]; then
        echo -e "- $ipv6 \t→ $(check_ip_type "$ipv6" "ipv6")"
    fi
done

# Teste CGNAT
echo -e "\n🔍 Testes Especiais:"
echo -e "1. 100.64.1.1 \t→ $(check_ip_type "100.64.1.1" "ipv4") (CGNAT)"
echo -e "2. 192.168.1.1 \t→ $(check_ip_type "192.168.1.1" "ipv4") (Privado)"
echo -e "3. 2001:db8::1 \t→ $(check_ip_type "2001:db8::1" "ipv6") (Público de exemplo)"

# IPs Públicos
echo -e "\n🌐 IPs Públicos:"
public_ipv4=$(curl -4 -s ifconfig.me 2>/dev/null)
if [[ -n "$public_ipv4" ]]; then
    echo -e "- IPv4: $public_ipv4 \t↔ NAT: $([[ "$ipv4" != "$public_ipv4" ]] && echo "✅" || echo "❌")"
else
    echo "❌ IPv4 público não detectado"
fi

public_ipv6=$(curl -6 -s ifconfig.me 2>/dev/null)
if [[ -n "$public_ipv6" ]]; then
    echo -e "- IPv6: $public_ipv6 \t↔ NAT: $([[ "$(ip -6 a | grep -w 'inet6' | grep -v 'fe80::' | awk '{print $2}' | cut -d'/' -f1 | head -n1)" != "$public_ipv6" ]] && echo "⚠️" || echo "✅")"
else
    echo "ℹ️ IPv6 público não detectado (normal se não houver suporte)"
fi

echo -e "\n💡 Dica: Se não vê IPv6, verifique:"
echo "1. Suporte do provedor (ipv6.br)"
echo "2. 'ip -6 a' para ver todos os endereços"
echo "3. 'sysctl net.ipv6.conf.all.disable_ipv6=0' para habilitar"
