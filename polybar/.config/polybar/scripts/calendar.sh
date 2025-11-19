#!/bin/bash
WINDOW_NAME="Calendario"

# Se a janela já existe, fecha
if wmctrl -l | grep -q "$WINDOW_NAME"; then
    wmctrl -c "$WINDOW_NAME"
    exit 0
fi

# Senão, abre o calendário em GTK3 (Python)
python3 - <<'EOF' &
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class CalendarWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Calendario")

        # Configurações da janela
        self.set_decorated(False)      # Sem bordas
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)      # Sempre no topo
        self.set_resizable(False)
        self.move(1029, 9)             # Posição da janela

        # Estilo CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background-color: #1e1e1e;
            }
            calendar {
                color: #ffffff;
                font: 11pt "SF Pro Display Bold";
                background-color: #1e1e1e;
            }
            calendar:selected {
                background-color: #ff3b30;
                color: #ffffff;
            }
        """)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        # Widget calendário
        self.calendar = Gtk.Calendar()
        self.add(self.calendar)

        # Eventos para toda a janela
        self.connect("button-press-event", self.on_double_click)
        self.connect("key-press-event", self.on_key_press)

    def on_double_click(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            Gtk.main_quit()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

win = CalendarWindow()
win.show_all()
Gtk.main()
EOF
