#!/bin/bash

# Diretório onde o djmount será montado
MOUNT_DIR="$HOME/UPnP"
NOTIFICATION_TAG="djmount-notification"

# Verifica se as dependências estão disponíveis
for cmd in djmount fusermount notify-send; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "Erro: O comando '$cmd' não foi encontrado. Instale-o e tente novamente."
        exit 1
    fi
done

# Verifica se o diretório existe; se não, cria
if [ ! -d "$MOUNT_DIR" ]; then
    mkdir -p "$MOUNT_DIR" || {
        notify-send -h "string:x-dunst-stack-tag:$NOTIFICATION_TAG" "Djmount" "Erro ao criar o diretório $MOUNT_DIR"
        exit 1
    }
    chmod 755 "$MOUNT_DIR"
    notify-send -h "string:x-dunst-stack-tag:$NOTIFICATION_TAG" "Djmount" "Diretório $MOUNT_DIR criado"
fi

# Verifica se o diretório está montado
if mountpoint -q "$MOUNT_DIR"; then
    # Se estiver montado, desmonta
    fusermount -u "$MOUNT_DIR" || {
        notify-send -h "string:x-dunst-stack-tag:$NOTIFICATION_TAG" "Djmount" "Erro ao desmontar $MOUNT_DIR"
        exit 1
    }
    notify-send -h "string:x-dunst-stack-tag:$NOTIFICATION_TAG" "Djmount" "🔴 Desmontado de $MOUNT_DIR"
else
    # Se não estiver montado, monta
    djmount "$MOUNT_DIR" || {
        notify-send -h "string:x-dunst-stack-tag:$NOTIFICATION_TAG" "Djmount" "Erro ao montar em $MOUNT_DIR"
        exit 1
    }
    notify-send -h "string:x-dunst-stack-tag:$NOTIFICATION_TAG" "Djmount" "🟢 Montado em $MOUNT_DIR"
fi
