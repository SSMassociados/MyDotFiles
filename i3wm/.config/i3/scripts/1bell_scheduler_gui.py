#!/usr/bin/env python3
# Agendador de Campainha com Interface GTK - Versão Completa Corrigida

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
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from gi.repository import Gtk, Gdk, GLib, Gio, Notify
from typing import List, Dict, Optional, Tuple, Set, Any

# Configurações de arquivos
CONFIG_DIR = os.path.expanduser("~/.config/bell_scheduler")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PID_FILE = os.path.join(CONFIG_DIR, "bell_scheduler.pid")
LOG_FILE = os.path.join(CONFIG_DIR, "bell_scheduler.log")
SCRIPT_FILE = os.path.join(CONFIG_DIR, "bell_scheduler.sh")
SERVICE_LOG = os.path.join(CONFIG_DIR, "service.log")
SERVICE_ERROR_LOG = os.path.join(CONFIG_DIR, "service_error.log")

# Verificar e criar diretório de configuração
os.makedirs(CONFIG_DIR, exist_ok=True, mode=0o755)

class AudioPlayer:
    def __init__(self):
        self.current_stream: Optional[sd.OutputStream] = None
        self.stop_playback = threading.Event()
        self.is_playing = False
        self.audio_data: Optional[np.ndarray] = None
        self.samplerate: Optional[int] = None
        self.position = 0
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        self.last_playback_error: Optional[str] = None
    
    def validate_audio_file(self, file_path: str) -> bool:
        """Valida se o arquivo de áudio é válido e legível"""
        try:
            with sf.SoundFile(file_path) as f:
                if f.channels not in (1, 2):
                    self.last_playback_error = f"Número de canais não suportado: {f.channels}"
                    return False
                if f.samplerate < 8000 or f.samplerate > 192000:
                    self.last_playback_error = f"Taxa de amostragem não suportada: {f.samplerate}"
                    return False
            return True
        except Exception as e:
            self.last_playback_error = str(e)
            return False
    
    def play(self, file_path: str) -> bool:
        """Reproduz um arquivo de áudio com capacidade de interrupção"""
        try:
            with self.lock:
                if self.is_playing:
                    self._stop_internal()
                
                if not self.validate_audio_file(file_path):
                    self.logger.error(f"Arquivo de áudio inválido: {self.last_playback_error}")
                    return False
                
                self.stop_playback.clear()
                self.audio_data, self.samplerate = sf.read(file_path, always_2d=True)
                self.position = 0
                
                self.is_playing = True
                self.current_stream = sd.OutputStream(
                    samplerate=self.samplerate,
                    channels=self.audio_data.shape[1],
                    callback=self.audio_callback,
                    finished_callback=self.playback_finished
                )
                self.current_stream.start()
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao reproduzir áudio: {str(e)}")
            self.last_playback_error = str(e)
            self._cleanup_playback()
            return False

    def audio_callback(self, outdata: np.ndarray, frames: int, time: Any, status: sd.CallbackFlags) -> None:
        """Callback para streaming de áudio"""
        if self.stop_playback.is_set():
            raise sd.CallbackAbort
        
        if not self.is_playing:  # Adicionado para evitar acesso quando não está playing
            raise sd.CallbackStop
            
        try:
            with self.lock:
                if self.position >= len(self.audio_data):
                    raise sd.CallbackStop
                
                available = len(self.audio_data) - self.position
                frames_to_write = min(frames, available)
                
                if frames_to_write > 0:
                    outdata[:frames_to_write] = self.audio_data[self.position:self.position + frames_to_write]
                    self.position += frames_to_write
                
                if frames_to_write < frames:
                    outdata[frames_to_write:] = 0
                    raise sd.CallbackStop
        except Exception as e:
            self.logger.error(f"Erro no callback de áudio: {str(e)}")
            self.last_playback_error = str(e)
            raise sd.CallbackAbort

    def playback_finished(self) -> None:
        """Chamado quando a reprodução termina"""
        self._cleanup_playback()  # Removido o with self.lock para evitar deadlock

    def _cleanup_playback(self) -> None:
        """Limpeza dos recursos de playback"""
        with self.lock:
            self.is_playing = False
            if self.current_stream:
                try:
                    self.current_stream.close()
                except:
                    pass
            self.current_stream = None
            self.audio_data = None
            self.position = 0

    def _stop_internal(self) -> None:
        """Método interno para parar a reprodução"""
        if self.is_playing and self.current_stream:
            self.stop_playback.set()
            try:
                # Não usamos mais stop() pois pode causar deadlock
                self._cleanup_playback()
            except Exception as e:
                self.logger.error(f"Erro ao parar stream: {str(e)}")

    def stop(self) -> bool:
        """Interrompe a reprodução atual"""
        start_time = time.time()
        while self.is_playing and (time.time() - start_time) < 3.0:
            self._stop_internal()
            time.sleep(0.1)
        
        if self.is_playing:
            self.logger.warning("Timeout ao parar reprodução")
            return False
        return True

class BellSchedulerApp(Gtk.Application):
    def __init__(self, service_mode: bool = False):
        flags = Gio.ApplicationFlags.FLAGS_NONE
        if not service_mode:
            flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE
            
        super().__init__(
            application_id="com.example.BellScheduler",
            flags=flags
        )
        self.process: Optional[subprocess.Popen] = None
        self.service_mode = service_mode
        self.tray_icon: Optional[Gtk.StatusIcon] = None
        self.logger = self.setup_logging()
        self.keep_running = True
        self.window: Optional[Gtk.Window] = None
        self.check_interval = 10
        self.audio_player = AudioPlayer()
        self.last_notification_time: Dict[str, float] = {}
        
        # Configuração padrão
        self.config = {
            "times": ["08:00", "10:00", "12:00", "14:00", "16:00"],
            "days": [1, 2, 3, 4, 5],  # 1=Segunda, 2=Terça, ..., 7=Domingo
            "message": "Hora da campainha!",
            "sound": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "icon": "/usr/share/icons/gnome/256x256/status/appointment-soon.png",
            "active": False,
            "check_interval": 10,
            "custom_sounds": {},
            "min_notification_interval": 60  # Evita notificações duplicadas em 60 segundos
        }
        
        self.load_config()

    def setup_logging(self) -> logging.Logger:
        """Configura o sistema de logging"""
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        logger = logging.getLogger(__name__)
        
        # Configurar logging para stderr também
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger

    def load_config(self) -> bool:
        """Carrega a configuração do arquivo"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_salva = json.load(f)
                    
                    # Atualiza apenas as chaves existentes na configuração padrão
                    for key in self.config:
                        if key in config_salva:
                            self.config[key] = config_salva[key]
                            
                    # Validação de tipos
                    if not isinstance(self.config["times"], list):
                        self.config["times"] = []
                    if not isinstance(self.config["days"], list):
                        self.config["days"] = []
                    if not isinstance(self.config["custom_sounds"], dict):
                        self.config["custom_sounds"] = {}
                    
                self.logger.info("Configuração carregada com sucesso")
                return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {str(e)}")
            # Se houver erro, mantém a configuração padrão
            return False

    def save_config(self) -> bool:
        """Salva a configuração no arquivo"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info("Configuração salva com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {str(e)}")
            return False

    def validate_time(self, time_str: str) -> bool:
        """Valida o formato de horário HH:MM"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return 0 <= hours < 24 and 0 <= minutes < 60
        except ValueError:
            return False

    def validate_file_path(self, path: str) -> bool:
        """Valida se o caminho do arquivo é válido e acessível"""
        try:
            return bool(path) and os.path.isfile(path) and os.access(path, os.R_OK)
        except (TypeError, ValueError):
            return False

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        """Manipula argumentos da linha de comando"""
        self.activate()
        return 0

    def do_activate(self) -> None:
        """Manipula a ativação da aplicação"""
        if not self.service_mode:
            if self.window is None:
                self.create_main_window()
            else:
                self.window.present()

    def create_main_window(self) -> None:
        """Cria e configura a janela principal"""
        self.window = Gtk.ApplicationWindow(
            application=self,
            title="Agendador de Campainha"
        )
        self.window.set_default_size(450, 400)
        self.window.set_border_width(4)

        # Configuração CSS
        self.setup_styles()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.window.add(main_box)
            
        # Configurar ícone na bandeja
        if not self.service_mode:
            self.setup_tray_icon()

        # Seção de dias da semana
        days_frame = Gtk.Frame(label="Dias da Semana")
        days_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, margin=4, homogeneous=True)
        days_frame.add(days_box)

        self.day_buttons = []
        days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for i, day in enumerate(days):
            btn = Gtk.ToggleButton(label=day)
            btn.set_active(i+1 in self.config["days"])
            btn.connect("toggled", self.on_day_toggled, i+1)
            btn.get_style_context().add_class("compact-button")
            days_box.pack_start(btn, True, True, 0)
            self.day_buttons.append(btn)

        main_box.pack_start(days_frame, False, False, 0)

        # Seção de horários
        times_frame = Gtk.Frame(label="Horários")
        times_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        times_frame.add(times_box)

        self.times_list = Gtk.ListBox()
        self.times_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.update_times_list()
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.times_list)
        times_box.pack_start(scroll, True, True, 0)

        add_box = Gtk.Box(spacing=4, margin=2)
        self.time_entry = Gtk.Entry(placeholder_text="HH:MM")
        btn_add = Gtk.Button(label="Adicionar")
        btn_add.connect("clicked", self.on_add_time)
        add_box.pack_start(self.time_entry, True, True, 0)
        add_box.pack_start(btn_add, False, False, 0)
        times_box.pack_start(add_box, False, False, 0)

        main_box.pack_start(times_frame, True, True, 0)

        # Configurações
        config_frame = Gtk.Frame(label="Configurações")
        config_grid = Gtk.Grid(column_spacing=6, row_spacing=6, margin=4)
        config_frame.add(config_grid)

        # Mensagem
        config_grid.attach(Gtk.Label(label="Mensagem:"), 0, 0, 1, 1)
        self.message_entry = Gtk.Entry()
        self.message_entry.set_text(self.config["message"])
        config_grid.attach(self.message_entry, 1, 0, 1, 1)

        # Som
        config_grid.attach(Gtk.Label(label="Som padrão:"), 0, 1, 1, 1)
        sound_box = Gtk.Box(spacing=4)
        self.sound_entry = Gtk.Entry()
        self.sound_entry.set_text(self.config["sound"])
        btn_sound = Gtk.Button(label="Procurar")
        btn_sound.connect("clicked", self.on_browse_sound)
        btn_preview = Gtk.Button(label="Testar")
        btn_preview.connect("clicked", self.on_test_sound)
        self.btn_stop = Gtk.Button.new_from_icon_name("audio-volume-muted-symbolic", Gtk.IconSize.BUTTON)
        self.btn_stop.connect("clicked", self.on_stop_sound)
        self.btn_stop.set_tooltip_text("Nenhum áudio sendo reproduzido")
        self.btn_stop.set_sensitive(False)
        self.btn_stop.get_style_context().add_class("mute-button")
        sound_box.pack_start(self.sound_entry, True, True, 0)
        sound_box.pack_start(btn_sound, False, False, 0)
        sound_box.pack_start(btn_preview, False, False, 0)
        sound_box.pack_start(self.btn_stop, False, False, 0)
        config_grid.attach(sound_box, 1, 1, 1, 1)

        # Ícone
        config_grid.attach(Gtk.Label(label="Ícone:"), 0, 2, 1, 1)
        icon_box = Gtk.Box(spacing=4)
        self.icon_entry = Gtk.Entry()
        self.icon_entry.set_text(self.config["icon"])
        btn_icon = Gtk.Button(label="Procurar")
        btn_icon.connect("clicked", self.on_browse_icon)
        btn_preview_icon = Gtk.Button(label="Visualizar")
        btn_preview_icon.connect("clicked", self.on_preview_icon)
        icon_box.pack_start(self.icon_entry, True, True, 0)
        icon_box.pack_start(btn_icon, False, False, 0)
        icon_box.pack_start(btn_preview_icon, False, False, 0)
        config_grid.attach(icon_box, 1, 2, 1, 1)

        # Intervalo
        config_grid.attach(Gtk.Label(label="Intervalo (segundos):"), 0, 3, 1, 1)
        self.interval_entry = Gtk.SpinButton.new_with_range(5, 60, 1)
        self.interval_entry.set_value(self.config.get("check_interval", 10))
        config_grid.attach(self.interval_entry, 1, 3, 1, 1)

        main_box.pack_start(config_frame, False, False, 0)

        # Botões de controle
        btn_box = Gtk.Box(spacing=6, margin=2)
        self.btn_start = Gtk.Button(label="Iniciar")
        self.btn_start.connect("clicked", self.on_start_stop)
        self.btn_start.get_style_context().add_class("suggested-action")
        btn_box.pack_start(self.btn_start, True, True, 0)

        btn_save = Gtk.Button(label="Salvar Configuração")
        btn_save.connect("clicked", self.on_save_config)
        btn_box.pack_start(btn_save, True, True, 0)

        main_box.pack_start(btn_box, False, False, 0)
        self.update_ui_state()

        self.window.connect("delete-event", self.on_window_close)
        self.window.show_all()

    def setup_styles(self) -> None:
        """Configura os estilos CSS da aplicação"""
        css_provider = Gtk.CssProvider()
        css = """
            .compact-button {
                padding: 2px 4px;
                margin: 0 2px;
                min-width: 40px;
            }
            .suggested-action {
                background-color: #4CAF50;
                color: white;
            }
            .destructive-action {
                background-color: #ff4444;
                color: white;
            }
            .mute-button {
                padding: 2px;
                border: none;
                background: none;
            }
            .error-label {
                color: #ff4444;
                font-size: 0.9em;
            }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_tray_icon(self) -> None:
        """Configura o ícone na bandeja do sistema"""
        try:
            Notify.init("BellScheduler")
            self.tray_icon = Gtk.StatusIcon.new_from_file(self.config["icon"])
            self.tray_icon.set_tooltip_text("Agendador de Campainha")
            self.tray_icon.connect("activate", self.on_tray_activate)
            self.tray_icon.connect("popup-menu", self.on_tray_popup)
        except Exception as e:
            self.logger.error(f"Erro ao configurar ícone de bandeja: {str(e)}")

    def update_times_list(self) -> None:
        """Atualiza a lista de horários na interface"""
        for child in self.times_list.get_children():
            self.times_list.remove(child)

        for time_str in sorted(self.config["times"]):
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row.add(box)

            label = Gtk.Label(label=time_str, xalign=0)
            box.pack_start(label, True, True, 0)

            if time_str in self.config.get("custom_sounds", {}):
                icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.MENU)
                box.pack_start(icon, False, False, 0)

            btn_edit = Gtk.Button.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.MENU)
            btn_edit.connect("clicked", lambda b, h=time_str: self.on_edit_time(h))
            box.pack_start(btn_edit, False, False, 0)

            btn_remove = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.MENU)
            btn_remove.connect("clicked", lambda b, h=time_str: self.on_remove_time(h))
            box.pack_start(btn_remove, False, False, 0)

            self.times_list.add(row)
        
        self.times_list.show_all()

    def on_day_toggled(self, button: Gtk.ToggleButton, day: int) -> None:
        """Atualiza os dias ativados quando um botão é alternado"""
        if button.get_active():
            if day not in self.config["days"]:
                self.config["days"].append(day)
        else:
            if day in self.config["days"]:
                self.config["days"].remove(day)
        self.config["days"].sort()

    def on_add_time(self, button: Gtk.Button) -> None:
        """Adiciona um novo horário à lista"""
        time_str = self.time_entry.get_text().strip()
        if not self.validate_time(time_str):
            self.show_error("Formato inválido", "Use HH:MM (24 horas)")
            return

        if time_str in self.config["times"]:
            self.show_error("Horário duplicado", "Este horário já está na lista")
            return

        self.config["times"].append(time_str)
        self.update_times_list()
        self.time_entry.set_text("")

    def on_edit_time(self, old_time: str) -> None:
        """Mostra diálogo para edição de horário"""
        dialog = Gtk.Dialog(title="Editar Horário", transient_for=self.window, flags=0)
        dialog.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)

        content = dialog.get_content_area()
        box = Gtk.Box(spacing=6)
        content.add(box)
        
        box.pack_start(Gtk.Label(label="Novo horário:"), False, False, 0)
        entry = Gtk.Entry(text=old_time)
        box.pack_start(entry, True, True, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_time = entry.get_text().strip()
            if self.validate_time(new_time):
                if new_time != old_time and new_time in self.config["times"]:
                    self.show_error("Horário existe", "Este horário já está na lista")
                else:
                    if old_time in self.config["custom_sounds"]:
                        self.config["custom_sounds"][new_time] = self.config["custom_sounds"].pop(old_time)
                    index = self.config["times"].index(old_time)
                    self.config["times"][index] = new_time
                    self.update_times_list()
            else:
                self.show_error("Formato inválido", "Use HH:MM (24 horas)")
        
        dialog.destroy()

    def on_remove_time(self, time_str: str) -> None:
        """Remove um horário da lista"""
        if time_str in self.config["times"]:
            if time_str in self.config.get("custom_sounds", {}):
                del self.config["custom_sounds"][time_str]
            self.config["times"].remove(time_str)
            self.update_times_list()

    def on_test_sound(self, widget: Gtk.Widget) -> None:
        """Testa o som selecionado"""
        sound_file = self.sound_entry.get_text()
        if not self.validate_file_path(sound_file):
            self.show_error("Arquivo inválido", "O arquivo de som não pode ser acessado")
            return

        try:
            if self.audio_player.play(sound_file):
                self.update_stop_button(True)
                self.show_info("Reproduzindo", f"Som: {os.path.basename(sound_file)}")
            else:
                self.show_error("Erro ao reproduzir", f"Detalhes: {self.audio_player.last_playback_error}")
        except Exception as e:
            self.show_error("Erro ao reproduzir som", f"Detalhes: {str(e)}")
            self.logger.error(f"Erro ao reproduzir som {sound_file}: {str(e)}")

    def on_stop_sound(self, widget: Gtk.Widget) -> None:
        """Para a reprodução de áudio atual"""
        if self.audio_player.stop():
            self.update_stop_button(False)
            self.show_info("Áudio parado", "A reprodução foi interrompida")
            self.logger.info("Reprodução de áudio interrompida pelo usuário")
        else:
            self.show_error("Erro", "Não foi possível parar a reprodução")

    def on_preview_icon(self, widget: Gtk.Widget) -> None:
        """Mostra uma pré-visualização do ícone selecionado"""
        icon_file = self.icon_entry.get_text()
        if self.validate_file_path(icon_file):
            dialog = Gtk.Dialog(title="Visualização de Ícone", transient_for=self.window, flags=0)
            dialog.add_buttons("Fechar", Gtk.ResponseType.CLOSE)
            
            content = dialog.get_content_area()
            image = Gtk.Image.new_from_file(icon_file)
            image.set_pixel_size(128)
            content.add(image)
            
            dialog.show_all()
            dialog.run()
            dialog.destroy()
        else:
            self.show_error("Arquivo inválido", "O arquivo de ícone não pode ser acessado")

    def on_browse_sound(self, widget: Gtk.Widget) -> None:
        """Abre diálogo para selecionar arquivo de som"""
        dialog = Gtk.FileChooserDialog(
            title="Selecione um arquivo de som",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons("_Cancelar", Gtk.ResponseType.CANCEL, "_Abrir", Gtk.ResponseType.OK)

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Arquivos de som")
        filter_audio.add_mime_type("audio/*")
        dialog.add_filter(filter_audio)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("Todos os arquivos")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if self.validate_file_path(filename):
                self.sound_entry.set_text(filename)
        
        dialog.destroy()

    def on_browse_icon(self, widget: Gtk.Widget) -> None:
        """Abre diálogo para selecionar arquivo de ícone"""
        dialog = Gtk.FileChooserDialog(
            title="Selecione um ícone",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons("_Cancelar", Gtk.ResponseType.CANCEL, "_Abrir", Gtk.ResponseType.OK)

        filter_image = Gtk.FileFilter()
        filter_image.set_name("Imagens")
        filter_image.add_mime_type("image/*")
        dialog.add_filter(filter_image)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("Todos os arquivos")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if self.validate_file_path(filename):
                self.icon_entry.set_text(filename)
        
        dialog.destroy()

    def on_save_config(self, widget: Gtk.Widget) -> None:
        """Salva as configurações atuais"""
        self.config["message"] = self.message_entry.get_text()
        self.config["sound"] = self.sound_entry.get_text()
        self.config["icon"] = self.icon_entry.get_text()
        self.config["check_interval"] = self.interval_entry.get_value()
        
        if not self.validate_file_path(self.config["sound"]):
            self.show_error("Som inválido", "O arquivo de som não existe")
            return
            
        if not self.validate_file_path(self.config["icon"]):
            self.show_error("Ícone inválido", "O arquivo de ícone não existe")
            return
        
        if self.save_config():
            self.show_info("Configuração salva", "As configurações foram salvas com sucesso")
            if self.tray_icon:
                self.tray_icon.set_from_file(self.config["icon"])

    def on_start_stop(self, widget: Gtk.Widget) -> None:
        """Inicia ou para o serviço"""
        if self.config["active"]:
            self.stop_service()
        else:
            self.start_service()

    def start_service(self) -> None:
        """Inicia o serviço em background"""
        if not self.service_mode:
            self.on_save_config(None)
            
            if not self.config["times"] or not self.config["days"]:
                self.show_error("Configuração incompleta", "Defina dias e horários primeiro")
                return

        self.config["active"] = True
        self.save_config()
        self.update_ui_state()
        self.show_info("Serviço iniciado", "O agendador está em execução")
        self.logger.info("Serviço iniciado")
        
        if self.service_mode:
            self.run_service()
        else:
            try:
                # Cria script de inicialização
                script_content = f"""#!/bin/bash
# Bell Scheduler Service Script
# Generated on {datetime.datetime.now().isoformat()}

# Redirect all output to log files
exec >> "{SERVICE_LOG}" 2>> "{SERVICE_ERROR_LOG}"

# Export necessary environment variables
export DISPLAY=:0
export XAUTHORITY={os.path.expanduser("~/.Xauthority")}
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID/bus

# Run the service
python3 "{os.path.abspath(__file__)}" --service
"""
                with open(SCRIPT_FILE, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                os.chmod(SCRIPT_FILE, 0o755)
                
                # Inicia o processo
                self.process = subprocess.Popen(
                    ["/bin/bash", SCRIPT_FILE],
                    stdout=open(SERVICE_LOG, 'a'),
                    stderr=open(SERVICE_ERROR_LOG, 'a'),
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                    preexec_fn=os.setsid
                )
                
                # Salva o PID
                with open(PID_FILE, 'w', encoding='utf-8') as f:
                    f.write(str(self.process.pid))
                
                # Verifica se o processo está rodando após 1 segundo
                time.sleep(1)
                if self.process.poll() is not None:
                    raise subprocess.SubprocessError("Processo terminou imediatamente")
                
            except Exception as e:
                self.show_error("Erro", f"Erro ao iniciar serviço: {str(e)}")
                self.logger.error(f"Erro ao iniciar serviço: {str(e)}")
                self.config["active"] = False
                self.save_config()
                try:
                    if self.process:
                        self.process.terminate()
                except:
                    pass

    def stop_service(self) -> None:
        """Para o serviço em execução"""
        self.keep_running = False
        
        # Tenta parar o processo de forma limpa
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), 15)  # SIGTERM
                self.process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired) as e:
                self.logger.error(f"Erro ao parar serviço: {str(e)}")
                try:
                    os.killpg(os.getpgid(self.process.pid), 9)  # SIGKILL
                except ProcessLookupError:
                    pass
            finally:
                self.process = None
        
        # Remove o arquivo PID
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass
        
        self.config["active"] = False
        self.save_config()
        self.update_ui_state()
        self.show_info("Serviço parado", "O agendador foi parado")
        self.logger.info("Serviço parado")

    def run_service(self) -> None:
        """Método principal de execução do serviço"""
        self.logger.info("Serviço do Agendador de Campainha iniciado")
        
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus()
            Notify.init("BellScheduler")
        except Exception as e:
            self.logger.error(f"Erro de inicialização: {str(e)}")
            return
        
        try:
            while self.keep_running:
                try:
                    self.check_and_notify()
                    time.sleep(self.config.get("check_interval", 10))
                except Exception as e:
                    self.logger.error(f"Erro no serviço: {str(e)}")
                    time.sleep(30)
        finally:
            if Notify.is_initted():
                Notify.uninit()
            self.logger.info("Serviço do Agendador de Campainha encerrado")

    def check_and_notify(self) -> None:
        """Verifica os horários e dispara notificações quando necessário"""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.isoweekday()
        current_timestamp = time.time()
        
        # Verifica se é um dia e horário programado
        if current_day in self.config["days"] and current_time in self.config["times"]:
            # Verifica se já notificou recentemente para evitar duplicatas
            last_notification = self.last_notification_time.get(current_time, 0)
            min_interval = self.config.get("min_notification_interval", 60)
            
            if current_timestamp - last_notification >= min_interval:
                self.last_notification_time[current_time] = current_timestamp
                self.logger.info(f"Disparando notificação para {current_time}")
                
                try:
                    sound_file = self.config["custom_sounds"].get(current_time, self.config["sound"])
                    
                    notification = Notify.Notification.new(
                        self.config["message"],
                        f"Hora atual: {current_time}",
                        self.config["icon"]
                    )
                    notification.set_urgency(2)
                    notification.show()
                    
                    self.audio_player.play(sound_file)
                    GLib.idle_add(self.update_stop_button, True)
                except Exception as e:
                    self.logger.error(f"Erro na notificação: {str(e)}")

    def update_ui_state(self) -> None:
        """Atualiza o estado dos botões na interface"""
        if self.config["active"]:
            self.btn_start.set_label("Parar")
            self.btn_start.get_style_context().remove_class("suggested-action")
            self.btn_start.get_style_context().add_class("destructive-action")
        else:
            self.btn_start.set_label("Iniciar")
            self.btn_start.get_style_context().remove_class("destructive-action")
            self.btn_start.get_style_context().add_class("suggested-action")

    def update_stop_button(self, playing: bool) -> None:
        """Atualiza o estado do botão de parar"""
        self.btn_stop.set_sensitive(playing)
        icon = "media-playback-stop-symbolic" if playing else "audio-volume-muted-symbolic"
        image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
        self.btn_stop.set_image(image)
        self.btn_stop.set_tooltip_text("Parar reprodução" if playing else "Nenhum áudio sendo reproduzido")

    def on_tray_activate(self, icon: Gtk.StatusIcon) -> None:
        """Mostra ou oculta a janela principal ao clicar no ícone"""
        if self.window.get_visible():
            self.window.hide()
        else:
            self.window.present()

    def on_tray_popup(self, icon: Gtk.StatusIcon, button: int, time: int) -> None:
        """Mostra menu de contexto ao clicar com botão direito no ícone"""
        menu = Gtk.Menu()
        
        item_show = Gtk.MenuItem(label="Mostrar/Ocultar")
        item_show.connect("activate", self.on_tray_activate)
        menu.append(item_show)
        
        action_label = "Parar" if self.config["active"] else "Iniciar"
        item_action = Gtk.MenuItem(label=action_label)
        item_action.connect("activate", self.on_start_stop, None)
        menu.append(item_action)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        item_quit = Gtk.MenuItem(label="Sair")
        item_quit.connect("activate", lambda x: self.quit())
        menu.append(item_quit)
        
        menu.show_all()
        menu.popup(None, None, None, None, button, time)

    def on_window_close(self, window: Gtk.Window, event: Gdk.Event) -> bool:
        """Esconde a janela em vez de fechar"""
        window.hide()
        return True

    def show_error(self, title: str, message: str) -> None:
        """Mostra diálogo de erro"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        self.logger.error(f"Erro: {title} - {message}")

    def show_info(self, title: str, message: str) -> None:
        """Mostra diálogo informativo"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        self.logger.info(f"Info: {title} - {message}")

def install_systemd_service() -> bool:
    """Instala o serviço systemd para o usuário"""
    try:
        service_content = f"""[Unit]
Description=Serviço do Agendador de Campainha
After=network.target sound.target graphical-session.target
Wants=graphical-session.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
ExecStart=/usr/bin/python3 {os.path.abspath(__file__)} --service
Restart=on-failure
RestartSec=10
WorkingDirectory={os.path.expanduser("~")}
Environment=DISPLAY=:0
Environment=XAUTHORITY={os.path.expanduser("~/.Xauthority")}
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus
StandardOutput=append:{SERVICE_LOG}
StandardError=append:{SERVICE_ERROR_LOG}

[Install]
WantedBy=default.target
"""

        service_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(service_dir, exist_ok=True, mode=0o755)
        
        service_path = os.path.join(service_dir, "bell-scheduler.service")
        
        with open(service_path, 'w', encoding='utf-8') as f:
            f.write(service_content)
        
        print(f"Serviço instalado em: {service_path}")
        print("\nPara ativar o serviço, execute:")
        print("systemctl --user enable bell-scheduler.service")
        print("systemctl --user start bell-scheduler.service")
        print("\nPara verificar o status:")
        print("systemctl --user status bell-scheduler.service")
        print("\nPara visualizar os logs:")
        print(f"tail -f {SERVICE_LOG}")
        return True
    except Exception as e:
        print(f"Erro ao instalar serviço: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Agendador de Campainha')
    parser.add_argument('--service', action='store_true', help='Executa em modo serviço')
    parser.add_argument('--install-service', action='store_true', help='Instala como serviço systemd')
    parser.add_argument('--check-interval', type=int, help='Intervalo de verificação em segundos')
    args = parser.parse_args()

    if args.install_service:
        if install_systemd_service():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        app = BellSchedulerApp(service_mode=args.service)
        if args.check_interval and args.service:
            app.check_interval = args.check_interval
        app.run(sys.argv)
