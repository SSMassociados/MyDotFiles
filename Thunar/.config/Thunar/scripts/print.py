#!/usr/bin/env python3
import sys
import subprocess
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

files = sys.argv[1:]
if not files:
    sys.exit(1)

# ── Impressoras ──────────────────────────────────────────────────────────────
try:
    raw = subprocess.check_output(["lpstat", "-a"], text=True)
    printers = [line.split()[0] for line in raw.splitlines() if line.strip()]
except subprocess.CalledProcessError:
    printers = []

if not printers:
    d = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR,
                          buttons=Gtk.ButtonsType.OK,
                          text="Nenhuma impressora encontrada.")
    d.run()
    sys.exit(1)

# ── Janela ───────────────────────────────────────────────────────────────────
win = Gtk.Dialog(title="Imprimir", modal=True)
win.set_default_size(340, 0)
win.add_buttons("Cancelar", Gtk.ResponseType.CANCEL,
                "Imprimir",  Gtk.ResponseType.OK)
win.set_default_response(Gtk.ResponseType.OK)

box = win.get_content_area()
box.set_spacing(6)
box.set_margin_top(14)
box.set_margin_bottom(10)
box.set_margin_start(14)
box.set_margin_end(14)

def label(text):
    l = Gtk.Label(label=text, xalign=0)
    l.get_style_context().add_class("dim-label")
    return l

def separator():
    sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    sep.set_margin_top(4)
    sep.set_margin_bottom(4)
    return sep

# ── Impressora ───────────────────────────────────────────────────────────────
box.add(label("Impressora"))
combo_printer = Gtk.ComboBoxText()
for p in printers:
    combo_printer.append_text(p)
combo_printer.set_active(0)
box.add(combo_printer)

box.add(separator())

# ── Cópias ───────────────────────────────────────────────────────────────────
box.add(label("Cópias"))
spin_copies = Gtk.SpinButton.new_with_range(1, 999, 1)
spin_copies.set_value(1)
spin_copies.set_activates_default(True)
box.add(spin_copies)

box.add(separator())

# ── Páginas ──────────────────────────────────────────────────────────────────
box.add(label("Páginas"))

radio_all   = Gtk.RadioButton.new_with_label(None, "Todas")
radio_range = Gtk.RadioButton.new_with_label_from_widget(radio_all, "Intervalo:")
hbox_pages  = Gtk.Box(spacing=6)
hbox_pages.pack_start(radio_all,   False, False, 0)
hbox_pages.pack_start(radio_range, False, False, 0)
box.add(hbox_pages)

hbox_range = Gtk.Box(spacing=6)
entry_pages = Gtk.Entry()
entry_pages.set_placeholder_text("ex: 1-3, 5, 7-9")
entry_pages.set_sensitive(False)
entry_pages.set_activates_default(True)
hbox_range.pack_start(Gtk.Label(label="   "), False, False, 0)
hbox_range.pack_start(entry_pages, True, True, 0)
box.add(hbox_range)

def on_range_toggled(btn):
    entry_pages.set_sensitive(btn.get_active())

radio_range.connect("toggled", on_range_toggled)

box.add(separator())

# ── Qualidade ────────────────────────────────────────────────────────────────
box.add(label("Qualidade"))
combo_quality = Gtk.ComboBoxText()
for q in ["Normal", "Rascunho", "Alto"]:
    combo_quality.append_text(q)
combo_quality.set_active(0)
box.add(combo_quality)

box.add(separator())

# ── Frente e verso ───────────────────────────────────────────────────────────
box.add(label("Frente e verso"))
combo_duplex = Gtk.ComboBoxText()
for d in ["Não", "Borda longa (retrato)", "Borda curta (paisagem)"]:
    combo_duplex.append_text(d)
combo_duplex.set_active(0)
box.add(combo_duplex)

box.add(separator())

# ── Cor ──────────────────────────────────────────────────────────────────────
box.add(label("Cor"))
combo_color = Gtk.ComboBoxText()
for c in ["Colorido", "Escala de cinza"]:
    combo_color.append_text(c)
combo_color.set_active(0)
box.add(combo_color)

# ── Exibe ────────────────────────────────────────────────────────────────────
win.show_all()
response = win.run()

if response != Gtk.ResponseType.OK:
    win.destroy()
    sys.exit(0)

# ── Coleta valores ───────────────────────────────────────────────────────────
printer   = combo_printer.get_active_text()
copies    = str(int(spin_copies.get_value()))
use_range = radio_range.get_active()
pages     = entry_pages.get_text().strip() if use_range else ""

quality_map = {"Normal": "normal", "Rascunho": "draft", "Alto": "high"}
quality = quality_map[combo_quality.get_active_text()]

duplex_map = {
    "Não":                    "one-sided",
    "Borda longa (retrato)":  "two-sided-long-edge",
    "Borda curta (paisagem)": "two-sided-short-edge",
}
duplex = duplex_map[combo_duplex.get_active_text()]

color_map = {"Colorido": "color", "Escala de cinza": "monochrome"}
color = color_map[combo_color.get_active_text()]

win.destroy()

# ── Valida intervalo ─────────────────────────────────────────────────────────
if use_range and not pages:
    d = Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR,
                          buttons=Gtk.ButtonsType.OK,
                          text="Informe o intervalo de páginas.")
    d.run()
    sys.exit(1)

# ── Monta comando lp ─────────────────────────────────────────────────────────
cmd = ["lp", "-d", printer, "-n", copies,
       "-o", f"print-quality={quality}",
       "-o", f"sides={duplex}",
       "-o", f"ColorModel={color}"]

if pages:
    cmd += ["-P", pages]

cmd += files

result = subprocess.run(cmd)

msg   = (f"Enviado para {printer} ({copies} cópia(s))."
         if result.returncode == 0
         else "Falha ao enviar para a impressora.")
mtype = Gtk.MessageType.INFO if result.returncode == 0 else Gtk.MessageType.ERROR
d = Gtk.MessageDialog(message_type=mtype, buttons=Gtk.ButtonsType.OK, text=msg)
d.run()
