#!/usr/bin/env python3
# Alt+Tab real para i3wm (X11) - versão estável
# Dependências:
# sudo pacman -S python-gobject gtk3 python-i3ipc

import gi
import os
import signal
import i3ipc

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

LOCKFILE = "/tmp/i3_alttab.lock"
AUTO_CONFIRM_MS = 700


# ---------------------------------------------------------
# lock único
# ---------------------------------------------------------
def cleanup_lock():
    try:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
    except:
        pass


if os.path.exists(LOCKFILE):
    cleanup_lock()

with open(LOCKFILE, "w") as f:
    f.write(str(os.getpid()))


# ---------------------------------------------------------
class AltTab(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        self.i3 = i3ipc.Connection()

        self.windows = []
        self.tiles = []
        self.current = 0
        self.timer = None

        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_accept_focus(True)
        self.set_focus_on_map(True)

        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=14
        )

        self.add(self.box)

        self.apply_css()
        self.load_windows()

        self.connect("map-event", self.on_map)
        self.connect("key-press-event", self.on_key)
        self.connect("focus-out-event", lambda *a: self.quit())

    # -----------------------------------------------------
    def apply_css(self):
        css = """
        #main {
            background-color: rgba(25,25,25,0.96);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.12);
            padding: 18px;
        }

        .tile {
            padding: 14px;
            border-radius: 12px;
            border: 2px solid transparent;
        }

        .active {
            border: 2px solid #89b4fa;
            background-color: rgba(255,255,255,0.08);
        }

        .lbl {
            color: #efefef;
            margin-top: 8px;
            font-size: 9pt;
        }
        """

        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.set_name("main")

    # -----------------------------------------------------
    def get_icon(self, cls):
        cls = (cls or "").lower()

        table = {
            "firefox": "firefox",
            "kitty": "kitty",
            "thunar": "thunar",
            "code": "visual-studio-code",
            "libreoffice": "libreoffice-startcenter",
            "vlc": "vlc",
            "mpv": "mpv",
        }

        return table.get(cls, "application-x-executable")

    # -----------------------------------------------------
    def load_windows(self):
        tree = self.i3.get_tree()
        focused = tree.find_focused()

        if not focused:
            return

        ws = focused.workspace()

        wins = [
            w for w in ws.leaves()
            if w.name and w.window_class
        ]

        if len(wins) == 0:
            return

        # coloca janela atual primeiro
        wins.sort(key=lambda w: 0 if w.id == focused.id else 1)

        self.windows = wins

        for w in wins:
            tile = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=5
            )

            tile.get_style_context().add_class("tile")

            icon = Gtk.Image.new_from_icon_name(
                self.get_icon(w.window_class),
                Gtk.IconSize.DIALOG
            )

            txt = w.name[:28]
            if len(w.name) > 28:
                txt += "..."

            label = Gtk.Label(label=txt)
            label.get_style_context().add_class("lbl")

            tile.pack_start(icon, True, True, 0)
            tile.pack_start(label, False, False, 0)

            self.box.pack_start(tile, False, False, 0)
            self.tiles.append(tile)

        # Alt+Tab já vai para próxima
        self.current = 1 if len(self.tiles) > 1 else 0
        self.refresh()

    # -----------------------------------------------------
    def refresh(self):
        for i, t in enumerate(self.tiles):
            ctx = t.get_style_context()

            if i == self.current:
                ctx.add_class("active")
            else:
                ctx.remove_class("active")

    # -----------------------------------------------------
    def on_map(self, *args):
        self.present()
        self.grab_focus()
        self.restart_timer()
        return False

    # -----------------------------------------------------
    def restart_timer(self):
        if self.timer:
            GLib.source_remove(self.timer)

        self.timer = GLib.timeout_add(
            AUTO_CONFIRM_MS,
            self.confirm
        )

    # -----------------------------------------------------
    def on_key(self, widget, event):
        key = Gdk.keyval_name(event.keyval)

        if key == "Tab":
            self.current = (self.current + 1) % len(self.tiles)
            self.refresh()
            self.restart_timer()
            return True

        elif key == "ISO_Left_Tab":
            self.current = (self.current - 1) % len(self.tiles)
            self.refresh()
            self.restart_timer()
            return True

        elif key == "Return":
            self.confirm()
            return True

        elif key == "Escape":
            self.quit()
            return True

        return False

    # -----------------------------------------------------
    def confirm(self):
        if not self.windows:
            self.quit()
            return False

        con_id = self.windows[self.current].id

        self.hide()

        def focus():
            self.i3.command(f'[con_id="{con_id}"] focus')
            self.quit()
            return False

        GLib.timeout_add(80, focus)
        return False

    # -----------------------------------------------------
    def quit(self):
        cleanup_lock()

        try:
            Gtk.main_quit()
        except:
            pass


# ---------------------------------------------------------
def sig_handler(sig, frame):
    cleanup_lock()
    Gtk.main_quit()


signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)


# ---------------------------------------------------------
if __name__ == "__main__":
    win = AltTab()
    win.show_all()

    if not win.windows:
        GLib.timeout_add(100, win.quit)

    Gtk.main()
