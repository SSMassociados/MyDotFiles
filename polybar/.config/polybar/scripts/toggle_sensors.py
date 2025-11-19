#!/usr/bin/env python3

import gi
import subprocess
import threading
import time
import re

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class SensorMonitor(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Monitor de Sensores")
        self.set_default_size(400, 300)
        self.set_border_width(10)
        
        # Variáveis de controle
        self.monitoring = False
        self.process = None
        
        # Layout principal
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        
        # Botão de toggle
        self.toggle_btn = Gtk.Button(label="Iniciar Monitoramento")
        self.toggle_btn.connect("clicked", self.on_toggle_clicked)
        vbox.pack_start(self.toggle_btn, False, False, 0)
        
        # Área de texto para exibir os dados
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_buffer = self.text_view.get_buffer()
        
        scrolled_window.add(self.text_view)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        # Thread para monitoramento
        self.monitor_thread = None
        
    def on_toggle_clicked(self, widget):
        if self.monitoring:
            self.stop_monitoring()
            widget.set_label("Iniciar Monitoramento")
        else:
            self.start_monitoring()
            widget.set_label("Parar Monitoramento")
    
    def start_monitoring(self):
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_sensors)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        if self.process:
            self.process.terminate()
    
    def monitor_sensors(self):
        while self.monitoring:
            try:
                # Executa o comando sensors
                result = subprocess.run(['sensors'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                
                if result.returncode == 0:
                    # Atualiza a interface na thread principal
                    GLib.idle_add(self.update_display, result.stdout)
                
            except subprocess.TimeoutExpired:
                GLib.idle_add(self.update_display, "Timeout ao ler sensores\n")
            except Exception as e:
                GLib.idle_add(self.update_display, f"Erro: {str(e)}\n")
            
            time.sleep(2)  # Atualiza a cada 2 segundos
    
    def update_display(self, text):
        self.text_buffer.set_text(text)
    
    def on_destroy(self, widget):
        self.stop_monitoring()
        Gtk.main_quit()

# Versão melhorada com parsing dos dados
class AdvancedSensorMonitor(SensorMonitor):
    def __init__(self):
        super().__init__()
        self.set_title("Monitor Avançado de Sensores")
        
        # Adicionar barra de progresso para temperaturas
        self.temp_bars = {}
        self.create_temp_bars()
    
    def create_temp_bars(self):
        # Esta função criaria barras de progresso para cada sensor
        # Implementação mais complexa para UI avançada
        pass
    
    def parse_sensor_data(self, text):
        # Parse mais sofisticado dos dados dos sensores
        sensors_data = {}
        current_sensor = None
        
        for line in text.split('\n'):
            if line.strip() and not line.startswith(' '):
                current_sensor = line.strip().replace(':', '')
                sensors_data[current_sensor] = {}
            elif line.strip() and current_sensor:
                # Parse de linhas como: "temp1:        +45.0°C  (high = +80.0°C, crit = +95.0°C)"
                match = re.search(r'(\w+):\s+\+([\d.]+)°C', line)
                if match:
                    sensor_name = match.group(1)
                    temperature = float(match.group(2))
                    sensors_data[current_sensor][sensor_name] = temperature
        
        return sensors_data

if __name__ == "__main__":
    win = SensorMonitor()
    win.connect("destroy", win.on_destroy)
    win.show_all()
    Gtk.main()
