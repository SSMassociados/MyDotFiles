#!/bin/bash

WINDOW_NAME="Informações da Bateria"

# Verifica se a janela já existe
if wmctrl -l | grep -q "$WINDOW_NAME"; then
    # Fecha a janela encontrada
    wmctrl -c "$WINDOW_NAME"
    exit 0
fi

# ---------- Lógica normal do script -----------

source "$HOME/.cache/wal/colors.sh"

BAT="BAT0"

CAPACITY=$(cat /sys/class/power_supply/$BAT/capacity)
STATUS=$(cat /sys/class/power_supply/$BAT/status)

HEALTH="N/A"
if [ -f /sys/class/power_supply/$BAT/charge_full_design ]; then
    FULL=$(cat /sys/class/power_supply/$BAT/charge_full)
    DESIGN=$(cat /sys/class/power_supply/$BAT/charge_full_design)
    if [ "$DESIGN" -gt 0 ]; then
        HEALTH="$((100 * FULL / DESIGN))%"
    fi
fi

VOLTAGE=$(cat /sys/class/power_supply/$BAT/voltage_now)
CURRENT=$(cat /sys/class/power_supply/$BAT/current_now)
TECHNOLOGY=$(cat /sys/class/power_supply/$BAT/technology)

VOLTAGE_V=$((VOLTAGE / 1000000))
CURRENT_A=$((CURRENT / 1000000))

PYTHON_SCRIPT=$(mktemp)

cat > "$PYTHON_SCRIPT" << EOF
#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

background = '$background'
foreground = '$foreground'

class BatteryWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="$WINDOW_NAME")
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(15)

        css = f"""
        window {{
            background-color: {background};
            color: {foreground};
        }}
        .info-label {{
            font-weight: bold;
        }}
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        context = self.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(title_box, False, False, 0)

        battery_icon = Gtk.Image.new_from_icon_name("battery-full-symbolic", Gtk.IconSize.DIALOG)
        title_box.pack_start(battery_icon, False, False, 0)

        title_label = Gtk.Label()
        title_label.set_markup("<b>Status da Bateria</b>")
        title_label.set_justify(Gtk.Justification.LEFT)
        title_box.pack_start(title_label, False, False, 0)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(separator, False, False, 5)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(8)
        main_box.pack_start(grid, True, True, 0)

        self.add_info_row(grid, 0, "🔋", "Capacidade:", "${CAPACITY}%")
        self.add_info_row(grid, 1, "⚡", "Status:", "${STATUS}")
        self.add_info_row(grid, 2, "🩺", "Saúde:", "${HEALTH}")
        self.add_info_row(grid, 3, "🔌", "Voltagem:", "${VOLTAGE_V}V")
        self.add_info_row(grid, 4, "🔋", "Corrente:", "${CURRENT_A}A")
        self.add_info_row(grid, 5, "⚙️", "Tecnologia:", "${TECHNOLOGY}")

        # Removido botão fechar, mantendo apenas ESC ou duplo clique para encerrar

        self.connect("key-press-event", self.on_key_press)
        self.connect("button-press-event", self.on_double_click)

    def add_info_row(self, grid, row, icon, label, value):
        icon_label = Gtk.Label(label=icon)
        icon_label.set_halign(Gtk.Align.START)
        grid.attach(icon_label, 0, row, 1, 1)

        name_label = Gtk.Label(label=label)
        name_label.set_halign(Gtk.Align.START)
        name_label.get_style_context().add_class("info-label")
        grid.attach(name_label, 1, row, 1, 1)

        value_label = Gtk.Label(label=value)
        value_label.set_halign(Gtk.Align.START)
        value_label.set_selectable(True)
        grid.attach(value_label, 2, row, 1, 1)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def on_double_click(self, widget, event):
        if event.type.value_name == "GDK_2BUTTON_PRESS":
            self.destroy()

win = BatteryWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
EOF

chmod +x "$PYTHON_SCRIPT"
python3 "$PYTHON_SCRIPT" &
disown
