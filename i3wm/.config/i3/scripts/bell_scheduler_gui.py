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
from typing import List, Dict, Optional, Tuple, Set, Any

# Configuration files
CONFIG_FILE = os.path.expanduser("~/.bell_scheduler_config.json")
PID_FILE = os.path.expanduser("~/.bell_scheduler.pid")
LOG_FILE = os.path.expanduser("~/.bell_scheduler.log")
SCRIPT_FILE = os.path.expanduser("~/.bell_scheduler.sh")
SERVICE_LOG = os.path.expanduser("~/.bell_scheduler/service.log")
SERVICE_ERROR_LOG = os.path.expanduser("~/.bell_scheduler/service_error.log")

class SoundPlayer:
    def __init__(self, app):
        self.app = app
        self.current_process = None
        self.is_playing = False
        self.lock = threading.Lock()
        
    def play(self, sound_file):
        """Play sound file"""
        with self.lock:
            if self.is_playing:
                self.stop()
            
            if not self.app.validate_file_path(sound_file):
                self.app.log(f"Invalid sound file: {sound_file}", "error")
                return False

            try:
                self.is_playing = True
                GLib.idle_add(self.app.update_sound_controls)
                
                self.current_process = subprocess.Popen(
                    ["paplay", sound_file],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                
                def monitor_process():
                    self.current_process.wait()
                    with self.lock:
                        self.is_playing = False
                        self.current_process = None
                    GLib.idle_add(self.app.update_sound_controls)
                
                threading.Thread(target=monitor_process, daemon=True).start()
                return True
                
            except Exception as e:
                self.app.log(f"Error playing sound: {str(e)}", "error")
                with self.lock:
                    self.is_playing = False
                    self.current_process = None
                GLib.idle_add(self.app.update_sound_controls)
                return False
    
    def stop(self):
        """Stop current playback"""
        with self.lock:
            if self.is_playing and self.current_process:
                try:
                    os.killpg(os.getpgid(self.current_process.pid), 15)
                    try:
                        self.current_process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        os.killpg(os.getpgid(self.current_process.pid), 9)
                except ProcessLookupError:
                    pass
                finally:
                    self.is_playing = False
                    self.current_process = None
                    GLib.idle_add(self.app.update_sound_controls)
                    
                    try:
                        notification = Notify.Notification.new(
                            "Sound stopped",
                            "Playback was successfully stopped",
                            self.app.config["icon"]
                        )
                        notification.show()
                    except Exception as e:
                        self.app.log(f"Notification error: {str(e)}", "error")

class BellSchedulerApp(Gtk.Application):
    def __init__(self, service_mode=False):
        super().__init__(
            application_id="com.example.BellScheduler",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.process = None
        self.service_mode = service_mode
        self.tray_icon = None
        self.logger = self.setup_logging()
        self.keep_running = True
        self.window = None
        self.check_interval = 10
        self.sound_player = SoundPlayer(self)
        self.last_played_time = None
        
        # Default configuration
        self.config = {
            "times": ["08:00", "10:00", "12:00", "14:00", "16:00"],
            "days": [1, 2, 3, 4, 5],  # 1=Monday, 2=Tuesday, etc.
            "message": "Bell time!",
            "sound": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
            "icon": "/usr/share/icons/gnome/256x256/status/appointment-soon.png",
            "active": False,
            "check_interval": 10,
            "custom_sounds": {}
        }
        
        self.load_config()
        
        if self.service_mode:
            GLib.idle_add(self.run_service)

    def setup_logging(self):
        """Configure logging system"""
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def log(self, message, level="info"):
        """Log events"""
        if level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def load_config(self):
        """Load configuration from file"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                self.config.update(saved_config)
                self.log("Configuration loaded successfully")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"Error loading configuration: {str(e)}", "error")

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.log("Configuration saved successfully")
        except Exception as e:
            self.log(f"Error saving configuration: {str(e)}", "error")

    def validate_time(self, time_str):
        """Validate time format HH:MM"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return 0 <= hours < 24 and 0 <= minutes < 60
        except ValueError:
            return False

    def validate_file_path(self, path):
        """Validate if file path is accessible"""
        try:
            return path and os.path.isfile(path) and os.access(path, os.R_OK)
        except (TypeError, ValueError):
            return False

    def do_command_line(self, command_line):
        """Handle command line arguments"""
        options = command_line.get_options_dict()
        if options.contains("service"):
            self.service_mode = True
        self.activate()
        return 0

    def do_activate(self):
        """Handle application activation"""
        if not self.service_mode:
            if self.window is None:
                self.create_main_window()
            else:
                self.window.present()

    def create_main_window(self):
        """Create and configure main window"""
        self.window = Gtk.ApplicationWindow(
            application=self,
            title="Bell Scheduler"
        )
        self.window.set_default_size(450, 400)
        self.window.set_border_width(4)

        # CSS configuration
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
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
            GtkListBox {
                background-color: transparent;
            }
            GtkListBoxRow {
                padding: 2px;
            }
            .sound-button {
                padding: 4px;
                margin: 0 2px;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.window.add(main_box)
            
        # System tray icon (only if not in service mode)
        if not self.service_mode:
            try:
                Notify.init("BellScheduler")
                self.tray_icon = Gtk.StatusIcon.new_from_file(self.config["icon"])
                self.tray_icon.set_tooltip_text("Bell Scheduler")
                self.tray_icon.connect("activate", self.on_icon_activate, self.window)
                self.tray_icon.connect("popup-menu", self.on_icon_click)
            except Exception as e:
                self.log(f"Error setting up tray icon: {str(e)}", "error")

        # Weekdays section
        days_frame = Gtk.Frame(label="Weekdays")
        days_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, margin=4, homogeneous=True)
        days_frame.add(days_box)

        self.day_buttons = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            btn = Gtk.ToggleButton(label=day)
            btn.set_active(i+1 in self.config["days"])
            btn.connect("toggled", self.on_day_toggle, i+1)
            btn.get_style_context().add_class("compact-button")
            days_box.pack_start(btn, True, True, 0)
            self.day_buttons.append(btn)

        main_box.pack_start(days_frame, False, False, 0)

        # Times section
        times_frame = Gtk.Frame(label="Times")
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
        add_button = Gtk.Button(label="Add")
        add_button.connect("clicked", self.on_add_time)
        add_box.pack_start(self.time_entry, True, True, 0)
        add_box.pack_start(add_button, False, False, 0)
        times_box.pack_start(add_box, False, False, 0)

        main_box.pack_start(times_frame, True, True, 0)

        # Settings
        settings_frame = Gtk.Frame(label="Settings")
        settings_grid = Gtk.Grid(column_spacing=6, row_spacing=6, margin=4)
        settings_frame.add(settings_grid)

        # Message
        settings_grid.attach(Gtk.Label(label="Message:"), 0, 0, 1, 1)
        self.message_entry = Gtk.Entry()
        self.message_entry.set_text(self.config["message"])
        settings_grid.attach(self.message_entry, 1, 0, 1, 1)

        # Sound
        settings_grid.attach(Gtk.Label(label="Default sound:"), 0, 1, 1, 1)
        sound_box = Gtk.Box(spacing=4)
        self.sound_entry = Gtk.Entry()
        self.sound_entry.set_text(self.config["sound"])
        
        sound_button = Gtk.Button.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        sound_button.set_tooltip_text("Browse sound file")
        sound_button.connect("clicked", self.on_browse_sound)
        
        self.test_button = Gtk.Button.new_from_icon_name("audio-volume-high-symbolic", Gtk.IconSize.BUTTON)
        self.test_button.set_tooltip_text("Test sound")
        self.test_button.connect("clicked", self.on_test_sound)
        self.test_button.get_style_context().add_class("sound-button")
        
        self.stop_button = Gtk.Button.new_from_icon_name("media-playback-stop-symbolic", Gtk.IconSize.BUTTON)
        self.stop_button.set_tooltip_text("Stop current sound")
        self.stop_button.connect("clicked", self.on_stop_sound)
        self.stop_button.get_style_context().add_class("sound-button")
        self.stop_button.set_sensitive(False)
        
        sound_box.pack_start(self.sound_entry, True, True, 0)
        sound_box.pack_start(sound_button, False, False, 0)
        sound_box.pack_start(self.test_button, False, False, 0)
        sound_box.pack_start(self.stop_button, False, False, 0)
        settings_grid.attach(sound_box, 1, 1, 1, 1)

        # Icon
        settings_grid.attach(Gtk.Label(label="Icon:"), 0, 2, 1, 1)
        icon_box = Gtk.Box(spacing=4)
        self.icon_entry = Gtk.Entry()
        self.icon_entry.set_text(self.config["icon"])
        icon_button = Gtk.Button.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        icon_button.set_tooltip_text("Browse icon file")
        icon_button.connect("clicked", self.on_browse_icon)
        preview_button = Gtk.Button.new_from_icon_name("image-x-generic-symbolic", Gtk.IconSize.BUTTON)
        preview_button.set_tooltip_text("Preview icon")
        preview_button.connect("clicked", self.on_preview_icon)
        icon_box.pack_start(self.icon_entry, True, True, 0)
        icon_box.pack_start(icon_button, False, False, 0)
        icon_box.pack_start(preview_button, False, False, 0)
        settings_grid.attach(icon_box, 1, 2, 1, 1)

        # Interval
        settings_grid.attach(Gtk.Label(label="Check interval (seconds):"), 0, 3, 1, 1)
        self.interval_spin = Gtk.SpinButton.new_with_range(5, 60, 1)
        self.interval_spin.set_value(self.config.get("check_interval", 10))
        settings_grid.attach(self.interval_spin, 1, 3, 1, 1)

        main_box.pack_start(settings_frame, False, False, 0)

        # Control buttons
        button_box = Gtk.Box(spacing=6, margin=2)
        self.start_button = Gtk.Button(label="Start")
        self.start_button.connect("clicked", self.on_start_stop)
        self.start_button.get_style_context().add_class("suggested-action")
        button_box.pack_start(self.start_button, True, True, 0)

        save_button = Gtk.Button(label="Save Configuration")
        save_button.connect("clicked", self.on_save_config)
        button_box.pack_start(save_button, True, True, 0)

        main_box.pack_start(button_box, False, False, 0)
        self.update_interface_state()

        self.window.connect("delete-event", self.on_window_close)
        self.window.show_all()

    def update_times_list(self):
        """Update times list in the interface"""
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

            edit_button = Gtk.Button.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.MENU)
            edit_button.connect("clicked", lambda b, t=time_str: self.on_edit_time(t))
            box.pack_start(edit_button, False, False, 0)

            remove_button = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.MENU)
            remove_button.connect("clicked", lambda b, t=time_str: self.on_remove_time(t))
            box.pack_start(remove_button, False, False, 0)

            self.times_list.add(row)
        
        self.times_list.show_all()

    def on_day_toggle(self, button, day):
        """Update active days when a button is toggled"""
        if button.get_active():
            if day not in self.config["days"]:
                self.config["days"].append(day)
        else:
            if day in self.config["days"]:
                self.config["days"].remove(day)
        self.config["days"].sort()

    def on_add_time(self, button):
        """Add a new time to the list"""
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

    def on_edit_time(self, old_time):
        """Show dialog for editing a time"""
        dialog = Gtk.Dialog(title="Edit Time", transient_for=self.window, flags=0)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)

        content = dialog.get_content_area()
        box = Gtk.Box(spacing=6)
        content.add(box)
        
        box.pack_start(Gtk.Label(label="New time:"), False, False, 0)
        entry = Gtk.Entry(text=old_time)
        box.pack_start(entry, True, True, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            new_time = entry.get_text().strip()
            if self.validate_time(new_time):
                if new_time != old_time and new_time in self.config["times"]:
                    self.show_error("Time exists", "This time is already in the list")
                else:
                    if old_time in self.config["custom_sounds"]:
                        self.config["custom_sounds"][new_time] = self.config["custom_sounds"].pop(old_time)
                    index = self.config["times"].index(old_time)
                    self.config["times"][index] = new_time
                    self.update_times_list()
            else:
                self.show_error("Invalid format", "Use HH:MM (24-hour format)")
        
        dialog.destroy()

    def on_remove_time(self, time_str):
        """Remove a time from the list"""
        if time_str in self.config["times"]:
            if time_str in self.config.get("custom_sounds", {}):
                del self.config["custom_sounds"][time_str]
            self.config["times"].remove(time_str)
            self.update_times_list()

    def play_sound(self, sound_file):
        """Play sound file"""
        return self.sound_player.play(sound_file)

    def on_test_sound(self, widget):
        """Test the selected sound"""
        sound_file = self.sound_entry.get_text()
        if not sound_file:
            self.show_error("No sound selected", "Select a sound file first")
            return
            
        if self.play_sound(sound_file):
            self.log(f"Testing sound: {sound_file}")

    def update_sound_controls(self):
        """Update sound control buttons state"""
        if hasattr(self, 'test_button') and hasattr(self, 'stop_button'):
            self.test_button.set_sensitive(not self.sound_player.is_playing)
            self.stop_button.set_sensitive(self.sound_player.is_playing)
        return False

    def on_stop_sound(self, widget):
        """Stop current sound playback"""
        self.sound_player.stop()

    def on_preview_icon(self, widget):
        """Show a preview of the selected icon"""
        icon_file = self.icon_entry.get_text()
        if self.validate_file_path(icon_file):
            dialog = Gtk.Dialog(title="Icon Preview", transient_for=self.window, flags=0)
            dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
            
            content = dialog.get_content_area()
            image = Gtk.Image.new_from_file(icon_file)
            image.set_pixel_size(128)
            content.add(image)
            
            dialog.show_all()
            dialog.run()
            dialog.destroy()
        else:
            self.show_error("Invalid file", "The icon file cannot be accessed")

    def on_browse_sound(self, widget):
        """Open dialog to select sound file"""
        dialog = Gtk.FileChooserDialog(
            title="Select a sound file",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)

        filter = Gtk.FileFilter()
        filter.set_name("Sound files")
        filter.add_mime_type("audio/*")
        dialog.add_filter(filter)

        if dialog.run() == Gtk.ResponseType.OK:
            file = dialog.get_filename()
            if self.validate_file_path(file):
                self.sound_entry.set_text(file)
        
        dialog.destroy()

    def on_browse_icon(self, widget):
        """Open dialog to select icon file"""
        dialog = Gtk.FileChooserDialog(
            title="Select an icon",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)

        filter = Gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/*")
        dialog.add_filter(filter)

        if dialog.run() == Gtk.ResponseType.OK:
            file = dialog.get_filename()
            if self.validate_file_path(file):
                self.icon_entry.set_text(file)
        
        dialog.destroy()

    def on_save_config(self, widget):
        """Save current settings"""
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
        self.show_info("Configuration saved", "Settings were saved successfully")
        
        if self.tray_icon:
            self.tray_icon.set_from_file(self.config["icon"])

    def on_start_stop(self, widget):
        """Start or stop the service"""
        if self.config["active"]:
            self.stop_service()
        else:
            self.start_service()

    def start_service(self):
        """Start background service"""
        if not self.service_mode:
            self.on_save_config(None)
            
            if not self.config["times"] or not self.config["days"]:
                self.show_error("Incomplete configuration", "Define days and times first")
                return

        self.config["active"] = True
        self.save_config()
        self.update_interface_state()
        self.show_info("Service started", "The scheduler is running")
        self.log("Service started")
        
        if self.service_mode:
            self.run_service()
        else:
            try:
                with open(SCRIPT_FILE, 'w') as f:
                    f.write(f"""#!/bin/bash
exec >> {SERVICE_LOG} 2>> {SERVICE_ERROR_LOG}
python3 {os.path.abspath(__file__)} --service
""")
                os.chmod(SCRIPT_FILE, 0o755)
                
                self.process = subprocess.Popen(
                    ["/bin/bash", SCRIPT_FILE],
                    stdout=open(SERVICE_LOG, 'a'),
                    stderr=open(SERVICE_ERROR_LOG, 'a'),
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                    preexec_fn=os.setsid
                )
                
                with open(PID_FILE, 'w') as f:
                    f.write(str(self.process.pid))
                
            except Exception as e:
                self.show_error("Error", f"Error starting service: {str(e)}")
                self.log(f"Error starting service: {str(e)}", "error")
                self.config["active"] = False
                self.save_config()

    def stop_service(self):
        """Stop running service"""
        self.keep_running = False
        self.on_stop_sound(None)
        
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), 15)
                self.process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired) as e:
                self.log(f"Error stopping service: {str(e)}", "error")
                try:
                    os.killpg(os.getpgid(self.process.pid), 9)
                except ProcessLookupError:
                    pass
            finally:
                self.process = None
        
        try:
            os.remove(PID_FILE)
        except FileNotFoundError:
            pass
        
        self.config["active"] = False
        self.save_config()
        self.update_interface_state()
        self.show_info("Service stopped", "The scheduler was stopped")
        self.log("Service stopped")

    def run_service(self):
        """Main service execution method"""
        self.log("Bell Scheduler Service started")
        
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus()
            Notify.init("BellScheduler")
        except Exception as e:
            self.log(f"Initialization error: {str(e)}", "error")
            return
        
        while self.keep_running:
            try:
                self.check_and_notify()
                time.sleep(self.config.get("check_interval", 10))
            except Exception as e:
                self.log(f"Service error: {str(e)}", "error")
                time.sleep(30)
        
        if Notify.is_initted():
            Notify.uninit()
        self.log("Bell Scheduler Service stopped")

    def check_and_notify(self):
        """Check times and trigger notifications when needed"""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.isoweekday()
        
        # Avoid multiple executions in the same minute
        if self.last_played_time == current_time:
            return
            
        if current_day in self.config["days"] and current_time in self.config["times"]:
            self.last_played_time = current_time
            self.log(f"Triggering bell for {current_time}")
            
            # Get specific sound file or default
            sound_file = self.config["custom_sounds"].get(
                current_time, 
                self.config["sound"]
            )
            
            # Verify file exists
            if not os.path.isfile(sound_file):
                self.log(f"Sound file not found: {sound_file}", "error")
                return
                
            # Visual notification
            try:
                notification = Notify.Notification.new(
                    self.config["message"],
                    f"Time: {current_time}",
                    self.config["icon"]
                )
                notification.set_urgency(2)
                notification.show()
            except Exception as e:
                self.log(f"Notification error: {str(e)}", "error")
            
            # Audio playback
            if self.play_sound(sound_file):
                GLib.idle_add(self.update_sound_controls)
            else:
                self.log(f"Failed to play sound: {sound_file}", "error")

    def update_interface_state(self):
        """Update button states in the interface"""
        if self.config["active"]:
            self.start_button.set_label("Stop")
            self.start_button.get_style_context().remove_class("suggested-action")
            self.start_button.get_style_context().add_class("destructive-action")
        else:
            self.start_button.set_label("Start")
            self.start_button.get_style_context().remove_class("destructive-action")
            self.start_button.get_style_context().add_class("suggested-action")

    def on_icon_activate(self, icon, window):
        """Show or hide main window when clicking icon"""
        if window.get_visible():
            window.hide()
        else:
            window.present()

    def on_icon_click(self, icon, button, time):
        """Show context menu when right-clicking icon"""
        menu = Gtk.Menu()
        
        show_item = Gtk.MenuItem(label="Show/Hide")
        show_item.connect("activate", self.on_icon_activate, self.window)
        menu.append(show_item)
        
        action_label = "Stop" if self.config["active"] else "Start"
        action_item = Gtk.MenuItem(label=action_label)
        action_item.connect("activate", self.on_start_stop, None)
        menu.append(action_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Item to stop current sound
        stop_sound_item = Gtk.MenuItem(label="Stop Current Sound")
        stop_sound_item.connect("activate", self.on_stop_sound)
        menu.append(stop_sound_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda x: self.quit())
        menu.append(quit_item)
        
        menu.show_all()
        menu.popup(None, None, None, None, button, time)

    def on_window_close(self, window, event):
        """Hide window instead of closing"""
        window.hide()
        return True

    def show_error(self, title, message):
        """Show error dialog"""
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
        self.log(f"Error: {title} - {message}", "error")

    def show_info(self, title, message):
        """Show info dialog"""
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
        self.log(f"Info: {title} - {message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bell Scheduler')
    parser.add_argument('--service', action='store_true', help='Run in service mode')
    parser.add_argument('--install-service', action='store_true', help='Install as systemd service')
    parser.add_argument('--check-interval', type=int, help='Check interval in seconds')
    args = parser.parse_args()

    if args.install_service:
        service_content = f"""[Unit]
Description=Bell Scheduler Service
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
        os.makedirs(service_dir, exist_ok=True)
        
        service_path = os.path.join(service_dir, "bell-scheduler.service")
        
        try:
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            print(f"Service installed at: {service_path}")
            print("To enable the service, run:")
            print("systemctl --user enable bell-scheduler.service")
            print("systemctl --user start bell-scheduler.service")
            print("\nTo check status:")
            print("systemctl --user status bell-scheduler.service")
        except Exception as e:
            print(f"Error installing service: {str(e)}")
            sys.exit(1)
    else:
        app = BellSchedulerApp(service_mode=args.service)
        if args.check_interval and args.service:
            app.check_interval = args.check_interval
        app.run(sys.argv)
