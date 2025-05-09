#!/bin/bash

# Define o caminho para a imagem de plano de fundo
wallpaper_path="~/.wallpaper"

# Comando xidlehook com os parâmetros desejados
xidlehook \
  --not-when-fullscreen \  # Não ativa quando um aplicativo está em tela cheia
  --not-when-audio \       # Não ativa quando o áudio está sendo reproduzido
  --timer normal \         # Define o tipo de temporizador como "normal"
  --timer-once \           # Especifica que o temporizador será executado apenas uma vez após o tempo ocioso definido
  --idle-time 120 \        # Define o tempo ocioso em segundos (120 segundos ou 2 minutos)
  "betterlockscreen -u $wallpaper_path -l dimblur" \  # Comando a ser executado quando o temporizador normal expirar. Neste caso, bloqueia a tela com o efeito dimblur, usando a imagem especificada como plano de fundo
  "" \                     # Comando a ser executado quando o temporizador normal for interrompido manualmente
  --timer 90 \             # Define um segundo temporizador de 90 segundos
  "systemctl suspend" \    # Comando a ser executado quando o segundo temporizador expirar. Neste caso, suspende o sistema
  ""                       # Comando a ser executado quando o segundo temporizador for interrompido manualmente
