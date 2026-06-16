#!/usr/bin/env python3
# ==================================================
# PYWAL DAEMON — Troca wallpaper em background
# Salve em: ~/.config/i3/scripts/pywal_daemon.py
# Gerenciado por: systemctl --user start pywal-wallpaper
# Não execute diretamente — use a GUI ou o systemctl
# systemctl --user status pywal-wallpaper
# journalctl --user -u pywal-wallpaper -f   # logs em tempo real
# cat ~/.config/systemd/user/pywal-wallpaper.service
# ==================================================

import json
import random
import shutil
import subprocess
import time
from pathlib import Path

WALLPAPER_DIR = Path.home() / ".wallpaper"
CACHE_DIR     = Path.home() / ".cache" / "wal"
I3_SCRIPTS    = Path.home() / ".config" / "i3" / "scripts"
POLYBAR_CONF  = Path.home() / ".config" / "polybar"
CONFIG_FILE   = CACHE_DIR / "pywal_gui.json"
EXTENSIONS    = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {"active": False, "interval_s": 300}


def find_wallpapers() -> list[Path]:
    if not WALLPAPER_DIR.exists():
        return []
    return [
        p for p in WALLPAPER_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    ]


def apply_wallpaper(wall: Path):
    wal_bin = shutil.which("wal")
    if not wal_bin:
        print(f"[pywal-daemon] pywal não encontrado", flush=True)
        return

    try:
        has_cols16 = "--cols16" in subprocess.run(
            [wal_bin, "--help"], capture_output=True, text=True
        ).stdout

        if has_cols16:
            subprocess.run(
                [wal_bin, "-i", str(wall), "--cols16", "--backend", "feh"],
                check=True, capture_output=True
            )
            subprocess.run(["feh", "--bg-fill", str(wall)], check=True)
        else:
            subprocess.run(
                [wal_bin, "-i", str(wall), "--iterative"],
                check=True, capture_output=True
            )

        # Xresources
        xres = CACHE_DIR / "colors.Xresources"
        if xres.exists():
            subprocess.run(["xrdb", "-merge", str(xres)], capture_output=True)

        # Scripts auxiliares
        for script in [
            I3_SCRIPTS / "pywal_dunst.sh",
            POLYBAR_CONF / "pywal_polybar.sh",
        ]:
            if script.exists():
                subprocess.Popen([str(script)])

        print(f"[pywal-daemon] Aplicado: {wall.name}", flush=True)

    except subprocess.CalledProcessError as e:
        print(f"[pywal-daemon] Erro ao aplicar {wall.name}: {e}", flush=True)


def main():
    print("[pywal-daemon] Iniciado", flush=True)

    while True:
        cfg = load_config()

        if not cfg.get("active", False):
            # Troca automática desativada — verifica a cada 10s por mudança
            print("[pywal-daemon] Inativo, aguardando ativação...", flush=True)
            time.sleep(10)
            continue

        interval_s = max(60, int(cfg.get("interval_s", 300)))
        walls = find_wallpapers()

        if not walls:
            print("[pywal-daemon] Nenhum wallpaper em ~/.wallpaper", flush=True)
            time.sleep(interval_s)
            continue

        wall = random.choice(walls)
        apply_wallpaper(wall)

        # Dorme pelo intervalo, relendo config a cada 15s para detectar mudanças
        slept = 0
        while slept < interval_s:
            time.sleep(min(15, interval_s - slept))
            slept += 15
            # Se config mudou (parou ou intervalo diferente), sai do sleep
            new_cfg = load_config()
            if not new_cfg.get("active", False):
                break
            if int(new_cfg.get("interval_s", interval_s)) != interval_s:
                break


if __name__ == "__main__":
    main()
