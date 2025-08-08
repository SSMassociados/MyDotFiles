#!/usr/bin/env bash

# 1) IP que a internet vê
public_ip=$(curl -s ipinfo.io/ip)

# 2) Descobre a interface de saída e seu IP local
iface=$(ip route get 1.1.1.1 2>/dev/null | awk '/dev/ {for(i=1;i<NF;i++) if($i=="dev") print $(i+1)}')
local_ip=$(ip -4 addr show dev "$iface" \
           | awk '/inet/ { sub(/\/.*/,"",$2); print $2 }' \
           | head -n1)

echo "→ IP público (internet): $public_ip"
echo "→ IP local   (sua máquina): $local_ip"
echo

# 3) Função para checar faixa
in_cgnat() {
  # devolve 0 (verdadeiro) se estiver em 100.64.0.0/10
  python3 - <<PYTHON
import ipaddress
ip = ipaddress.ip_address("$1")
print(ip in ipaddress.ip_network("100.64.0.0/10"))
PYTHON
}

in_priv() {
  # checa RFC1918
  [[ "$1" =~ ^10\. ]]   && return 0
  [[ "$1" =~ ^192\.168\. ]] && return 0
  [[ "$1" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]] && return 0
  return 1
}

# 4) Classificação
if in_priv "$local_ip"; then
  echo "🟡 Você está atrás de um NAT doméstico (RFC1918)."
elif [[ $(in_cgnat "$public_ip") == "True" ]]; then
  echo "🟠 Seu IP público está em 100.64.0.0/10 → **CGNAT de operadora**."
elif ! in_priv "$public_ip"; then
  echo "🟢 Você tem um IP público de verdade!"
else
  echo "⚪️ Caso especial – investigue manualmente."
fi
