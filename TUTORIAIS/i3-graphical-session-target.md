# i3wm + systemd-user: ativando o graphical-session.target

> **Problema:** o i3wm não declara formalmente uma sessão gráfica para o
> systemd-user. O `graphical-session.target` fica `inactive (dead)` mesmo
> com o i3 rodando, o que faz serviços de usuário com
> `WantedBy=graphical-session.target` (dunst, picom, waybar, etc.) falharem
> silenciosamente.

---

## 1. Permitir start manual do target

Por padrão o `graphical-session.target` recusa inicialização manual.
Crie um drop-in para liberar isso:

```bash
mkdir -p ~/.config/systemd/user/graphical-session.target.d
```

```ini
# ~/.config/systemd/user/graphical-session.target.d/override.conf
[Unit]
RefuseManualStart=no
```

---

## 2. Configurar o ~/.xprofile

O `.xprofile` é executado pelo display manager (LightDM, SDDM, GDM) antes
da sessão gráfica iniciar. Ele deve: exportar variáveis de ambiente,
propagá-las para o systemd-user e o DBus, e então ativar o target.

```bash
#!/bin/bash
# ==============================================================
# ~/.xprofile
# Executado pelo display manager (GDM, LightDM, SDDM) antes
# da sessão gráfica iniciar. Não use 'set -e' aqui: uma falha
# isolada não deve impedir o login.
# ==============================================================

# ── Variáveis de ambiente do i3 ───────────────────────────────
[ -f "$HOME/.config/i3/env.sh" ] && . "$HOME/.config/i3/env.sh"

# ── PATH ──────────────────────────────────────────────────────
export PATH="$PATH:$HOME/.local/bin"
export PATH="$PATH:$HOME/.config/i3/scripts"
export PATH="$PATH:$HOME/.config/polybar/scripts"
export PATH="$PATH:$HOME/.config/Thunar/scripts"

# ── IBUS ──────────────────────────────────────────────────────
ibus-daemon -drxR

# ── GTK: sincroniza GTK3 → GTK4 a cada login ─────────────────
# Garante que apps GTK4 herdem tema, fonte e cursor do GTK3.
# exit 0 interno: falha aqui nunca trava o login.
"$HOME/.config/i3/scripts/sync_gtk3_to_gtk4.sh"

# ── Exporta variáveis para systemd-user e DBus ────────────────
systemctl --user import-environment \
    DISPLAY \
    XAUTHORITY \
    XDG_CURRENT_DESKTOP \
    XDG_SESSION_TYPE \
    XDG_SESSION_DESKTOP \
    DESKTOP_SESSION \
    QT_QPA_PLATFORMTHEME

dbus-update-activation-environment --systemd \
    DISPLAY \
    XAUTHORITY \
    XDG_CURRENT_DESKTOP \
    XDG_SESSION_TYPE \
    XDG_SESSION_DESKTOP \
    DESKTOP_SESSION \
    QT_QPA_PLATFORMTHEME

# ── Declara sessão gráfica para o systemd-user ────────────────
systemctl --user start graphical-session.target
```

> **Ordem importa:** o `import-environment` e `dbus-update-activation-environment`
> devem vir **antes** do `start`, para que os serviços ativados pelo target
> já encontrem as variáveis disponíveis.

---

## 3. Configurar as variáveis de ambiente do i3

Crie (ou mantenha) o arquivo `~/.config/i3/env.sh` com as variáveis que
identificam a sessão:

```bash
#!/bin/bash
# ==========================
# Ambiente gráfico do i3wm
# ==========================

# Monitor
export FALLBACK_MONITOR="eDP1"

# Locale
export LANG=pt_BR.UTF-8

# Qt
export QT_QPA_PLATFORMTHEME=qt6ct
export QT_AUTO_SCREEN_SCALE_FACTOR=1
# Mantenha o WPS usando Noto Sans - wrapper
export QT_FONT_OVERRIDE="Noto Sans,12,-1,5,50,0,0,0,0,0"

# IBUS (input method)
export GTK_IM_MODULE=ibus
export QT_IM_MODULE=ibus
export XMODIFIERS=@im=ibus
export SDL_IM_MODULE=ibus

# Sessão e ambiente (essenciais para o systemd-user reconhecer o i3)
export XDG_CURRENT_DESKTOP=i3
export XDG_SESSION_TYPE=x11
export XDG_SESSION_DESKTOP=i3
export DESKTOP_SESSION=i3
```

---

## 4. Parar o target ao sair do i3

O target deve ser encerrado quando a sessão gráfica termina.
Ajuste os pontos de saída do i3:

**No `~/.config/i3/config`** (binding de logout):
```
$ss+e $exe systemctl --user stop graphical-session.target && i3-msg exit
```

**Na polybar** (se usar powermenu):
```ini
menu-0-2-exec = systemctl --user stop graphical-session.target && i3-msg exit
```

> Para `reboot`, `poweroff` e `suspend` não é necessário: o systemd encerra
> a sessão de usuário automaticamente nesses casos.

---

## 5. Criar serviço âncora para manter o target ativo

O `graphical-session.target` tem `StopWhenUnneeded=yes` — ele para sozinho
quando nenhum serviço o está segurando. Isso faz o `xdg-desktop-portal` falhar
porque usa `Requisite=graphical-session.target` (exige ativo no momento do start,
mas não o inicia). A solução é um serviço âncora atrelado ao `default.target`:

```bash
# ~/.config/systemd/user/graphical-session-anchor.service
[Unit]
Description=Keep graphical-session.target active
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=oneshot
ExecStart=/usr/bin/true
RemainAfterExit=yes

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now graphical-session-anchor.service
```

> O âncora sobe junto com a sessão de usuário via `default.target`, puxa o
> `graphical-session.target` via `Wants=`, e o mantém ativo com
> `RemainAfterExit=yes` — impedindo que o `StopWhenUnneeded` o derrube.

---

## 6. Verificar se está funcionando

```bash
# Todos devem mostrar: active
systemctl --user is-active graphical-session.target
systemctl --user is-active graphical-session-anchor.service
systemctl --user is-active xdg-desktop-portal.service

# Confirmar que as variáveis chegaram ao systemd-user
systemctl --user show-environment | grep -E 'DISPLAY|XAUTHORITY|XDG'
```

---

## Resumo dos arquivos modificados

| Arquivo | O que faz |
|---|---|
| `~/.config/systemd/user/graphical-session.target.d/override.conf` | Permite start manual do target |
| `~/.config/systemd/user/graphical-session-anchor.service` | Mantém o target ativo via `RemainAfterExit=yes` |
| `~/.xprofile` | Exporta env vars e ativa o target no login |
| `~/.config/i3/env.sh` | Define variáveis XDG e de ambiente do i3 |
| `~/.config/i3/config` | Para o target no binding de logout |
| Polybar `powermenu` | Para o target na opção de logout do menu |
