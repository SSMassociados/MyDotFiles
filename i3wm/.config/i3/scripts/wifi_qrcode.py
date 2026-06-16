#!/usr/bin/env python3
import sys
import subprocess
import tempfile
import os
import signal
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
import qrcode
from PIL import ImageOps

LOCK_FILE = "/tmp/wifi_qrcode.pid"

def handle_toggle():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass
        finally:
            if os.path.exists(LOCK_FILE):
                os.unlink(LOCK_FILE)
        sys.exit(0)

def write_pid():
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def cleanup(*args):
    if os.path.exists(LOCK_FILE):
        try:
            os.unlink(LOCK_FILE)
        except FileNotFoundError:
            pass
    Gtk.main_quit()

def get_wifi_info():
    result = subprocess.run(
        ['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'],
        capture_output=True, text=True
    )
    ssid = None
    for line in result.stdout.splitlines():
        if line.startswith('sim:'):
            ssid = line[4:]
            break
    if not ssid:
        return None, None

    result = subprocess.run(
        ['sudo', 'grep', '-rl', f'ssid={ssid}',
         '/etc/NetworkManager/system-connections/'],
        capture_output=True, text=True
    )
    conn_files = result.stdout.strip().splitlines()
    if not conn_files:
        return ssid, None

    result = subprocess.run(
        ['sudo', 'awk', '-F=',
         '/^\\[wifi-security\\]/{found=1} found && /^psk=/{print $2; exit}',
         conn_files[0]],
        capture_output=True, text=True
    )
    password = result.stdout.strip()
    return ssid, password

def generate_qr_pixbuf(ssid, password, size=320):
    data = f"WIFI:S:{ssid};T:WPA;P:{password};;"
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="#000000",
        back_color="#ffffff"
    ).convert("RGB")
    img = ImageOps.expand(img, border=12, fill="#ffffff")

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        tmp_path = f.name
    img.save(tmp_path)
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp_path, size, size, True)
    os.unlink(tmp_path)
    return pixbuf

def center_window(win):
    screen = Gdk.Screen.get_default()
    sw = screen.get_width()
    sh = screen.get_height()
    ww, wh = win.get_size()
    win.move((sw - ww) // 2, (sh - wh) // 2)

def build_window():
    win = Gtk.Window(title="Wi-Fi QR")
    win.set_resizable(False)
    win.set_decorated(False)
    win.set_keep_above(True)
    win.set_focus_on_map(True)
    win.add_events(Gdk.EventMask.FOCUS_CHANGE_MASK)
    win.connect("destroy", cleanup)
    win.connect("focus-out-event", lambda w, e: cleanup())
    win.connect("key-press-event", lambda w, e: cleanup()
                if e.keyval in (Gdk.KEY_q, Gdk.KEY_Escape) else None)

    css = b"""
    .qr-frame {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 8px;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    box.set_margin_top(16)
    box.set_margin_bottom(16)
    box.set_margin_start(16)
    box.set_margin_end(16)

    stack = Gtk.Stack()
    stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
    stack.set_transition_duration(150)

    # --- Spinner ---
    spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    spinner_box.set_halign(Gtk.Align.CENTER)
    spinner_box.set_valign(Gtk.Align.CENTER)
    spinner_box.set_margin_top(60)
    spinner_box.set_margin_bottom(60)
    spinner_box.set_margin_start(60)
    spinner_box.set_margin_end(60)
    spinner = Gtk.Spinner()
    spinner.set_size_request(48, 48)
    spinner.start()
    lbl_loading = Gtk.Label(label="Obtendo rede...")
    lbl_loading.get_style_context().add_class("dim-label")
    spinner_box.pack_start(spinner, False, False, 0)
    spinner_box.pack_start(lbl_loading, False, False, 0)

    # --- Conteúdo ---
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

    lbl_ssid = Gtk.Label()
    lbl_ssid.set_halign(Gtk.Align.START)

    pass_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    lbl_icon = Gtk.Label(label="🔑")
    lbl_icon.set_halign(Gtk.Align.START)
    entry_pass = Gtk.Entry()
    entry_pass.set_visibility(False)
    entry_pass.set_editable(False)
    entry_pass.set_can_focus(False)
    entry_pass.set_has_frame(False)
    entry_pass.set_hexpand(True)

    btn_eye = Gtk.Button()
    btn_eye.set_relief(Gtk.ReliefStyle.NONE)
    btn_eye.set_can_focus(False)
    btn_eye.set_image(Gtk.Image.new_from_icon_name(
        "view-reveal-symbolic", Gtk.IconSize.BUTTON))
    btn_eye.set_tooltip_text("Mostrar/ocultar senha")

    def toggle_password(btn):
        visible = entry_pass.get_visibility()
        entry_pass.set_visibility(not visible)
        icon = "view-conceal-symbolic" if not visible else "view-reveal-symbolic"
        btn.set_image(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))

    btn_eye.connect("clicked", toggle_password)
    pass_box.pack_start(lbl_icon, False, False, 0)
    pass_box.pack_start(entry_pass, True, True, 0)
    pass_box.pack_start(btn_eye, False, False, 0)

    frame = Gtk.Frame()
    frame.set_shadow_type(Gtk.ShadowType.NONE)
    frame.get_style_context().add_class("qr-frame")
    img_qr = Gtk.Image()
    frame.add(img_qr)

    content_box.pack_start(lbl_ssid, False, False, 0)
    content_box.pack_start(pass_box, False, False, 0)
    content_box.pack_start(frame, False, False, 0)

    stack.add_named(spinner_box, "spinner")
    stack.add_named(content_box, "content")
    stack.set_visible_child_name("spinner")

    box.pack_start(stack, True, True, 0)
    win.add(box)
    win.show_all()
    center_window(win)

    def worker():
        ssid, password = get_wifi_info()

        if not ssid or not password:
            GLib.idle_add(lambda: (
                subprocess.run(['notify-send', 'Wi-Fi QR',
                               'Rede ou senha não encontrada.']),
                cleanup()
            ))
            return

        pixbuf = generate_qr_pixbuf(ssid, password)

        def update_ui():
            lbl_ssid.set_label(f"📡  {ssid}")
            entry_pass.set_text(password)
            img_qr.set_from_pixbuf(pixbuf)
            stack.set_visible_child_name("content")

            def recenter():
                win.resize(1, 1)
                center_window(win)
                return False

            GLib.timeout_add(50, recenter)
            return False

        GLib.idle_add(update_ui)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    return win

def main():
    handle_toggle()
    write_pid()
    signal.signal(signal.SIGTERM, cleanup)

    win = build_window()
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
