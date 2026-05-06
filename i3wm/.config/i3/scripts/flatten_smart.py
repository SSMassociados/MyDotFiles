#!/usr/bin/env python3
"""
i3wm Flatten Smart - Remove TODOS os containers e splits, forçando o i3 a reaplicar as regras do for_window.
Versão com proteção para janelas flutuantes + layout horizontal 

Uso:
    ./flatten_smart.py                     # Limpeza padrão (com layout horizontal)
    ./flatten_smart.py --no-horizontal     # Limpeza sem forçar horizontal
    ./flatten_smart.py --debug             # Modo debug
    ./flatten_smart.py --force             # Execução forçada sem confirmação
"""

import subprocess
import json
import sys
import time

class I3FlattenSmart:
    def __init__(self):
        self.normal_windows = []
        self.floating_windows = []
        self.all_containers = []
        
    def get_complete_tree(self):
        """Obtém a árvore completa do i3"""
        try:
            result = subprocess.run(
                ['i3-msg', '-t', 'get_tree'],
                capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            print(f"❌ Erro ao obter árvore: {e}")
            return None
    
    def is_window_floating(self, node):
        """Verifica se uma janela está flutuando"""
        return node.get('floating', 'auto_off') != 'auto_off' or node.get('type') == 'floating_con'
    
    def extract_all_windows_and_containers(self, node):
        """Extrai janelas e containers recursivamente"""
        if 'window' in node and node['window'] is not None:
            window_info = {
                'id': node['window'],
                'con_id': node['id'],
                'name': node.get('name', 'Sem nome')
            }
            if self.is_window_floating(node):
                self.floating_windows.append(window_info)
            else:
                self.normal_windows.append(window_info)
        
        if node.get('type') == 'con' and 'window' not in node:
            self.all_containers.append({'id': node['id']})
        
        for child in node.get('nodes', []):
            self.extract_all_windows_and_containers(child)
        for child in node.get('floating_nodes', []):
            self.extract_all_windows_and_containers(child)
    
    def get_current_workspace_name(self):
        """Pega o nome do workspace focado"""
        try:
            result = subprocess.run(
                ['i3-msg', '-t', 'get_workspaces'],
                capture_output=True, text=True, check=True
            )
            workspaces = json.loads(result.stdout)
            return next((ws['name'] for ws in workspaces if ws.get('focused')), None)
        except:
            return None
    
    def analyze_current_workspace(self):
        """Filtra a árvore para o workspace atual"""
        tree = self.get_complete_tree()
        ws_name = self.get_current_workspace_name()
        if not tree or not ws_name: return

        def find_workspace(node):
            if node.get('type') == 'workspace' and node.get('name') == ws_name:
                return node
            for child in node.get('nodes', []):
                res = find_workspace(child)
                if res: return res
            return None
        
        workspace = find_workspace(tree)
        if workspace:
            self.extract_all_windows_and_containers(workspace)
    
    def move_normal_windows_to_root(self):
        """Move janelas para fora de containers"""
        for window in self.normal_windows:
            wid = window['id']
            # Focar e desabilitar floating (garantia)
            subprocess.run(['i3-msg', f'[id="{wid}"]', 'focus; floating disable'], capture_output=True)
            time.sleep(0.02)
            # Tentar mover para todas as direções para "escapar" de aninhamentos
            for direction in ['left', 'right', 'up', 'down']:
                subprocess.run(['i3-msg', 'move', direction], capture_output=True)
                time.sleep(0.01)
    
    def kill_all_containers(self):
        """Remove containers vazios residuais"""
        killed = 0
        for container in self.all_containers:
            res = subprocess.run(['i3-msg', f'[con_id="{container["id"]}"]', 'kill'], capture_output=True)
            if res.returncode == 0: killed += 1
        return killed

    def restore_title_format(self):
        """
        O TRUQUE: Reseta o title_format para vazio.
        Isso força o i3 a invalidar o estado manual e reaplicar as regras
        definidas no seu config (como o seu for_window de pinguins).
        """
        print("🎨 Sincronizando decorações com o config do i3...")
        for window in self.normal_windows:
            wid = window['id']
            subprocess.run(['i3-msg', f'[id="{wid}"]', 'title_format', ''], capture_output=True)
            time.sleep(0.01)
        
        # Opcional: Garante que o i3 processe as mudanças
        subprocess.run(['i3-msg', 'reload'], capture_output=True)

    def run(self, no_horizontal=False):
        print("🧹 Iniciando limpeza e sincronização...")
        self.analyze_current_workspace()
        
        if not self.normal_windows:
            print("⚠️ Nenhuma janela normal encontrada.")
            return

        self.move_normal_windows_to_root()
        time.sleep(0.2)
        
        killed = self.kill_all_containers()
        
        if not no_horizontal:
            subprocess.run(['i3-msg', 'layout splith'], capture_output=True)
        
        # Reaplicar regras do config
        self.restore_title_format()
        
        print(f"\n✅ Concluído: {len(self.normal_windows)} janelas reorganizadas e {killed} containers limpos.")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', '-f', action='store_true')
    parser.add_argument('--no-horizontal', action='store_true')
    args = parser.parse_args()

    cleaner = I3FlattenSmart()
    
    if not args.force:
        confirm = input("Deseja achatar o workspace e reaplicar as regras do config? (s/N): ")
        if confirm.lower() != 's': sys.exit(0)
    
    cleaner.run(no_horizontal=args.no_horizontal)

if __name__ == "__main__":
    main()
