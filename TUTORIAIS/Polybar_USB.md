# Polybar USB — Setup completo (udev + módulo + script)

## Contexto

`/home` é uma partição separada (`nvme0n1p6`). O udev dispara **antes** dessa
partição ser montada, então o script não pode ser referenciado diretamente de
`~/.config/polybar/scripts/`. Uma cópia deve existir em `/usr/local/bin`.

---

## 1. Script

O script principal fica em:

```
~/.config/polybar/scripts/system_usb_udev.sh
```

Após qualquer edição, sincronize para o local que o udev acessa:

```bash
sudo cp ~/.config/polybar/scripts/system_usb_udev.sh \
  /usr/local/bin/polybar-usb-udev.sh
sudo chmod +x /usr/local/bin/polybar-usb-udev.sh
```

---

## 2. Regra udev

```bash
sudo tee /etc/udev/rules.d/99-polybar-usb.rules << 'EOF2'
ACTION=="add", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", RUN+="/usr/local/bin/polybar-usb-udev.sh --update"
ACTION=="remove", SUBSYSTEM=="block", ENV{DEVTYPE}=="partition", RUN+="/usr/local/bin/polybar-usb-udev.sh --update"
EOF2

sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## 3. Módulo da Polybar

```ini
[module/pen_usb]
type     = custom/script
exec     = ~/.config/polybar/scripts/system_usb_udev.sh
tail     = true
format-prefix            = "  "
format-prefix-foreground = #FF0000
format-underline         = ${colors.underline}
label    = %output%
click-left  = ~/.config/polybar/scripts/system_usb_udev.sh --mount-notify &
click-right = ~/.config/polybar/scripts/system_usb_udev.sh --unmount-notify &
```

> O módulo da polybar usa o script em `~/.config/polybar/scripts/` normalmente,
> pois já roda com `/home` montado. Só o udev precisa da cópia em `/usr/local/bin`.

---

## 4. Verificar se está funcionando

```bash
# Sem erros relacionados ao script
journalctl -b -p err..warning | grep -i "polybar\|usb"

# Testar manualmente como o udev executa
sudo /usr/local/bin/polybar-usb-udev.sh --update
echo "Exit: $?"
```
