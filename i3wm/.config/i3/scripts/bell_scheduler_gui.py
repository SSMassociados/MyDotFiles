#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")

import os
import sys
import subprocess
import json
import argparse
import logging
import time
import datetime
import dbus
import threading
import dbus.mainloop.glib
from gi.repository import Gtk, Gdk, GLib, Gio, Notify
from typing import Optional, Tuple

# ── Paths ──────────────────────────────────────────────────────────────────────
CONFIG_FILE       = os.path.expanduser("~/.bell_scheduler_config.json")
PID_FILE          = os.path.expanduser("~/.bell_scheduler.pid")
LOG_FILE          = os.path.expanduser("~/.bell_scheduler.log")
SERVICE_DIR       = os.path.expanduser("~/.bell_scheduler")
SERVICE_LOG       = os.path.join(SERVICE_DIR, "service.log")
SERVICE_ERROR_LOG = os.path.join(SERVICE_DIR, "service_error.log")
SCRIPT_FILE       = os.path.join(SERVICE_DIR, "run.sh")

# i3 config dir — respects $XDG_CONFIG_HOME
I3_CONFIG_DIR      = os.path.expanduser(
    os.path.join(os.environ.get("XDG_CONFIG_HOME", "~/.config"), "i3")
)
# Modular setup: autostart lives in its own module file
I3_AUTOSTART_FILE  = os.path.join(I3_CONFIG_DIR, "modules", "autostart.conf")

# Systemd user service
SYSTEMD_USER_DIR = os.path.expanduser("~/.config/systemd/user")
SYSTEMD_SERVICE  = os.path.join(SYSTEMD_USER_DIR, "bell-scheduler.service")

# Autostart exec line that will be appended to / removed from i3 config
_EXEC_MARKER = "# bell-scheduler autostart"
_EXEC_LINE   = (
    f"exec --no-startup-id python3 {os.path.abspath(__file__)} --autostart {_EXEC_MARKER}"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
# Sem CSS customizado — evita conflito com gtk-dark.css do tema Arch.
# Estilo dos botões de controle é feito via Pango markup no label.
APP_CSS = None

# ── Helpers ────────────────────────────────────────────────────────────────────

def terminate_process(proc, timeout: float = 0.5):
    """SIGTERM → wait → SIGKILL."""
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, 15)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                return
            time.sleep(0.05)
        os.killpg(pgid, 9)
    except ProcessLookupError:
        pass


def run_cmd(*args) -> Tuple[int, str, str]:
    """Run a command; return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(args, capture_output=True, text=True)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError as e:
        return 1, "", str(e)


# ── Sound player ───────────────────────────────────────────────────────────────

class SoundPlayer:
    """Player para uso na GUI — usa GLib.idle_add para atualizar widgets."""

    def __init__(self, app):
        self.app = app
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False
        self.lock = threading.RLock()
        self.stop_event = threading.Event()

    def play(self, sound_file: str) -> bool:
        with self.lock:
            if self.is_playing:
                self._stop_locked()
            if not self.app.validate_file_path(sound_file):
                self.app.log(f"Invalid sound file: {sound_file}", "error")
                return False
            try:
                self.stop_event.clear()
                self.is_playing = True
                GLib.idle_add(self.app.update_sound_controls)
                proc = subprocess.Popen(
                    ["paplay", sound_file],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )
                self.current_process = proc

                def _monitor(watched):
                    while not self.stop_event.is_set():
                        if watched.poll() is not None:
                            break
                        time.sleep(0.1)
                    with self.lock:
                        if self.current_process is watched:
                            self.is_playing = False
                            self.current_process = None
                    GLib.idle_add(self.app.update_sound_controls)

                threading.Thread(target=_monitor, args=(proc,), daemon=True).start()
                return True
            except Exception as e:
                self.app.log(f"Error playing sound: {e}", "error")
                self.is_playing = False
                self.current_process = None
                GLib.idle_add(self.app.update_sound_controls)
                return False

    def stop(self):
        with self.lock:
            self._stop_locked()

    def _stop_locked(self):
        if self.is_playing and self.current_process:
            self.stop_event.set()
            terminate_process(self.current_process)
            self.is_playing = False
            self.current_process = None
            GLib.idle_add(self.app.update_sound_controls)
            GLib.idle_add(self._notify_stopped)

    def _notify_stopped(self):
        try:
            Notify.Notification.new(
                "Sound stopped", "Playback stopped", self.app.config["icon"]
            ).show()
        except Exception as e:
            self.app.log(f"Notification error: {e}", "error")
        return False


class DaemonSoundPlayer:
    """Player para uso no daemon — sem GLib.idle_add, sem GTK main loop.
    Lança paplay diretamente e espera terminar (bloqueante por design:
    o daemon tem seu próprio loop while, não precisa de async aqui).
    """

    def __init__(self, log_fn):
        self._log = log_fn
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def play(self, sound_file: str) -> bool:
        with self._lock:
            self._kill_current()
            try:
                self._proc = subprocess.Popen(
                    ["paplay", sound_file],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )
                self._log(f"DaemonSoundPlayer: paplay PID={self._proc.pid}")
                return True
            except Exception as e:
                self._log(f"DaemonSoundPlayer.play error: {e}")
                self._proc = None
                return False

    def stop(self):
        with self._lock:
            self._kill_current()

    def _kill_current(self):
        if self._proc and self._proc.poll() is None:
            terminate_process(self._proc)
        self._proc = None


# ── Main application ───────────────────────────────────────────────────────────

class BellSchedulerApp(Gtk.Application):
    def __init__(self, service_mode=False, autostart_mode=False):
        super().__init__(
            application_id="com.example.BellScheduler",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.process: Optional[subprocess.Popen] = None
        self._svc_log_out = None
        self._svc_log_err = None
        self.service_mode = service_mode
        # autostart_mode: iniciado pelo i3 exec — deve subir daemon automaticamente
        self.autostart_mode = autostart_mode
        self.tray_icon = None
        self.logger = self._setup_logging()
        self.shutdown_event = threading.Event()
        self.window = None
        self.sound_player = SoundPlayer(self)
        self.last_played: Optional[Tuple[str, datetime.date]] = None
        self.notify_initialized = False
        self.config_file_mtime = 0
        # silenced: para o toque atual E suprime os próximos até ser
        # cancelado explicitamente. O daemon continua rodando normalmente.
        self.silenced = False
        self._snooze_timer_id: Optional[int] = None  # GLib source id do snooze
        self._snooze_remaining: int = 0               # segundos restantes
        self._start_minimized = False   # resolvido após load_config
        self._hiding_on_start = False   # True durante o timeout de minimizar

        self.config = {
            "times": ["08:00", "10:00", "12:00", "14:00", "16:00"],
            "days": [1, 2, 3, 4, 5],
            "message": "Bell time!",
            "sound": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "icon": "/usr/share/icons/gnome/256x256/status/appointment-soon.png",
            "active": False,
            "check_interval": 5,
            "custom_sounds": {},
            "start_minimized": False,
            "silenced": False,
        }
        self.load_config()

        if self.service_mode:
            GLib.idle_add(self.run_service)

    # ── Logging ────────────────────────────────────────────────────────────────

    def _setup_logging(self):
        os.makedirs(SERVICE_DIR, exist_ok=True)
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(__name__)

    def log(self, message: str, level: str = "info"):
        (self.logger.error if level == "error" else self.logger.info)(message)

    # ── Config ─────────────────────────────────────────────────────────────────

    def load_config(self):
        try:
            with open(CONFIG_FILE) as f:
                self.config.update(json.load(f))
            self.config_file_mtime = os.path.getmtime(CONFIG_FILE)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"Error loading config: {e}", "error")

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            self.config_file_mtime = os.path.getmtime(CONFIG_FILE)
        except Exception as e:
            self.log(f"Error saving config: {e}", "error")

    def check_config_updates(self):
        try:
            mtime = os.path.getmtime(CONFIG_FILE)
            if mtime > self.config_file_mtime:
                self.load_config()
                return True
        except OSError:
            pass
        return False

    # ── Validation ─────────────────────────────────────────────────────────────

    def validate_time(self, time_str: str) -> bool:
        try:
            h, m = map(int, time_str.split(":"))
            return 0 <= h < 24 and 0 <= m < 60
        except ValueError:
            return False

    def validate_file_path(self, path: str) -> bool:
        try:
            return bool(path and os.path.isfile(path) and os.access(path, os.R_OK))
        except (TypeError, ValueError):
            return False

    # ── Notifications ──────────────────────────────────────────────────────────

    def initialize_notifications(self) -> bool:
        for attempt in range(1, 4):
            try:
                if Notify.is_initted():
                    Notify.uninit()
                Notify.init("BellScheduler")
                self.notify_initialized = True
                return True
            except Exception as e:
                self.log(f"Notify init attempt {attempt}/3: {e}", "error")
                time.sleep(0.5)   # reduzido: não bloquear boot por 3s
        self.notify_initialized = False
        return False

    def check_notification_service(self) -> bool:
        try:
            return dbus.SessionBus().name_has_owner("org.freedesktop.Notifications")
        except Exception:
            return False

    def show_notification(self, message: str, submessage: str) -> bool:
        """Mostra notificação. Em modo daemon usa notify-send (sem depender
        de GLib.MainLoop). Em modo GUI usa libnotify normalmente."""
        if self.service_mode:
            return self._notify_send(message, submessage)
        # Modo GUI: libnotify via GObject
        try:
            if not self.notify_initialized and not self.initialize_notifications():
                return self._notify_send(message, submessage)
            n = Notify.Notification.new(message, submessage, self.config["icon"])
            n.set_urgency(2)
            n.set_timeout(5000)
            return n.show()
        except Exception as e:
            self.log(f"Notification libnotify error: {e}", "error")
            return self._notify_send(message, submessage)

    def _notify_send(self, message: str, submessage: str) -> bool:
        """Fallback: chama notify-send via subprocess.
        Funciona no daemon sem GLib.MainLoop e é mais robusto no boot do i3."""
        try:
            icon = self.config.get("icon", "")
            cmd = ["notify-send", "-t", "5000", "-u", "normal"]
            if icon and os.path.isfile(icon):
                cmd += ["-i", icon]
            cmd += [message, submessage]
            result = subprocess.run(cmd, capture_output=True, timeout=3)
            if result.returncode == 0:
                self.log(f"notify-send OK: {message}")
                return True
            # notify-send falhou — logar stderr mas não abortar
            self.log(f"notify-send rc={result.returncode}: {result.stderr.decode()}", "error")
            return False
        except FileNotFoundError:
            self.log("notify-send não encontrado — instale libnotify", "error")
            return False
        except Exception as e:
            self.log(f"notify-send error: {e}", "error")
            return False

    # ── GTK lifecycle ──────────────────────────────────────────────────────────

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        if options.contains("service"):
            self.service_mode = True
        if options.contains("autostart"):
            self.autostart_mode = True
        self.activate()
        return 0

    def do_activate(self):
        if not self.service_mode:
            if self.window is None:
                self._reconcile_state()
                self.create_main_window()
                if self.autostart_mode or self.config.get("active", False):
                    GLib.idle_add(self._autostart_daemon)
            else:
                if not self._hiding_on_start:
                    self.window.show_all()
                    self.window.present()

    # ── Window ─────────────────────────────────────────────────────────────────

    def _reconcile_state(self):
        """Chamado uma vez no startup da GUI.
        Verifica se o daemon realmente está rodando e corrige config["active"]
        para refletir a realidade — evita botão "Parar" sem daemon ativo.
        """
        daemon_alive = False

        # 1. Verifica PID file
        if os.path.isfile(PID_FILE):
            try:
                with open(PID_FILE) as f:
                    pid = int(f.read().strip())
                # Envia sinal 0: verifica se processo existe sem matá-lo
                os.kill(pid, 0)
                daemon_alive = True
            except (ValueError, ProcessLookupError, PermissionError, OSError):
                # PID não existe mais — remover arquivo obsoleto
                try:
                    os.remove(PID_FILE)
                except OSError:
                    pass

        # 2. Verifica systemd como fallback
        if not daemon_alive:
            _, out, _ = run_cmd("systemctl", "--user", "is-active", "bell-scheduler.service")
            if out == "active":
                daemon_alive = True

        # 3. Reconcilia
        if self.config.get("active", False) and not daemon_alive:
            self.log("Startup: config dizia active mas daemon não está rodando — corrigindo")
            self.config["active"] = False
            self.save_config()
        elif daemon_alive and not self.config.get("active", False):
            self.log("Startup: daemon rodando mas config dizia inactive — corrigindo")
            self.config["active"] = True
            self.save_config()

        self.log(f"Startup reconciliation: active={self.config['active']}, daemon_alive={daemon_alive}")

    def _autostart_daemon(self):
        """Inicia o daemon silenciosamente ao iniciar pelo i3 ou restaurar sessão.
        Chamado via GLib.idle_add para rodar após a janela estar pronta.
        """
        # Só inicia se não há processo filho já vivo
        if self.process is not None and self.process.poll() is None:
            self.log("_autostart_daemon: processo já está rodando, nada a fazer")
            return False
        # Verifica também via PID file (daemon pode ter sido iniciado antes)
        if os.path.isfile(PID_FILE):
            try:
                with open(PID_FILE) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                self.log(f"_autostart_daemon: daemon PID={pid} já ativo via PID file")
                self.config["active"] = True
                self.save_config()
                GLib.idle_add(self.update_interface_state)
                GLib.idle_add(self._refresh_daemon_status)
                return False
            except (ValueError, ProcessLookupError, OSError):
                try:
                    os.remove(PID_FILE)
                except OSError:
                    pass
        self.log("_autostart_daemon: subindo daemon")
        self._start_daemon_silent()
        return False  # remove do idle queue

    def _start_daemon_silent(self):
        """Inicia o subprocesso daemon sem show_info/show_error modais."""
        try:
            os.makedirs(SERVICE_DIR, exist_ok=True)
            with open(SCRIPT_FILE, "w") as f:
                script_path = os.path.abspath(__file__)
                f.write(
                    "#!/bin/bash\n"
                    + f"exec >> {SERVICE_LOG} 2>> {SERVICE_ERROR_LOG}\n"
                    + f"python3 {script_path} --service\n"
                )
            os.chmod(SCRIPT_FILE, 0o755)
            self._svc_log_out = open(SERVICE_LOG, "a")
            self._svc_log_err = open(SERVICE_ERROR_LOG, "a")
            # Passar DBUS_SESSION_BUS_ADDRESS explicitamente ao daemon
            uid = os.getuid()
            daemon_env = os.environ.copy()
            bus_path = f"/run/user/{uid}/bus"
            if os.path.exists(bus_path):
                daemon_env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"
            if os.environ.get("DISPLAY"):
                daemon_env["DISPLAY"] = os.environ["DISPLAY"]

            self.process = subprocess.Popen(
                ["/bin/bash", SCRIPT_FILE],
                stdout=self._svc_log_out,
                stderr=self._svc_log_err,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                preexec_fn=os.setsid,
                env=daemon_env,
            )
            with open(PID_FILE, "w") as f:
                f.write(str(self.process.pid))
            self.config["active"] = True
            self.save_config()
            self.log(f"Daemon auto-iniciado PID={self.process.pid}")
            GLib.idle_add(self.update_interface_state)
            GLib.idle_add(self._refresh_daemon_status)
        except Exception as e:
            self.log(f"Erro no auto-start do daemon: {e}", "error")
            self.config["active"] = False
            self.save_config()

    def create_main_window(self):
        self.window = Gtk.ApplicationWindow(application=self, title="Bell Scheduler")
        self.window.set_default_size(500, 580)
        self.window.set_border_width(6)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.add(main_box)

        try:
            self.initialize_notifications()
            icon_path = self.config["icon"]
            if self.validate_file_path(icon_path):
                self.tray_icon = Gtk.StatusIcon.new_from_file(icon_path)
            else:
                self.tray_icon = Gtk.StatusIcon.new_from_icon_name("appointment-soon")
            self.tray_icon.connect("activate", self.on_icon_activate, self.window)
            self.tray_icon.connect("popup-menu", self.on_icon_click)
            self._update_tray_tooltip()
            self._update_tray_icon()
        except Exception as e:
            self.log(f"Tray error: {e}", "error")

        # ── Weekdays ──────────────────────────────────────────────────────────
        days_frame = Gtk.Frame(label="Weekdays")
        days_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=4, margin=4, homogeneous=True
        )
        days_frame.add(days_box)
        self.day_buttons = []
        for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            btn = Gtk.ToggleButton(label=day)
            btn.set_active(i + 1 in self.config["days"])
            btn.connect("toggled", self.on_day_toggle, i + 1)
            days_box.pack_start(btn, True, True, 0)
            self.day_buttons.append(btn)
        main_box.pack_start(days_frame, False, False, 0)

        # ── Times ─────────────────────────────────────────────────────────────
        times_frame = Gtk.Frame(label="Times")
        times_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        times_frame.add(times_box)
        self.times_list = Gtk.ListBox()
        self.times_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.update_times_list()
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(120)
        scroll.add(self.times_list)
        times_box.pack_start(scroll, True, True, 0)
        add_box = Gtk.Box(spacing=4, margin=2)
        self.time_entry = Gtk.Entry(placeholder_text="HH:MM")
        add_btn = Gtk.Button(label="Add")
        add_btn.connect("clicked", self.on_add_time)
        add_box.pack_start(self.time_entry, True, True, 0)
        add_box.pack_start(add_btn, False, False, 0)
        times_box.pack_start(add_box, False, False, 0)
        main_box.pack_start(times_frame, True, True, 0)

        # ── Settings ──────────────────────────────────────────────────────────
        settings_frame = Gtk.Frame(label="Settings")
        sg = Gtk.Grid(column_spacing=6, row_spacing=6, margin=4)
        settings_frame.add(sg)

        sg.attach(Gtk.Label(label="Message:", xalign=0), 0, 0, 1, 1)
        self.message_entry = Gtk.Entry()
        self.message_entry.set_text(self.config["message"])
        sg.attach(self.message_entry, 1, 0, 1, 1)

        sg.attach(Gtk.Label(label="Default sound:", xalign=0), 0, 1, 1, 1)
        sound_box = Gtk.Box(spacing=4)
        self.sound_entry = Gtk.Entry()
        self.sound_entry.set_text(self.config["sound"])
        sb = Gtk.Button.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        sb.set_tooltip_text("Browse sound file")
        sb.connect("clicked", self.on_browse_sound)
        self.test_button = Gtk.Button.new_from_icon_name(
            "audio-volume-high-symbolic", Gtk.IconSize.BUTTON
        )
        self.test_button.set_tooltip_text("Test sound")
        self.test_button.connect("clicked", self.on_test_sound)
        self.stop_button = Gtk.Button.new_from_icon_name(
            "media-playback-stop-symbolic", Gtk.IconSize.BUTTON
        )
        self.stop_button.set_tooltip_text("Stop sound")
        self.stop_button.connect("clicked", self.on_stop_sound)
        self.stop_button.set_sensitive(False)
        sound_box.pack_start(self.sound_entry, True, True, 0)
        for w in (sb, self.test_button, self.stop_button):
            sound_box.pack_start(w, False, False, 0)
        sg.attach(sound_box, 1, 1, 1, 1)

        sg.attach(Gtk.Label(label="Icon:", xalign=0), 0, 2, 1, 1)
        icon_box = Gtk.Box(spacing=4)
        self.icon_entry = Gtk.Entry()
        self.icon_entry.set_text(self.config["icon"])
        ib = Gtk.Button.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        ib.set_tooltip_text("Browse icon")
        ib.connect("clicked", self.on_browse_icon)
        pv = Gtk.Button.new_from_icon_name("image-x-generic-symbolic", Gtk.IconSize.BUTTON)
        pv.set_tooltip_text("Preview icon")
        pv.connect("clicked", self.on_preview_icon)
        icon_box.pack_start(self.icon_entry, True, True, 0)
        icon_box.pack_start(ib, False, False, 0)
        icon_box.pack_start(pv, False, False, 0)
        sg.attach(icon_box, 1, 2, 1, 1)

        sg.attach(Gtk.Label(label="Check interval (s):", xalign=0), 0, 3, 1, 1)
        self.interval_spin = Gtk.SpinButton.new_with_range(5, 60, 1)
        self.interval_spin.set_value(self.config.get("check_interval", 5))
        sg.attach(self.interval_spin, 1, 3, 1, 1)

        main_box.pack_start(settings_frame, False, False, 0)

        # ── Startup / daemon ──────────────────────────────────────────────────
        startup_frame = Gtk.Frame(label="Startup & Daemon")
        startup_grid = Gtk.Grid(column_spacing=8, row_spacing=8, margin=6)
        startup_frame.add(startup_grid)

        # -- i3 autostart --
        startup_grid.attach(Gtk.Label(label="i3 autostart:", xalign=0), 0, 0, 1, 1)
        i3_box = Gtk.Box(spacing=6)
        self.i3_switch = Gtk.Switch()
        self.i3_switch.set_active(self._i3_autostart_enabled())
        # Path completo fica no tooltip — não estoura o layout
        self.i3_switch.set_tooltip_text(f"Escreve exec em:\n{I3_AUTOSTART_FILE}")
        self.i3_switch.connect("notify::active", self.on_i3_autostart_toggled)
        # Label curto: substitui home por ~, trunca com ellipsis se necessário
        _short_i3 = I3_AUTOSTART_FILE.replace(os.path.expanduser("~"), "~")
        self.i3_path_label = Gtk.Label(xalign=0)
        self.i3_path_label.set_markup(f"<small><tt>{_short_i3}</tt></small>")
        self.i3_path_label.set_ellipsize(3)       # PANGO_ELLIPSIZE_END = 3
        self.i3_path_label.set_max_width_chars(36)
        i3_box.pack_start(self.i3_switch, False, False, 0)
        i3_box.pack_start(self.i3_path_label, True, True, 0)
        startup_grid.attach(i3_box, 1, 0, 1, 1)

        # -- systemd user service --
        startup_grid.attach(Gtk.Label(label="Systemd:", xalign=0), 0, 1, 1, 1)
        sd_box = Gtk.Box(spacing=4)
        install_btn = Gtk.Button(label="Install")
        install_btn.set_tooltip_text(f"Grava o unit em:\n{SYSTEMD_SERVICE}")
        install_btn.connect("clicked", self.on_install_systemd)
        enable_btn = Gtk.Button(label="Enable & start")
        enable_btn.connect("clicked", self.on_enable_systemd)
        disable_btn = Gtk.Button(label="Disable & stop")
        disable_btn.connect("clicked", self.on_disable_systemd)
        # Botão cleanup: detecta unit antiga ativa/habilitada e remove tudo
        clean_btn = Gtk.Button(label="Cleanup")
        clean_btn.set_tooltip_text(
            "Verifica se há unit ativa/habilitada e faz limpeza completa:\n"
            "stop → disable → remove arquivo .service"
        )
        clean_btn.connect("clicked", self.on_cleanup_systemd)
        for w in (install_btn, enable_btn, disable_btn, clean_btn):
            sd_box.pack_start(w, True, True, 0)
        startup_grid.attach(sd_box, 1, 1, 1, 1)

        # -- daemon status --
        startup_grid.attach(Gtk.Label(label="Status:", xalign=0), 0, 2, 1, 1)
        self.daemon_status_label = Gtk.Label(xalign=0)
        self.daemon_status_label.set_ellipsize(3)
        startup_grid.attach(self.daemon_status_label, 1, 2, 1, 1)
        self._refresh_daemon_status()

        # -- notification daemon hint --
        hint = Gtk.Label(xalign=0)
        hint.set_markup(
            "<small><i>i3 não tem daemon de notificação embutido.\n"
            "Instale <b>dunst</b> e adicione-o ao autostart.conf.</i></small>"
        )
        hint.set_line_wrap(True)
        startup_grid.attach(hint, 0, 3, 2, 1)

        main_box.pack_start(startup_frame, False, False, 0)

        # ── Opção iniciar minimizado ──────────────────────────────────────────
        opt_box = Gtk.Box(spacing=6, margin=2)
        self.minimized_check = Gtk.CheckButton(
            label="Iniciar minimizado na tray"
        )
        self.minimized_check.set_active(self.config.get("start_minimized", False))
        self.minimized_check.set_tooltip_text(
            "Ao abrir o app, a janela fica oculta — só o ícone na tray aparece"
        )
        self.minimized_check.connect("toggled", self.on_minimized_toggled)
        opt_box.pack_start(self.minimized_check, False, False, 0)
        main_box.pack_start(opt_box, False, False, 0)

        # ── Control buttons ───────────────────────────────────────────────────
        btn_box = Gtk.Box(spacing=6, margin=2)
        self.start_button = Gtk.Button(label="Start")
        self.start_button.connect("clicked", self.on_start_stop)
        save_btn = Gtk.Button(label="Save Configuration")
        save_btn.connect("clicked", self.on_save_config)
        btn_box.pack_start(self.start_button, True, True, 0)
        btn_box.pack_start(save_btn, True, True, 0)
        main_box.pack_start(btn_box, False, False, 0)

        self.update_interface_state()
        self.window.connect("delete-event", self.on_window_close)

        if self.config.get("start_minimized", False):
            # Configurar hints ANTES do show_all para o WM não colocar no layout
            self.window.set_skip_taskbar_hint(True)
            self.window.set_skip_pager_hint(True)
            self.window.show_all()
            self._hiding_on_start = True
            # Tentar esconder em múltiplos intervalos — boot do i3 é imprevisível
            GLib.timeout_add(100, self._hide_on_start)
            GLib.timeout_add(500, self._hide_on_start)
        else:
            self.window.show_all()

    # ── Times list ─────────────────────────────────────────────────────────────

    def _hide_on_start(self):
        """Esconde a janela no startup. Idempotente — pode ser chamado múltiplas vezes."""
        if self.window and self.window.get_visible():
            self.window.hide()
        if self._hiding_on_start:
            # Restaurar hints normais para quando o usuário abrir depois
            self.window.set_skip_taskbar_hint(False)
            self.window.set_skip_pager_hint(False)
            self._hiding_on_start = False
        return False  # não repetir o timeout

    def update_times_list(self):
        for child in self.times_list.get_children():
            self.times_list.remove(child)
        for time_str in sorted(self.config["times"]):
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row.add(box)
            box.pack_start(Gtk.Label(label=time_str, xalign=0), True, True, 0)
            if time_str in self.config.get("custom_sounds", {}):
                box.pack_start(
                    Gtk.Image.new_from_icon_name(
                        "audio-volume-high-symbolic", Gtk.IconSize.MENU
                    ),
                    False, False, 0,
                )
            edit_btn = Gtk.Button.new_from_icon_name(
                "document-edit-symbolic", Gtk.IconSize.MENU
            )
            edit_btn.connect("clicked", lambda b, t=time_str: self.on_edit_time(t))
            rem_btn = Gtk.Button.new_from_icon_name(
                "edit-delete-symbolic", Gtk.IconSize.MENU
            )
            rem_btn.connect("clicked", lambda b, t=time_str: self.on_remove_time(t))
            box.pack_start(edit_btn, False, False, 0)
            box.pack_start(rem_btn, False, False, 0)
            self.times_list.add(row)
        self.times_list.show_all()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def on_day_toggle(self, button, day):
        if button.get_active():
            if day not in self.config["days"]:
                self.config["days"].append(day)
        else:
            self.config["days"] = [d for d in self.config["days"] if d != day]
        self.config["days"].sort()

    def on_add_time(self, button):
        time_str = self.time_entry.get_text().strip()
        if not self.validate_time(time_str):
            self.show_error("Invalid format", "Use HH:MM (24-hour format)")
            return
        if time_str in self.config["times"]:
            self.show_error("Duplicate time", "This time is already in the list")
            return
        self.config["times"].append(time_str)
        self.update_times_list()
        self.time_entry.set_text("")

    def on_edit_time(self, old_time: str):
        dialog = Gtk.Dialog(title="Edit Time", transient_for=self.window, modal=True)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)
        box = Gtk.Box(spacing=6)
        box.pack_start(Gtk.Label(label="New time:"), False, False, 0)
        entry = Gtk.Entry(text=old_time)
        box.pack_start(entry, True, True, 0)
        dialog.get_content_area().add(box)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            new_time = entry.get_text().strip()
            if self.validate_time(new_time):
                if new_time != old_time and new_time in self.config["times"]:
                    self.show_error("Time exists", "Already in the list")
                else:
                    if old_time in self.config["custom_sounds"]:
                        self.config["custom_sounds"][new_time] = (
                            self.config["custom_sounds"].pop(old_time)
                        )
                    self.config["times"][self.config["times"].index(old_time)] = new_time
                    self.update_times_list()
            else:
                self.show_error("Invalid format", "Use HH:MM (24-hour format)")
        dialog.destroy()

    def on_remove_time(self, time_str: str):
        if time_str in self.config["times"]:
            self.config.get("custom_sounds", {}).pop(time_str, None)
            self.config["times"].remove(time_str)
            self.update_times_list()

    def on_test_sound(self, widget):
        sound_file = self.sound_entry.get_text()
        if not sound_file:
            self.show_error("No sound selected", "Select a sound file first")
            return
        self.sound_player.play(sound_file)

    def update_sound_controls(self):
        if hasattr(self, "test_button"):
            self.test_button.set_sensitive(not self.sound_player.is_playing)
            self.stop_button.set_sensitive(self.sound_player.is_playing)
        return False

    def on_stop_sound(self, widget):
        self.sound_player.stop()

    def on_browse_sound(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select a sound file", parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)
        f = Gtk.FileFilter()
        f.set_name("Sound files")
        f.add_mime_type("audio/*")
        dialog.add_filter(f)
        if dialog.run() == Gtk.ResponseType.OK:
            p = dialog.get_filename()
            if self.validate_file_path(p):
                self.sound_entry.set_text(p)
        dialog.destroy()

    def on_browse_icon(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select an icon", parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)
        f = Gtk.FileFilter()
        f.set_name("Images")
        f.add_mime_type("image/*")
        dialog.add_filter(f)
        if dialog.run() == Gtk.ResponseType.OK:
            p = dialog.get_filename()
            if self.validate_file_path(p):
                self.icon_entry.set_text(p)
        dialog.destroy()

    def on_preview_icon(self, widget):
        icon_file = self.icon_entry.get_text()
        if self.validate_file_path(icon_file):
            dialog = Gtk.Dialog(title="Icon Preview", transient_for=self.window, modal=True)
            dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
            img = Gtk.Image.new_from_file(icon_file)
            img.set_pixel_size(128)
            dialog.get_content_area().add(img)
            dialog.show_all()
            dialog.run()
            dialog.destroy()
        else:
            self.show_error("Invalid file", "The icon file cannot be accessed")

    def on_minimized_toggled(self, widget):
        """Salva imediatamente a preferência de iniciar minimizado."""
        self.config["start_minimized"] = widget.get_active()
        self.save_config()

    def on_save_config(self, widget):
        self.config["message"] = self.message_entry.get_text()
        self.config["sound"] = self.sound_entry.get_text()
        self.config["icon"] = self.icon_entry.get_text()
        self.config["check_interval"] = self.interval_spin.get_value()
        if not self.validate_file_path(self.config["sound"]):
            self.show_error("Invalid sound", "The sound file doesn't exist")
            return
        if not self.validate_file_path(self.config["icon"]):
            self.show_error("Invalid icon", "The icon file doesn't exist")
            return
        self.save_config()
        self.show_info("Saved", "Configuration saved successfully")
        if self.tray_icon:
            self.tray_icon.set_from_file(self.config["icon"])

    # ── Start / stop daemon ────────────────────────────────────────────────────

    def on_start_stop(self, widget):
        if self.silenced:
            # botão no estado "silenciado" → retomar
            self.toggle_silenced()
        elif self.config["active"]:
            self.stop_service()
        else:
            self.start_service()

    def start_service(self):
        if not self.service_mode:
            self.on_save_config(None)
            if not self.config["times"] or not self.config["days"]:
                self.show_error("Incomplete config", "Define days and times first")
                return

        self.config["active"] = True
        self.save_config()
        if self.window:
            self.update_interface_state()
        self.log("Service started")

        if self.service_mode:
            self.run_service()
            return

        try:
            os.makedirs(SERVICE_DIR, exist_ok=True)
            with open(SCRIPT_FILE, "w") as f:
                f.write(
                    "#!/bin/bash\n"
                    f"exec >> {SERVICE_LOG} 2>> {SERVICE_ERROR_LOG}\n"
                    f"python3 {os.path.abspath(__file__)} --service\n"
                )
            os.chmod(SCRIPT_FILE, 0o755)
            self._svc_log_out = open(SERVICE_LOG, "a")
            self._svc_log_err = open(SERVICE_ERROR_LOG, "a")
            uid = os.getuid()
            daemon_env = os.environ.copy()
            bus_path = f"/run/user/{uid}/bus"
            if os.path.exists(bus_path):
                daemon_env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"
            if os.environ.get("DISPLAY"):
                daemon_env["DISPLAY"] = os.environ["DISPLAY"]

            self.process = subprocess.Popen(
                ["/bin/bash", SCRIPT_FILE],
                stdout=self._svc_log_out,
                stderr=self._svc_log_err,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                preexec_fn=os.setsid,
                env=daemon_env,
            )
            with open(PID_FILE, "w") as f:
                f.write(str(self.process.pid))
            self._refresh_daemon_status()
            self.show_info("Service started", "The scheduler is running in background")
        except Exception as e:
            self.show_error("Start failed", str(e))
            self.log(f"Start error: {e}", "error")
            self.config["active"] = False
            self.save_config()

    def stop_service(self):
        self.shutdown_event.set()
        self.sound_player.stop()
        if self.process:
            terminate_process(self.process)
            self.process = None
        for attr in ("_svc_log_out", "_svc_log_err"):
            fh = getattr(self, attr, None)
            if fh:
                try:
                    fh.close()
                except Exception:
                    pass
                setattr(self, attr, None)
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass
        self.config["active"] = False
        self.save_config()
        if self.window:
            self.update_interface_state()
        self._refresh_daemon_status()
        self.show_info("Service stopped", "The scheduler was stopped")
        self.log("Service stopped")

    # ── Service loop ───────────────────────────────────────────────────────────

    def run_service(self):
        self.log("Bell Scheduler Service started")
        self.shutdown_event.clear()

        # Garantir DBUS_SESSION_BUS_ADDRESS para notify-send funcionar
        uid = os.getuid()
        bus_path = f"/run/user/{uid}/bus"
        if not os.environ.get("DBUS_SESSION_BUS_ADDRESS") and os.path.exists(bus_path):
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_path}"
            self.log(f"DBUS_SESSION_BUS_ADDRESS: unix:path={bus_path}")

        # Usar DaemonSoundPlayer — sem GLib.idle_add, compatível com loop while
        daemon_player = DaemonSoundPlayer(self.log)
        self.log("Daemon iniciado")

        while not self.shutdown_event.is_set():
            try:
                self.check_config_updates()
                self.silenced = self.config.get("silenced", False)
                # Parar som se silenciado mudou para True
                if self.silenced:
                    daemon_player.stop()
                self.check_and_notify(daemon_player)
                self.shutdown_event.wait(self.config.get("check_interval", 5))
            except Exception as e:
                self.log(f"Service error: {e}", "error")
                self.shutdown_event.wait(30)

        daemon_player.stop()
        self.log("Bell Scheduler Service stopped")

    def check_and_notify(self, player=None):
        """Verifica horários e dispara som+notificação.
        player: DaemonSoundPlayer (daemon) ou None (GUI, não usado aqui).
        """
        now = datetime.datetime.now()
        today = now.date()

        for scheduled_time in self.config["times"]:
            try:
                sh, sm = map(int, scheduled_time.split(":"))
                diff = abs((now.hour - sh) * 60 + (now.minute - sm))
                if not (diff <= 1 and now.isoweekday() in self.config["days"]):
                    continue
                if self.last_played == (scheduled_time, today):
                    continue

                self.last_played = (scheduled_time, today)

                if self.silenced:
                    self.log(f"Silenciado — pulando {scheduled_time}")
                    continue

                self.log(f"Triggering bell for {scheduled_time}")
                sound_file = self.config["custom_sounds"].get(
                    scheduled_time, self.config["sound"]
                )
                if not self.validate_file_path(sound_file):
                    self.log(f"Sound file not found: {sound_file}", "error")
                    continue

                self.show_notification(
                    self.config["message"],
                    f"Time: {scheduled_time}",
                )

                active_player = player if player is not None else self.sound_player
                if not active_player.play(sound_file):
                    self.log(f"Failed to play: {sound_file}", "error")
            except ValueError:
                continue

    # ── i3 autostart ──────────────────────────────────────────────────────────

    def _i3_autostart_enabled(self) -> bool:
        if not os.path.isfile(I3_AUTOSTART_FILE):
            return False
        with open(I3_AUTOSTART_FILE) as f:
            return _EXEC_MARKER in f.read()

    def _i3_autostart_add(self):
        # autostart.conf pode não existir ainda — é seguro criar,
        # pois o include já está declarado no config principal.
        if not os.path.isdir(os.path.dirname(I3_AUTOSTART_FILE)):
            self.show_error(
                "Módulo i3 não encontrado",
                f"Diretório não existe:\n{os.path.dirname(I3_AUTOSTART_FILE)}\n\n"
                "Verifique se o seu i3 usa a estrutura modular esperada.",
            )
            return False
        if not os.path.isfile(I3_AUTOSTART_FILE):
            # Cria o arquivo vazio com cabeçalho
            with open(I3_AUTOSTART_FILE, "w") as f:
                f.write("# ----------------------------------------------------------------------------\n")
                f.write("# AUTOSTART\n")
                f.write("# ----------------------------------------------------------------------------\n")
        with open(I3_AUTOSTART_FILE) as f:
            content = f.read()
        if _EXEC_MARKER in content:
            return True  # já está
        with open(I3_AUTOSTART_FILE, "a") as f:
            f.write(f"\n{_EXEC_LINE}\n")
        return True

    def _i3_autostart_remove(self):
        if not os.path.isfile(I3_AUTOSTART_FILE):
            return
        with open(I3_AUTOSTART_FILE) as f:
            lines = f.readlines()
        filtered = [l for l in lines if _EXEC_MARKER not in l]
        with open(I3_AUTOSTART_FILE, "w") as f:
            f.writelines(filtered)

    def on_i3_autostart_toggled(self, switch, _param):
        if switch.get_active():
            if self._i3_autostart_add():
                self.show_info(
                    "i3 autostart enabled",
                    f"Added exec line to:\n{I3_AUTOSTART_FILE}\n\n"
                    "Restart i3 ($mod+Shift+r) for it to take effect.",
                )
                self.log("i3 autostart enabled")
            else:
                switch.set_active(False)
        else:
            self._i3_autostart_remove()
            self.show_info(
                "i3 autostart disabled",
                f"Removed exec line from:\n{I3_AUTOSTART_FILE}",
            )
            self.log("i3 autostart disabled")

    # ── Systemd user service ───────────────────────────────────────────────────

    def _systemd_unit_content(self) -> str:
        script = os.path.abspath(__file__)
        home = os.path.expanduser("~")
        uid = os.getuid()
        return (
            "[Unit]\n"
            "Description=Bell Scheduler Service\n"
            "After=graphical-session.target sound.target\n"
            "Wants=graphical-session.target\n"
            "StartLimitIntervalSec=60\n"
            "StartLimitBurst=3\n\n"
            "[Service]\n"
            "Type=simple\n"
            f"ExecStart=/usr/bin/python3 {script} --service\n"
            "Restart=on-failure\n"
            "RestartSec=10\n"
            f"WorkingDirectory={home}\n"
            "Environment=DISPLAY=:0\n"
            f"Environment=XAUTHORITY={home}/.Xauthority\n"
            f"Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus\n"
            f"StandardOutput=append:{SERVICE_LOG}\n"
            f"StandardError=append:{SERVICE_ERROR_LOG}\n\n"
            "[Install]\n"
            "WantedBy=default.target\n"
        )

    def on_install_systemd(self, widget):
        try:
            os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)
            with open(SYSTEMD_SERVICE, "w") as f:
                f.write(self._systemd_unit_content())
            rc, _, err = run_cmd("systemctl", "--user", "daemon-reload")
            if rc != 0:
                self.show_error("daemon-reload failed", err)
                return
            self.show_info(
                "Unit installed",
                f"Written to:\n{SYSTEMD_SERVICE}\n\n"
                "Click 'Enable & start' to activate.\n\n"
                "Note: on i3 you may need to run\n"
                "  systemctl --user import-environment\n"
                "after login so the service inherits DISPLAY.",
            )
            self.log("Systemd unit installed")
            self._refresh_daemon_status()
        except Exception as e:
            self.show_error("Install failed", str(e))

    def on_enable_systemd(self, widget):
        rc, _, err = run_cmd(
            "systemctl", "--user", "enable", "--now", "bell-scheduler.service"
        )
        if rc == 0:
            self.show_info("Enabled", "Service is active and will start at login.")
            self.log("Systemd service enabled")
        else:
            self.show_error("Enable failed", err or "Install the unit first.")
        self._refresh_daemon_status()

    def on_disable_systemd(self, widget):
        rc, _, err = run_cmd(
            "systemctl", "--user", "disable", "--now", "bell-scheduler.service"
        )
        if rc == 0:
            self.show_info("Disabled", "Service stopped and disabled.")
            self.log("Systemd service disabled")
        else:
            self.show_error("Disable failed", err)
        self._refresh_daemon_status()

    def on_cleanup_systemd(self, widget):
        """Detecta qualquer rastro do serviço antigo e limpa tudo."""
        report = []
        errors = []

        # 1. Verificar se está ativo
        _, out_active, _ = run_cmd("systemctl", "--user", "is-active", "bell-scheduler.service")
        if out_active in ("active", "activating", "deactivating"):
            rc, _, err = run_cmd("systemctl", "--user", "stop", "bell-scheduler.service")
            if rc == 0:
                report.append("✓ Serviço parado")
            else:
                errors.append(f"✗ Stop falhou: {err}")

        # 2. Verificar se está habilitado
        _, out_enabled, _ = run_cmd("systemctl", "--user", "is-enabled", "bell-scheduler.service")
        if out_enabled in ("enabled", "enabled-runtime", "static", "indirect"):
            rc, _, err = run_cmd("systemctl", "--user", "disable", "bell-scheduler.service")
            if rc == 0:
                report.append("✓ Serviço desabilitado")
            else:
                errors.append(f"✗ Disable falhou: {err}")

        # 3. Remover arquivo .service se existir
        if os.path.isfile(SYSTEMD_SERVICE):
            try:
                os.remove(SYSTEMD_SERVICE)
                report.append(f"✓ Arquivo removido:\n   {SYSTEMD_SERVICE}")
            except OSError as e:
                errors.append(f"✗ Remoção do .service falhou: {e}")

        # 4. daemon-reload para limpar o estado do systemd
        rc, _, err = run_cmd("systemctl", "--user", "daemon-reload")
        if rc == 0:
            report.append("✓ daemon-reload executado")
        else:
            errors.append(f"✗ daemon-reload falhou: {err}")

        # 5. Matar processo interno se houver
        if self.process and self.process.poll() is None:
            terminate_process(self.process)
            self.process = None
            report.append("✓ Processo interno encerrado")

        # 6. Remover PID file se existir
        if os.path.isfile(PID_FILE):
            try:
                os.remove(PID_FILE)
                report.append("✓ PID file removido")
            except OSError:
                pass

        # Resultado
        if not report and not errors:
            self.show_info(
                "Nada encontrado",
                "Nenhum serviço ativo, habilitado ou arquivo .service foi encontrado.\n"
                "O ambiente já está limpo.",
            )
        else:
            summary = "\n".join(report)
            if errors:
                summary += "\n\nErros:\n" + "\n".join(errors)
            self.show_info("Cleanup concluído", summary)

        self.log(f"Cleanup systemd: {'; '.join(report + errors)}")
        self._refresh_daemon_status()
        if self.window:
            self.update_interface_state()

    def _refresh_daemon_status(self):
        if not hasattr(self, "daemon_status_label"):
            return
        rc_active, out_active, _ = run_cmd(
            "systemctl", "--user", "is-active", "bell-scheduler.service"
        )
        rc_enabled, out_enabled, _ = run_cmd(
            "systemctl", "--user", "is-enabled", "bell-scheduler.service"
        )
        active = out_active == "active"
        enabled = out_enabled == "enabled"

        # Processo filho desta instância da GUI
        if self.process and self.process.poll() is None:
            active = True

        # Fallback: config diz active e PID file existe e processo vivo
        if not active and self.config.get("active", False):
            if os.path.isfile(PID_FILE):
                try:
                    with open(PID_FILE) as f:
                        pid = int(f.read().strip())
                    os.kill(pid, 0)
                    active = True
                except (ValueError, ProcessLookupError, OSError):
                    pass

        # Montar texto e cor considerando silêncio/snooze
        if not active:
            status_text = "○ inactive"
            color = "#888888"
        elif self.silenced:
            if self._snooze_remaining > 0:
                status_text = f"● ativo  🔇 snooze ({self._snooze_remaining}s)"
            else:
                status_text = "● ativo  🔇 silenciado"
            color = "#E65100"   # laranja — ativo mas suprimido
        else:
            status_text = "● active"
            color = "#4CAF50"   # verde — ativo e funcionando

        if enabled:
            status_text += "  (boot)"

        self.daemon_status_label.set_markup(
            f'<span foreground="{color}">{status_text}</span>'
        )

    # ── Interface ──────────────────────────────────────────────────────────────

    def update_interface_state(self):
        if self.window and hasattr(self, "start_button"):
            if self.silenced:
                self.start_button.set_label("🔇 Silenciado")
            elif self.config["active"]:
                self.start_button.set_label("⏹ Parar")
            else:
                self.start_button.set_label("▶ Iniciar")
        self._update_tray_tooltip()
        self._update_tray_icon()

    # ── Silenciar / retomar ───────────────────────────────────────────────────

    def toggle_silenced(self):
        """Liga/desliga o modo silenciado.
        - Silenciado ON:  para o toque atual imediatamente + suprime todos
          os próximos toques e notificações até ser desativado.
          O daemon continua rodando; ao retomar, os horários que passaram
          enquanto silenciado são marcados como já executados (não acumulam).
        - Silenciado OFF: volta ao funcionamento normal a partir do próximo
          horário agendado.
        O estado é persistido no config.json para o subprocesso daemon
        capturar no próximo ciclo (~5s).
        """
        # Cancela snooze ativo ao alternar manualmente
        if self._snooze_timer_id is not None:
            GLib.source_remove(self._snooze_timer_id)
            self._snooze_timer_id = None
            self._snooze_remaining = 0

        self.silenced = not self.silenced
        # ── persiste para o daemon subprocesso ler via config ──
        self.config["silenced"] = self.silenced
        self.save_config()
        if self.silenced:
            # 1. Para paplay da GUI (caso esteja em teste de som)
            if self.sound_player.is_playing:
                self.sound_player.stop()
            # 2. Mata paplay do daemon (processo separado)
            #    pkill -u $USER paplay envia SIGTERM a todos os paplay
            #    do usuário atual — seguro pois só este app usa paplay
            try:
                subprocess.run(
                    ["pkill", "-TERM", "-u", str(os.getuid()), "paplay"],
                    capture_output=True
                )
                self.log("pkill paplay enviado ao daemon")
            except Exception as e:
                self.log(f"pkill paplay falhou: {e}", "error")
            self.log("Modo silenciado ATIVADO — toques suprimidos")
        else:
            self.log("Modo silenciado DESATIVADO — agendamento retomado")
        GLib.idle_add(self._update_tray_tooltip)
        GLib.idle_add(self._update_tray_icon)
        if self.window:
            GLib.idle_add(self.update_interface_state)
            GLib.idle_add(self._refresh_daemon_status)

    def snooze_silenced(self, seconds: int = 60):
        """Silencia por N segundos e reativa automaticamente.
        Pode ser chamado enquanto já silenciado — reinicia a contagem.
        """
        # Cancela timer anterior se existir
        if self._snooze_timer_id is not None:
            GLib.source_remove(self._snooze_timer_id)
            self._snooze_timer_id = None

        # Para o som imediatamente
        if self.sound_player.is_playing:
            self.sound_player.stop()
        try:
            subprocess.run(
                ["pkill", "-TERM", "-u", str(os.getuid()), "paplay"],
                capture_output=True
            )
        except Exception:
            pass

        # Ativa silenced se ainda não estava
        if not self.silenced:
            self.silenced = True
            self.config["silenced"] = True
            self.save_config()

        self._snooze_remaining = seconds
        self.log(f"Snooze ativado por {seconds}s")

        # Tick a cada 1s para atualizar o tooltip com contagem regressiva
        self._snooze_timer_id = GLib.timeout_add(1000, self._snooze_tick)
        GLib.idle_add(self._update_tray_tooltip)
        GLib.idle_add(self._update_tray_icon)
        if self.window:
            GLib.idle_add(self.update_interface_state)

    def _snooze_tick(self) -> bool:
        """Chamado a cada 1s pelo GLib.timeout_add durante o snooze."""
        self._snooze_remaining -= 1
        GLib.idle_add(self._update_tray_tooltip)
        if self.window:
            GLib.idle_add(self._refresh_daemon_status)

        if self._snooze_remaining <= 0:
            # Tempo esgotado — reativa agendamento
            self._snooze_timer_id = None
            self.silenced = False
            self.config["silenced"] = False
            self.save_config()
            self.log("Snooze encerrado — agendamento retomado")
            GLib.idle_add(self._update_tray_tooltip)
            GLib.idle_add(self._update_tray_icon)
            if self.window:
                GLib.idle_add(self.update_interface_state)
                GLib.idle_add(self._refresh_daemon_status)
            return False  # para o timer
        return True  # continua o timer

    def _update_tray_tooltip(self):
        if not self.tray_icon:
            return False
        if self.silenced:
            if self._snooze_remaining > 0:
                tip = f"Bell Scheduler — 🔇 Snooze ({self._snooze_remaining}s restantes)"
            else:
                tip = "Bell Scheduler — 🔇 SILENCIADO (clique dir. → Retomar)"
        elif self.config["active"]:
            tip = "Bell Scheduler — ▶ Ativo"
        else:
            tip = "Bell Scheduler — ■ Parado"
        self.tray_icon.set_tooltip_text(tip)
        return False

    def _update_tray_icon(self):
        """Troca o ícone do tray: mudo=pause, parado=stop, normal=config."""
        if not self.tray_icon:
            return False
        if self.silenced:
            candidates = ["audio-volume-muted", "audio-volume-muted-symbolic",
                          "media-playback-pause", "media-playback-pause-symbolic"]
        elif not self.config["active"]:
            candidates = ["media-playback-stop", "media-playback-stop-symbolic"]
        else:
            candidates = []   # usa o ícone configurado pelo usuário

        theme = Gtk.IconTheme.get_default()
        for name in candidates:
            if theme.has_icon(name):
                self.tray_icon.set_from_icon_name(name)
                return False
        if self.validate_file_path(self.config["icon"]):
            self.tray_icon.set_from_file(self.config["icon"])
        return False

    # ── Tray icon ─────────────────────────────────────────────────────────────

    def on_icon_activate(self, icon, window=None):
        """Clique simples no tray: mostra ou esconde a janela."""
        if self.window is None:
            return
        if self.window.get_visible():
            self.window.hide()
        else:
            self.window.show_all()
            self.window.present()

    def on_icon_click(self, icon, button, time):
        """Botão direito no tray: menu de contexto."""
        menu = Gtk.Menu()

        def item(label, cb, sensitive=True):
            it = Gtk.MenuItem(label=label)
            it.connect("activate", cb)
            it.set_sensitive(sensitive)
            menu.append(it)

        def sep():
            menu.append(Gtk.SeparatorMenuItem())

        # ── Janela ────────────────────────────────────────────────────────
        item("Mostrar / Esconder", lambda _: self.on_icon_activate(icon))
        sep()

        # ── Silenciar / Retomar ───────────────────────────────────────────
        # Um único botão que alterna o estado silenciado:
        #   OFF → ON : para o som atual + suprime próximos toques
        #   ON  → OFF: retoma agendamento normalmente
        if self.silenced:
            if self._snooze_remaining > 0:
                item(f"▶  Retomar agora ({self._snooze_remaining}s restantes)",
                     lambda _: self.toggle_silenced())
            else:
                item("▶  Retomar agendamento", lambda _: self.toggle_silenced())
        else:
            if self.sound_player.is_playing:
                label_sil = "🔇  Silenciar agora + suprimir próximos"
            else:
                label_sil = "🔇  Silenciar agendamento"
            item(label_sil, lambda _: self.toggle_silenced(),
                 sensitive=self.config["active"])
            item("⏱  Snooze 60s (retoma automaticamente)",
                 lambda _: self.snooze_silenced(60),
                 sensitive=self.config["active"])
        sep()

        # ── Scheduler on/off ──────────────────────────────────────────────
        if self.config["active"]:
            item("⏹  Parar scheduler", lambda _: self.stop_service())
        else:
            item("▶  Iniciar scheduler", lambda _: self.start_service())
        sep()

        # ── App ───────────────────────────────────────────────────────────
        item("Sair", lambda _: self.quit())

        menu.show_all()
        menu.popup(None, None, None, None, button, time)

    def on_window_close(self, window, event):
        """Esconde a janela em vez de fechar — app continua no tray."""
        window.hide()
        return True

    def show_error(self, title: str, message: str):
        d = Gtk.MessageDialog(
            transient_for=self.window, modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=title,
        )
        d.format_secondary_text(message)
        d.run()
        d.destroy()
        self.log(f"Error: {title} — {message}", "error")

    def show_info(self, title: str, message: str):
        d = Gtk.MessageDialog(
            transient_for=self.window, modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK, text=title,
        )
        d.format_secondary_text(message)
        d.run()
        d.destroy()
        self.log(f"Info: {title} — {message}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bell Scheduler")
    parser.add_argument("--service",   action="store_true",
                        help="Rodar em modo daemon (sem GUI)")
    parser.add_argument("--autostart", action="store_true",
                        help="Iniciado pelo i3 exec: sobe daemon automaticamente")
    parser.add_argument("--check-interval", type=int)
    args, remaining = parser.parse_known_args()
    app = BellSchedulerApp(
        service_mode=args.service,
        autostart_mode=args.autostart,
    )
    if args.check_interval and args.service:
        app.check_interval = args.check_interval
    app.run(sys.argv)
