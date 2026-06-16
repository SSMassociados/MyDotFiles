#!/usr/bin/env python3
# ==================================================
# PYWAL GUI — Interface GTK para gerenciar wallpapers
# Salve em: ~/.config/i3/scripts/pywal_gui.py
# Dependências: python3-gi, gir1.2-gtk-3.0, python3-pil
# Uso: python3 pywal_gui.py
# ==================================================

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk, Pango

import os
import sys
import json
import random
import subprocess
import threading
import shutil
from pathlib import Path


# ── Configurações ──────────────────────────────────────────────────────────────
WALLPAPER_DIR = Path.home() / ".wallpaper"
CACHE_DIR     = Path.home() / ".cache" / "wal"
I3_SCRIPTS    = Path.home() / ".config" / "i3" / "scripts"
POLYBAR_CONF  = Path.home() / ".config" / "polybar"
THUMB_SIZE    = 200   # px — largura da miniatura
THUMB_HEIGHT  = 120   # px — altura da miniatura
EXTENSIONS    = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
CONFIG_FILE   = CACHE_DIR / "pywal_gui.json"
DAEMON_SCRIPT = I3_SCRIPTS / "pywal_daemon.py"
SERVICE_NAME  = "pywal-wallpaper.service"


def save_config(active: bool, interval_s: int):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({
        "active": active,
        "interval_s": interval_s,
    }))


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {"active": False, "interval_s": 300}


def daemon_is_running() -> bool:
    r = subprocess.run(
        ["systemctl", "--user", "is-active", "--quiet", SERVICE_NAME],
        capture_output=True
    )
    return r.returncode == 0


def daemon_start():
    subprocess.run(["systemctl", "--user", "start", SERVICE_NAME], capture_output=True)


def daemon_stop():
    subprocess.run(["systemctl", "--user", "stop", SERVICE_NAME], capture_output=True)


def daemon_enable():
    subprocess.run(["systemctl", "--user", "enable", SERVICE_NAME], capture_output=True)


def daemon_disable():
    subprocess.run(["systemctl", "--user", "disable", SERVICE_NAME], capture_output=True)


def daemon_is_enabled() -> bool:
    r = subprocess.run(
        ["systemctl", "--user", "is-enabled", "--quiet", SERVICE_NAME],
        capture_output=True
    )
    return r.returncode == 0


def daemon_restart():
    subprocess.run(["systemctl", "--user", "restart", SERVICE_NAME], capture_output=True)


def install_service():
    """Instala o .service do systemd --user se ainda não existir."""
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_file = service_dir / SERVICE_NAME
    daemon_path = DAEMON_SCRIPT
    service_content = f"""[Unit]
Description=Pywal wallpaper rotation daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} {daemon_path}
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%i/bus

[Install]
WantedBy=default.target
"""
    service_file.write_text(service_content)
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)

# CSS mínimo — herda tema, fontes e cores do GTK do sistema (lê ~/.config/gtk-3.0/settings.ini)
# Só define estrutura/espaçamento e estados que o tema não cobre.
CSS = b"""
.sidebar {
    border-right: 1px solid alpha(currentColor, 0.12);
    padding: 0;
}

.sidebar-title {
    font-weight: bold;
    padding: 20px 16px 8px 16px;
}

.sidebar-section {
    font-size: smaller;
    opacity: 0.55;
    padding: 16px 16px 4px 16px;
}

.current-wall-label {
    font-size: smaller;
    opacity: 0.7;
    padding: 4px 16px 0 16px;
}

.separator-line {
    min-height: 1px;
}

.random-toggle {
    margin: 6px 12px;
}
.random-toggle.active-toggle {
    font-weight: bold;
}

.interval-label {
    font-size: smaller;
    opacity: 0.6;
    padding: 4px 16px;
}

.apply-btn {
    margin: 6px 12px;
    font-weight: bold;
}

.status-bar {
    padding: 4px 12px;
    border-top: 1px solid alpha(currentColor, 0.1);
}
.status-ok {
    color: @success_color;
}
.status-err {
    color: @error_color;
}

.grid-area {
    padding: 8px;
}

.thumb-box {
    border: 2px solid transparent;
    border-radius: 4px;
    padding: 3px;
    margin: 3px;
}
.thumb-box:hover {
    border-color: alpha(@theme_selected_bg_color, 0.6);
}
.thumb-box.selected-thumb {
    border-color: @theme_selected_bg_color;
}

.thumb-name {
    font-size: smaller;
    opacity: 0.6;
    padding: 2px 2px 0 2px;
}
.thumb-name.selected-name {
    opacity: 1.0;
    font-weight: bold;
}

.search-entry {
    margin: 8px 16px;
}

.header-bar {
    padding: 6px 16px;
    border-bottom: 1px solid alpha(currentColor, 0.1);
}
.header-title {
    font-weight: bold;
}
.header-count {
    opacity: 0.4;
    font-size: smaller;
}

.pywal-check {
    color: @success_color;
    font-size: smaller;
    padding: 4px 16px;
}
.pywal-missing {
    color: @error_color;
    font-size: smaller;
    padding: 4px 16px;
}

.color-label {
    font-size: smaller;
    opacity: 0.5;
    padding: 0 16px 4px 16px;
}
"""


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_wallpapers():
    if not WALLPAPER_DIR.exists():
        return []
    files = []
    for p in sorted(WALLPAPER_DIR.rglob("*")):
        if p.is_file() and p.suffix.lower() in EXTENSIONS:
            files.append(p)
    return files


def load_wal_colors():
    colors_json = CACHE_DIR / "colors.json"
    if not colors_json.exists():
        return []
    try:
        data = json.loads(colors_json.read_text())
        palette = []
        for key in sorted(data.get("colors", {}).keys()):
            palette.append(data["colors"][key])
        return palette[:16]
    except Exception:
        return []


def hex_to_gdk(hex_color: str):
    c = Gdk.RGBA()
    c.parse(hex_color)
    return c


def make_thumbnail(path: Path, w=THUMB_SIZE, h=THUMB_HEIGHT) -> GdkPixbuf.Pixbuf | None:
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(str(path))
        pw, ph = pb.get_width(), pb.get_height()
        scale = min(w / pw, h / ph)
        nw, nh = int(pw * scale), int(ph * scale)
        return pb.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
    except Exception:
        return None


def run_pywal(wallpaper: Path, callback):
    """Roda pywal em thread separada para não travar a UI."""
    def worker():
        wal_bin = shutil.which("wal")
        if not wal_bin:
            GLib.idle_add(callback, False, "pywal não encontrado no PATH")
            return
        try:
            # 1. Pywal gera as cores
            has_cols16 = "--cols16" in subprocess.run(
                [wal_bin, "--help"], capture_output=True, text=True
            ).stdout
            if has_cols16:
                subprocess.run(
                    [wal_bin, "-i", str(wallpaper), "--cols16", "--backend", "feh"],
                    check=True, capture_output=True
                )
                subprocess.run(["feh", "--bg-fill", str(wallpaper)], check=True)
            else:
                subprocess.run(
                    [wal_bin, "-i", str(wallpaper), "--iterative"],
                    check=True, capture_output=True
                )
            # 2. Xresources
            xres = CACHE_DIR / "colors.Xresources"
            if xres.exists():
                subprocess.run(["xrdb", "-merge", str(xres)])
            # 3. Scripts auxiliares (se existirem)
            for script in [
                I3_SCRIPTS / "pywal_dunst.sh",
                POLYBAR_CONF / "pywal_polybar.sh",
            ]:
                if script.exists():
                    subprocess.Popen([str(script)])
            GLib.idle_add(callback, True, str(wallpaper.name))
        except subprocess.CalledProcessError as e:
            GLib.idle_add(callback, False, f"Erro: {e}")
    threading.Thread(target=worker, daemon=True).start()


# ── Widget de miniatura ────────────────────────────────────────────────────────

class ThumbCard(Gtk.EventBox):
    def __init__(self, path: Path, on_click):
        super().__init__()
        self.path = path
        self.on_click = on_click
        self._selected = False

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.box)
        self.get_style_context().add_class("thumb-box")

        # Imagem
        self.image = Gtk.Image()
        pb = make_thumbnail(path)
        if pb:
            self.image.set_from_pixbuf(pb)
        else:
            self.image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        self.image.set_size_request(THUMB_SIZE, THUMB_HEIGHT)
        self.box.pack_start(self.image, False, False, 0)

        # Nome
        name = path.name if len(path.name) <= 22 else path.name[:19] + "…"
        self.lbl = Gtk.Label(label=name)
        self.lbl.set_xalign(0)
        self.lbl.get_style_context().add_class("thumb-name")
        self.box.pack_start(self.lbl, False, False, 0)

        self.connect("button-press-event", self._clicked)
        self.set_tooltip_text(str(path))

    def _clicked(self, *_):
        self.on_click(self)

    def set_selected(self, val: bool):
        self._selected = val
        ctx = self.get_style_context()
        lctx = self.lbl.get_style_context()
        if val:
            ctx.add_class("selected-thumb")
            lctx.add_class("selected-name")
        else:
            ctx.remove_class("selected-thumb")
            lctx.remove_class("selected-name")


# ── Janela principal ───────────────────────────────────────────────────────────

class PywalGUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="PYWAL")
        self.set_default_size(1100, 680)
        self.set_border_width(0)

        self._all_walls: list[Path] = []
        self._filtered: list[Path] = []
        self._cards: dict[Path, ThumbCard] = {}
        self._selected_card: ThumbCard | None = None
        self._random_active = False
        self._random_timer_id: int | None = None
        self._random_interval_s = 300  # 5 min

        self._build_ui()
        self._refresh_wallpapers()
        self._refresh_colors()
        self._load_and_sync_daemon()
        self.connect("destroy", self._on_destroy)

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hdr.get_style_context().add_class("header-bar")
        title = Gtk.Label(label="Pywal — Gerenciador de Wallpapers")
        title.get_style_context().add_class("header-title")
        title.set_xalign(0)
        hdr.pack_start(title, True, True, 0)
        self.count_lbl = Gtk.Label(label="0 WALLPAPERS")
        self.count_lbl.get_style_context().add_class("header-count")
        hdr.pack_end(self.count_lbl, False, False, 0)
        root.pack_start(hdr, False, False, 0)

        # Body (sidebar + grid)
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.set_vexpand(True)
        root.pack_start(body, True, True, 0)

        body.pack_start(self._build_sidebar(), False, False, 0)
        body.pack_start(self._build_grid_area(), True, True, 0)

        # Status bar
        root.pack_start(self._build_status_bar(), False, False, 0)

    def _build_sidebar(self):
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side.set_size_request(220, -1)
        side.get_style_context().add_class("sidebar")

        # Título
        t = Gtk.Label(label="Controles")
        t.set_xalign(0)
        t.get_style_context().add_class("sidebar-title")
        side.pack_start(t, False, False, 0)

        # Pywal status
        wal_ok = bool(shutil.which("wal"))
        pywal_lbl = Gtk.Label(label="● PYWAL OK" if wal_ok else "● PYWAL NÃO ENCONTRADO")
        pywal_lbl.set_xalign(0)
        pywal_lbl.get_style_context().add_class("pywal-check" if wal_ok else "pywal-missing")
        side.pack_start(pywal_lbl, False, False, 0)

        # Wallpaper atual
        sec1 = Gtk.Label(label="Wallpaper Atual")
        sec1.set_xalign(0)
        sec1.get_style_context().add_class("sidebar-section")
        side.pack_start(sec1, False, False, 0)

        cl = Gtk.Label(label="Nenhum selecionado")
        cl.set_xalign(0)
        cl.get_style_context().add_class("current-wall-label")
        cl.set_line_wrap(True)
        cl.set_max_width_chars(22)
        self.current_lbl = cl
        side.pack_start(cl, False, False, 0)

        # Botão aplicar
        self.apply_btn = Gtk.Button(label="▶  Aplicar Wallpaper")
        self.apply_btn.get_style_context().add_class("apply-btn")
        self.apply_btn.connect("clicked", self._on_apply)
        self.apply_btn.set_sensitive(False)
        side.pack_start(self.apply_btn, False, False, 0)

        # Separador
        sep = Gtk.Separator()
        sep.get_style_context().add_class("separator-line")
        side.pack_start(sep, False, False, 8)

        # Troca aleatória
        sec2 = Gtk.Label(label="Troca Automática")
        sec2.set_xalign(0)
        sec2.get_style_context().add_class("sidebar-section")
        side.pack_start(sec2, False, False, 0)

        self.random_btn = Gtk.Button(label="⟳  Iniciar Troca Automática")
        self.random_btn.get_style_context().add_class("random-toggle")
        self.random_btn.connect("clicked", self._toggle_random)
        side.pack_start(self.random_btn, False, False, 0)

        # Intervalo
        intv_lbl = Gtk.Label(label="Intervalo (minutos)")
        intv_lbl.set_xalign(0)
        intv_lbl.get_style_context().add_class("interval-label")
        side.pack_start(intv_lbl, False, False, 0)

        self.interval_spin = Gtk.SpinButton()
        self.interval_spin.set_adjustment(
            Gtk.Adjustment(value=5, lower=1, upper=999, step_increment=1, page_increment=5)
        )
        self.interval_spin.set_margin_start(12)
        self.interval_spin.set_margin_end(12)
        self.interval_spin.connect("value-changed", self._on_interval_changed)
        side.pack_start(self.interval_spin, False, False, 4)

        # Botão aleatório agora
        rnd_now = Gtk.Button(label="⚡  Trocar Agora")
        rnd_now.get_style_context().add_class("apply-btn")
        rnd_now.connect("clicked", self._apply_random)
        side.pack_start(rnd_now, False, False, 0)

        # Autostart
        self.autostart_chk = Gtk.CheckButton(label="Iniciar automaticamente no login")
        self.autostart_chk.set_margin_start(12)
        self.autostart_chk.set_margin_end(12)
        self.autostart_chk.set_margin_top(4)
        self.autostart_chk.set_active(daemon_is_enabled())
        self.autostart_chk.connect("toggled", self._on_autostart_toggled)
        side.pack_start(self.autostart_chk, False, False, 0)

        # Separador
        sep2 = Gtk.Separator()
        sep2.get_style_context().add_class("separator-line")
        side.pack_start(sep2, False, False, 8)

        # Paleta de cores
        sec3 = Gtk.Label(label="Paleta de Cores")
        sec3.set_xalign(0)
        sec3.get_style_context().add_class("sidebar-section")
        side.pack_start(sec3, False, False, 0)

        self.color_flow = Gtk.FlowBox()
        self.color_flow.set_max_children_per_line(8)
        self.color_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.color_flow.set_margin_start(12)
        self.color_flow.set_margin_end(12)
        self.color_flow.set_margin_bottom(8)
        side.pack_start(self.color_flow, False, False, 0)

        # Dir wallpaper
        side.pack_start(Gtk.Box(), True, True, 0)  # spacer

        dir_lbl = Gtk.Label(label=f"DIR: {WALLPAPER_DIR}")
        dir_lbl.set_xalign(0)
        dir_lbl.set_ellipsize(Pango.EllipsizeMode.START)
        dir_lbl.get_style_context().add_class("color-label")
        dir_lbl.set_margin_bottom(8)
        side.pack_start(dir_lbl, False, False, 0)

        return side

    def _build_grid_area(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Busca
        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Filtrar wallpapers…")
        self.search.get_style_context().add_class("search-entry")
        self.search.connect("search-changed", self._on_search)
        vbox.pack_start(self.search, False, False, 0)

        # Grade com scroll
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.get_style_context().add_class("grid-area")
        vbox.pack_start(scroll, True, True, 0)

        self.flow = Gtk.FlowBox()
        self.flow.set_max_children_per_line(10)
        self.flow.set_min_children_per_line(2)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_row_spacing(4)
        self.flow.set_column_spacing(4)
        self.flow.set_margin_start(8)
        self.flow.set_margin_end(8)
        self.flow.set_margin_top(8)
        self.flow.set_margin_bottom(8)
        scroll.add(self.flow)

        return vbox

    def _build_status_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bar.get_style_context().add_class("status-bar")
        self.status_lbl = Gtk.Label(label="Pronto")
        self.status_lbl.set_xalign(0)
        self.status_lbl.get_style_context().add_class("status-text")
        bar.pack_start(self.status_lbl, True, True, 0)
        self.timer_lbl = Gtk.Label(label="")
        self.timer_lbl.get_style_context().add_class("status-text")
        bar.pack_end(self.timer_lbl, False, False, 0)
        return bar

    # ── Lógica ─────────────────────────────────────────────────────────────────

    def _refresh_wallpapers(self):
        self._all_walls = find_wallpapers()
        self._filtered = list(self._all_walls)
        self._rebuild_grid(self._filtered)
        self.count_lbl.set_text(f"{len(self._all_walls)} WALLPAPERS")
        self._set_status(f"{len(self._all_walls)} wallpapers em {WALLPAPER_DIR}", "ok")

    def _rebuild_grid(self, walls: list[Path]):
        # Remove filhos antigos
        for child in self.flow.get_children():
            child.destroy()
        self._cards.clear()

        for p in walls:
            card = ThumbCard(p, self._on_card_click)
            self._cards[p] = card
            self.flow.add(card)

        self.flow.show_all()

    def _on_card_click(self, card: ThumbCard):
        if self._selected_card:
            self._selected_card.set_selected(False)
        card.set_selected(True)
        self._selected_card = card

        name = card.path.name
        self.current_lbl.set_text(name if len(name) <= 24 else name[:21] + "…")
        self.apply_btn.set_sensitive(True)

        # Aplica imediatamente ao clicar
        self._do_apply(card.path)

    def _on_apply(self, *_):
        if self._selected_card:
            self._do_apply(self._selected_card.path)

    def _apply_random(self, *_):
        if not self._all_walls:
            self._set_status("Nenhum wallpaper encontrado!", "err")
            return
        wall = random.choice(self._all_walls)
        # Atualiza seleção visual sem re-aplicar
        if self._selected_card:
            self._selected_card.set_selected(False)
        if wall in self._cards:
            self._cards[wall].set_selected(True)
            self._selected_card = self._cards[wall]
        name = wall.name
        self.current_lbl.set_text(name if len(name) <= 24 else name[:21] + "…")
        self.apply_btn.set_sensitive(True)
        self._do_apply(wall)

    def _do_apply(self, path: Path):
        self._set_status(f"APLICANDO: {path.name} …", "text")
        self.apply_btn.set_sensitive(False)

        def done(ok: bool, msg: str):
            if ok:
                self._set_status(f"APLICADO: {msg}", "ok")
                self._refresh_colors()
            else:
                self._set_status(msg, "err")
            self.apply_btn.set_sensitive(True)

        run_pywal(path, done)

    def _refresh_colors(self):
        for child in self.color_flow.get_children():
            child.destroy()

        palette = load_wal_colors()
        for hex_color in palette:
            da = Gtk.DrawingArea()
            da.set_size_request(16, 16)
            da.connect("draw", self._draw_swatch, hex_color)
            da.set_tooltip_text(hex_color)
            self.color_flow.add(da)

        self.color_flow.show_all()

    def _draw_swatch(self, widget, cr, hex_color):
        c = Gdk.RGBA()
        c.parse(hex_color)
        cr.set_source_rgba(c.red, c.green, c.blue, c.alpha)
        cr.rectangle(0, 0, 16, 16)
        cr.fill()

    def _on_search(self, entry):
        q = entry.get_text().lower()
        if q:
            self._filtered = [p for p in self._all_walls if q in p.name.lower()]
        else:
            self._filtered = list(self._all_walls)
        self._rebuild_grid(self._filtered)
        self.count_lbl.set_text(f"{len(self._filtered)} / {len(self._all_walls)} WALLPAPERS")

    # ── Rotação aleatória ───────────────────────────────────────────────────────

    def _toggle_random(self, *_):
        if self._random_active:
            self._stop_random()
        else:
            self._start_random()

    def _start_random(self):
        self._random_interval_s = self.interval_spin.get_value_as_int() * 60
        self._random_active = True
        self.random_btn.set_label("⏹  Parar Troca Automática")
        self.random_btn.get_style_context().add_class("active-toggle")
        mins = self.interval_spin.get_value_as_int()
        self._set_status(f"Troca automática: a cada {mins} min — persistente", "ok")
        self._update_timer_label()
        self._schedule_next()
        # Persiste e inicia daemon em background
        save_config(True, self._random_interval_s)
        install_service()
        daemon_start()

    def _schedule_next(self):
        if not self._random_active:
            return
        interval_ms = int(self._random_interval_s * 1000)
        self._random_timer_id = GLib.timeout_add(interval_ms, self._random_tick)

    def _stop_random(self):
        self._random_active = False
        self.random_btn.set_label("⟳  Iniciar Troca Automática")
        self.random_btn.get_style_context().remove_class("active-toggle")
        if self._random_timer_id:
            GLib.source_remove(self._random_timer_id)
            self._random_timer_id = None
        self.timer_lbl.set_text("")
        self._set_status("Troca automática parada", "text")
        # Para daemon e salva config
        save_config(False, self._random_interval_s)
        daemon_stop()

    def _random_tick(self) -> bool:
        # Retorna False para não repetir automaticamente;
        # reagendamos manualmente depois do apply.
        if not self._random_active:
            return False
        self._apply_random()
        self._schedule_next()
        return False

    def _on_interval_changed(self, spin):
        minutes = spin.get_value_as_int()
        self._random_interval_s = minutes * 60
        if self._random_active:
            if self._random_timer_id:
                GLib.source_remove(self._random_timer_id)
                self._random_timer_id = None
            self._schedule_next()
            self._set_status(f"Troca automática: a cada {minutes} min", "ok")
            save_config(True, self._random_interval_s)
            daemon_restart()

    def _load_and_sync_daemon(self):
        """Restaura estado da troca automática a partir do config salvo."""
        cfg = load_config()
        interval_s = cfg.get("interval_s", 300)
        self._random_interval_s = interval_s
        mins = interval_s // 60
        self.interval_spin.set_value(mins)
        running = daemon_is_running()
        # Sincroniza checkbox de autostart
        self.autostart_chk.set_active(daemon_is_enabled())

        if running:
            # Daemon já está rodando — sincroniza UI
            self._random_active = True
            self.random_btn.set_label("⏹  Parar Troca Automática")
            self.random_btn.get_style_context().add_class("active-toggle")
            self._update_timer_label()
            self._schedule_next()
            self._set_status(f"Troca automática ativa: a cada {mins} min — persistente", "ok")

    def _on_autostart_toggled(self, chk):
        if chk.get_active():
            install_service()
            daemon_enable()
            self._set_status("Autostart ativado — inicia no login", "ok")
        else:
            daemon_disable()
            self._set_status("Autostart desativado", "text")

    def _on_destroy(self, *_):
        """Fecha a GUI mas mantém o daemon rodando se estiver ativo."""
        Gtk.main_quit()

    def _update_timer_label(self):
        mins = int(self._random_interval_s // 60)
        self.timer_lbl.set_text(f"Troca automática: {mins} min")

    # ── Status ──────────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, kind: str = "text"):
        self.status_lbl.set_text(msg)
        ctx = self.status_lbl.get_style_context()
        ctx.remove_class("status-ok")
        ctx.remove_class("status-err")
        ctx.remove_class("status-text")
        if kind == "ok":
            ctx.add_class("status-ok")
        elif kind == "err":
            ctx.add_class("status-err")
        else:
            ctx.add_class("status-text")


# ── Entrada ────────────────────────────────────────────────────────────────────

def main():
    apply_css()
    win = PywalGUI()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
