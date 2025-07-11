#!/usr/bin/env python3
# Sistema de Informações e Gerenciamento Escolar (SIGE) - Versão Completa

import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkf
import sys
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import platform
from reportlab.lib.units import inch
import os
import subprocess
import threading
import webbrowser
import logging
from typing import List, Tuple, Optional, Dict, Any

# Configuração de logging
logging.basicConfig(
    filename='sige.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configurações de caminhos
DOCUMENTS_PATH = os.path.expanduser("~/Documents/AUSTRO/DECLARAÇÕES")
DEFAULT_PDF_VIEWER = {
    'Linux': 'atril',
    'Windows': 'explorer',
    'Darwin': 'open'
}

class SIGEApplication:
    def __init__(self, root: tk.Tk, csv_file: str = ""):
        self.root = root
        self.csv_file = csv_file
        self.last_save_location = ""
        self.classes = self.load_classes() if csv_file else []
        
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        """Configura a interface gráfica principal"""
        self.root.title("Sistema de Informações e Gerenciamento Escolar")
        self.root.configure(bg='#3B3B3B')
        
        # Estilos
        self.style = ttk.Style(self.root)
        self.style.configure('Treeview.Heading', font=('JetBrains Mono', 12))
        self.style.configure('TButton', font=('JetBrains Mono', 12))
        self.style.configure('TLabel', font=('JetBrains Mono', 12))
        self.style.configure('TEntry', font=('JetBrains Mono', 12))
        self.style.configure('Treeview', font=('JetBrains Mono', 11), rowheight=25)
        self.style.configure('Custom.Treeview', background='#3B3B3B', foreground='#ffffff')
        
        # Cabeçalho
        sige_label = ttk.Label(
            self.root, 
            text="SISTEMA DE INFORMAÇÕES E GERENCIAMENTO ESCOLAR", 
            font=('JetBrains Mono', 12), 
            background='#333333', 
            foreground='#ffffff'
        )
        sige_label.pack(side=tk.TOP, pady=10)
        
        # Frame principal
        self.main_frame = tk.Frame(self.root, bg='#3B3B3B')
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Frame de pesquisa
        self.setup_search_frame()
        
        # Frame de resultados
        self.setup_results_frame()
        
        # Botões de exportação
        self.setup_export_buttons()
        
        # Botão About
        about_button = tk.Button(
            self.root, text="About", font=('JetBrains Mono', 10), 
            command=self.open_about_window, bg='#333333', fg='#ffffff'
        )
        about_button.pack(side=tk.RIGHT, anchor=tk.SE, padx=10, pady=10)
        
        # Focar no campo de entrada
        self.entry_student.focus_set()
    
    def setup_search_frame(self):
        """Configura o frame de pesquisa"""
        search_frame = tk.Frame(self.main_frame, bg='#3B3B3B')
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Campo de pesquisa por aluno
        student_label = tk.Label(
            search_frame, text="Aluno:", 
            font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff'
        )
        student_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        self.entry_student = tk.Entry(
            search_frame, font=('JetBrains Mono', 12), 
            bg='#2d2d32', fg='#ffffff'
        )
        self.entry_student.pack(side=tk.LEFT, padx=(0, 5), pady=5, fill=tk.X, expand=True)
        
        self.search_button = tk.Button(
            search_frame, text="Pesquisar", font=('JetBrains Mono', 12), 
            command=self.show_search_result, bg='#007acc', fg='#ffffff'
        )
        self.search_button.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        
        # Combobox de turmas
        class_label = tk.Label(
            search_frame, text="Turma:", 
            font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff'
        )
        class_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        self.class_combobox = ttk.Combobox(
            search_frame, values=list(self.classes), 
            font=('JetBrains Mono', 12), state="readonly"
        )
        self.class_combobox.pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.class_combobox.bind("<<ComboboxSelected>>", self.select_class)
    
    def setup_results_frame(self):
        """Configura o frame de resultados"""
        result_frame = tk.Frame(self.main_frame, bg='#3B3B3B')
        result_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        result_label = tk.Label(
            result_frame, text="Resultados:", 
            font=('JetBrains Mono', 12), bg='#3B3B3B', fg='#ffffff'
        )
        result_label.pack(pady=5)
        
        # Treeview de resultados
        self.result_tree = ttk.Treeview(
            result_frame, 
            columns=("Matrícula", "Nome", "Nascimento", "Idade", "Turma", "Turno"), 
            show="headings", 
            style="Custom.Treeview"
        )
        for col in ("Matrícula", "Nome", "Nascimento", "Idade", "Turma", "Turno"):
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, stretch=True)
        
        # Configurar tags para linhas zebra
        self.result_tree.tag_configure('even', background='#2d2d32', foreground='#ffffff')
        self.result_tree.tag_configure('odd', background='#3B3B3B', foreground='#ffffff')
        self.result_tree.pack(expand=True, fill="both")
        
        # Rótulo de ocorrências
        self.occurrences_label = tk.Label(
            self.main_frame, font=('JetBrains Mono', 12), 
            bg='#3B3B3B', fg='#ffffff'
        )
        self.occurrences_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))
    
    def setup_export_buttons(self):
        """Configura os botões de exportação"""
        export_buttons_frame = tk.Frame(self.root, bg='#3B3B3B')
        export_buttons_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))
        
        buttons = [
            ("Resultados", self.export_results_to_pdf),
            ("Ata", self.export_ata_to_pdf),
            ("Bolsa", self.open_declaration),
            ("Presença", self.open_presence),
            ("Provisória", self.open_provisoria),
            ("SIEPE", self.open_siepe),
            ("Censo Escolar", self.open_censo),
            ("Alunos das Turmas", self.show_class_statistics)
        ]
        
        for text, command in buttons:
            tk.Button(
                export_buttons_frame, text=text, font=('JetBrains Mono', 12), 
                command=command, bg='#007acc', fg='#ffffff', width=11
            ).pack(side=tk.LEFT, padx=5, pady=5)
    
    def setup_bindings(self):
        """Configura os atalhos de teclado"""
        self.root.bind("<Return>", self.show_search_result)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Control-q>", lambda e: self.root.destroy())
        self.root.bind("<F1>", lambda e: self.open_about_window())
        self.root.bind("<Tab>", self.handle_tab_navigation)
        self.root.bind("<Shift-Tab>", self.handle_shift_tab_navigation)
    
    def handle_tab_navigation(self, event):
        """Manipula navegação com Tab"""
        if self.root.focus_get() == self.entry_student:
            self.class_combobox.focus_set()
        elif self.root.focus_get() == self.class_combobox:
            self.search_button.focus_set()
    
    def handle_shift_tab_navigation(self, event):
        """Manipula navegação com Shift+Tab"""
        if self.root.focus_get() == self.search_button:
            self.class_combobox.focus_set()
        elif self.root.focus_get() == self.class_combobox:
            self.entry_student.focus_set()
    
    def load_classes(self) -> set:
        """Carrega as turmas do arquivo CSV"""
        if not os.path.exists(self.csv_file):
            logging.error(f"Arquivo CSV não encontrado: {self.csv_file}")
            return set()
        
        try:
            with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Pular cabeçalho
                return {row[8] for row in reader if len(row) > 8}  # Turma está na coluna 9
        except Exception as e:
            logging.error(f"Erro ao ler arquivo CSV: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao ler arquivo CSV: {str(e)}")
            return set()
    
    def calculate_age(self, birth_date: str) -> str:
        """Calcula idade a partir da data de nascimento"""
        try:
            today = datetime.now()
            birth_date = pd.to_datetime(birth_date, dayfirst=True)
            age = relativedelta(today, birth_date)
            return f"{age.years} Anos, {age.months} Meses e {age.days} Dias"
        except Exception as e:
            logging.error(f"Erro ao calcular idade: {str(e)}")
            return "Data inválida"
    
    def adjust_column_widths(self, tree: ttk.Treeview):
        """Ajusta automaticamente as larguras das colunas"""
        tree.update_idletasks()
        column_widths = {}
        
        for col in tree["columns"]:
            column_widths[col] = tkf.Font().measure(col)
        
        for child in tree.get_children():
            for idx, value in enumerate(tree.item(child)["values"]):
                col = tree["columns"][idx]
                cell_width = tkf.Font().measure(str(value))
                if cell_width > column_widths[col]:
                    column_widths[col] = cell_width
        
        for col, width in column_widths.items():
            tree.column(col, width=width + 10)  # Adiciona pequena margem
    
    def search_student(self, student_name: str) -> List[Tuple[str, ...]]:
        """Pesquisa alunos pelo nome"""
        if not self.csv_file:
            self.show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")
            return []
        
        try:
            with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                found_students = []
                
                for row in reader:
                    if len(row) < 2:  # Verifica se há pelo menos 2 colunas
                        continue
                    
                    full_name = row[1]  # Nome completo está na coluna 2
                    if student_name.lower() in full_name.lower():
                        found_students.append(tuple(row))
                
                return sorted(found_students, key=lambda x: x[1].lower())
        except Exception as e:
            logging.error(f"Erro ao pesquisar aluno: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao pesquisar aluno: {str(e)}")
            return []
    
    def search_class(self, class_name: str) -> List[Tuple[str, ...]]:
        """Pesquisa alunos por turma"""
        if not self.csv_file:
            self.show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")
            return []
        
        try:
            with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Pula cabeçalho
                
                return [tuple(row) for row in reader 
                       if len(row) > 8 and class_name.lower() == row[8].lower()]  # Turma está na coluna 9
        except Exception as e:
            logging.error(f"Erro ao pesquisar turma: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao pesquisar turma: {str(e)}")
            return []
    
    def show_search_result(self, event=None):
        """Mostra resultados da pesquisa por aluno"""
        student_name = self.entry_student.get().strip()
        
        if not student_name:
            self.show_custom_message("Erro", "Por favor, insira o nome do aluno.")
            return
        
        # Limpa resultados anteriores
        self.result_tree.delete(*self.result_tree.get_children())
        self.class_combobox.set("")
        
        found_students = self.search_student(student_name)
        
        if found_students:
            for i, student in enumerate(found_students):
                age = self.calculate_age(student[2])  # Data de nascimento na coluna 3
                self.result_tree.insert(
                    "", "end", 
                    values=(
                        student[0],  # Matrícula
                        student[1],  # Nome
                        student[2],  # Nascimento
                        age,
                        student[8],  # Turma
                        student[9]   # Turno
                    ), 
                    tags=('even' if i % 2 == 0 else 'odd')
                )
            
            self.occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
            self.adjust_column_widths(self.result_tree)
        else:
            self.occurrences_label.config(text="Ocorrências encontradas: 0")
            self.show_custom_message("Resultado", "Aluno não encontrado.")
        
        self.entry_student.select_range(0, tk.END)
    
    def select_class(self, event=None):
        """Seleciona alunos por turma"""
        selected_class = self.class_combobox.get()
        
        if not selected_class:
            return
        
        # Limpa resultados anteriores
        self.result_tree.delete(*self.result_tree.get_children())
        self.entry_student.delete(0, tk.END)
        
        found_students = self.search_class(selected_class)
        
        if found_students:
            for i, student in enumerate(found_students):
                age = self.calculate_age(student[2])  # Data de nascimento na coluna 3
                self.result_tree.insert(
                    "", "end", 
                    values=(
                        student[0],  # Matrícula
                        student[1],  # Nome
                        student[2],  # Nascimento
                        age,
                        student[8],  # Turma
                        student[9]   # Turno
                    ), 
                    tags=('even' if i % 2 == 0 else 'odd')
                )
            
            self.occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
            self.adjust_column_widths(self.result_tree)
        else:
            self.occurrences_label.config(text="Ocorrências encontradas: 0")
            self.show_custom_message("Resultado", "Nenhum aluno encontrado para esta turma.")
    
    def calculate_class_statistics(self) -> List[Dict[str, Any]]:
        """Calcula estatísticas de alunos por turma e série"""
        if not self.csv_file:
            self.show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")
            return []

        try:
            with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Pular cabeçalho
                
                stats = {}
                
                for row in reader:
                    if len(row) < 10:  # Verificar se tem colunas necessárias
                        continue
                    
                    turma = row[8]  # Turma está na coluna 9
                    
                    # Extrair informações da turma
                    serie_completa = row[7] if len(row) > 7 else ''  # Série/Fase/Módulo na coluna 8
                    
                    # Determinar tipo de classificação (Ano ou Módulo)
                    if '1º Ano' in serie_completa:
                        serie = '1º Ano'
                        ordem = 1
                    elif '2º Ano' in serie_completa:
                        serie = '2º Ano'
                        ordem = 2
                    elif '3º Ano' in serie_completa:
                        serie = '3º Ano'
                        ordem = 3
                    elif 'Módulo 1' in serie_completa:
                        serie = 'Módulo 1'
                        ordem = 4
                    elif 'Módulo 2' in serie_completa:
                        serie = 'Módulo 2'
                        ordem = 5
                    elif 'Módulo 3' in serie_completa:
                        serie = 'Módulo 3'
                        ordem = 6
                    else:
                        serie = serie_completa.split('-')[0].strip()
                        ordem = 7  # Outros ficam no final
                    
                    turno = row[9] if len(row) > 9 else ''  # Turno na coluna 10
                    
                    if turma not in stats:
                        stats[turma] = {
                            'Série': serie,
                            'Ordem': ordem,
                            'Turno': turno,
                            'Turma': turma,
                            'Total/Turma': 0,
                            'Total/Série': 0
                        }
                    
                    stats[turma]['Total/Turma'] += 1
                
                # Calcular totais por série
                series_totals = {}
                for turma_data in stats.values():
                    serie = turma_data['Série']
                    if serie not in series_totals:
                        series_totals[serie] = 0
                    series_totals[serie] += turma_data['Total/Turma']
                
                # Adicionar totais por série
                for turma_data in stats.values():
                    serie = turma_data['Série']
                    turma_data['Total/Série'] = series_totals.get(serie, 0)
                
                # Ordenar por ordem (1º, 2º, 3º, Módulos) e depois por turma
                return sorted(stats.values(), key=lambda x: (x['Ordem'], x['Turma']))
                
        except Exception as e:
            logging.error(f"Erro ao calcular estatísticas: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao calcular estatísticas: {str(e)}")
            return []

    def show_class_statistics(self):
        """Mostra estatísticas de alunos por turma em uma nova janela"""
        stats = self.calculate_class_statistics()
        
        if not stats:
            return
        
        # Criar nova janela
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Alunos por Turma")
        stats_window.configure(bg='#3B3B3B')
        
        # Frame principal
        main_frame = tk.Frame(stats_window, bg='#3B3B3B')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview para mostrar os dados
        tree = ttk.Treeview(
            main_frame,
            columns=("Série", "Turno", "Turma", "Total/Turma", "Total/Série"),
            show="headings",
            style="Custom.Treeview"
        )
        
        # Configurar colunas
        columns = ["Série", "Turno", "Turma", "Total/Turma", "Total/Série"]
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        
        # Adicionar dados organizados
        current_serie = None
        for i, data in enumerate(stats):
            # Mostrar total por série apenas na primeira turma de cada série
            show_serie_total = (current_serie != data['Série'])
            current_serie = data['Série']
            
            values = [
                data['Série'],
                data['Turno'],
                data['Turma'],
                data['Total/Turma'],
                data['Total/Série'] if show_serie_total else ""
            ]
            tree.insert("", "end", values=values, tags=('even' if i % 2 == 0 else 'odd'))
        
        # Barra de rolagem
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Ajustar tamanho da janela ao conteúdo
        tree.update_idletasks()
        width = sum(tree.column(col)['width'] for col in tree["columns"]) + 50
        height = min(600, tree.winfo_reqheight() + 100)
        stats_window.geometry(f"{width}x{height}")
        
        # Centralizar janela
        self.center_window(stats_window)
        
        # Configurar tags para linhas zebradas
        tree.tag_configure('even', background='#2d2d32', foreground='#ffffff')
        tree.tag_configure('odd', background='#3B3B3B', foreground='#ffffff')
        
        # Botão de exportar
        export_button = tk.Button(
            stats_window, text="Exportar para PDF", font=('JetBrains Mono', 12),
            command=lambda: self.export_stats_to_pdf(stats),
            bg='#007acc', fg='#ffffff'
        )
        export_button.pack(pady=10)
    
    def export_stats_to_pdf(self, stats: List[Dict[str, Any]]):
        """Exporta estatísticas por turma para PDF"""
        if not stats:
            self.show_custom_message("Erro", "Nenhum dado para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile="Alunos_por_Turma",
            initialdir=self.last_save_location
        )
        
        if not filename:
            return
        
        self.last_save_location = os.path.dirname(filename)
        
        # Preparar dados para a tabela
        data = []
        columns = ["Série", "Turno", "Turma", "Total/Turma", "Total/Série"]
        
        # Cabeçalho
        data.append(columns)
        
        # Dados
        for stat in stats:
            data.append([
                stat['Série'],
                stat['Turno'],
                stat['Turma'],
                stat['Total/Turma'],
                stat['Total/Série'] if stat == stats[0] or stat['Série'] != stats[stats.index(stat)-1]['Série'] else ""
            ])
        
        # Criar documento PDF
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        elements = []
        
        # Título
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontSize=14,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("<b>ALUNOS POR TURMA</b>", title_style))
        elements.append(Spacer(1, 20))
        
        # Data
        date_style = ParagraphStyle(
            name='DateStyle',
            fontSize=12,
            alignment=TA_CENTER
        )
        current_date = datetime.now().strftime("%d/%m/%Y")
        elements.append(Paragraph(f"Data: {current_date}", date_style))
        elements.append(Spacer(1, 20))
        
        # Tabela
        table = Table(data)
        
        # Estilos
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        # Zebrar linhas
        row_count = len(data)
        for i in range(1, row_count):
            if i % 2 == 0:
                bg_color = colors.beige
            else:
                bg_color = colors.whitesmoke
            style.add('BACKGROUND', (0, i), (-1, i), bg_color)
        
        table.setStyle(style)
        elements.append(table)
        
        try:
            doc.build(elements)
            self.show_export_success_window(filename)
        except Exception as e:
            logging.error(f"Erro ao exportar estatísticas: {str(e)}")
            self.show_custom_message("Erro", f"Falha ao exportar estatísticas: {str(e)}")
    
    def create_pdf_table(self, data: List[List[str]], title: str = "", date: str = "") -> SimpleDocTemplate:
        """Cria uma tabela PDF com os dados fornecidos"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialdir=self.last_save_location
        )
        
        if not filename:
            return None
        
        self.last_save_location = os.path.dirname(filename)
        filename = filename.replace(" ", "_").replace("-", "_")
        
        doc = SimpleDocTemplate(
            filename, 
            pagesize=A4, 
            leftMargin=50, 
            rightMargin=50, 
            topMargin=50, 
            bottomMargin=50
        )
        elements = []
        
        if title:
            title_style = ParagraphStyle(
                name='TitleStyle', 
                fontSize=14, 
                alignment=TA_CENTER
            )
            elements.append(Paragraph(f"<b>{title}</b>", title_style))
        
        if date:
            date_style = ParagraphStyle(
                name='DateStyle', 
                fontSize=12, 
                alignment=TA_CENTER
            )
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(date, date_style))
            elements.append(Spacer(1, 10))
        
        # Estilo do cabeçalho
        header_style = TableStyle([
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12)
        ])
        
        # Estilo dos dados
        data_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        # Listras zebradas
        for i in range(0, len(data), 2):
            data_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.beige)
        
        table = Table(data)
        table.setStyle(header_style)
        table.setStyle(data_style)
        elements.append(table)
        
        try:
            doc.build(elements)
            return filename
        except Exception as e:
            logging.error(f"Erro ao gerar PDF: {str(e)}")
            self.show_custom_message("Erro", f"Falha ao gerar PDF: {str(e)}")
            return None
    
    def export_to_pdf(self, data: List[List[str]], title: str = "", date: str = ""):
        """Exporta dados para PDF"""
        filename = self.create_pdf_table(data, title, date)
        
        if filename:
            self.show_export_success_window(filename)
    
    def export_ata_to_pdf(self):
        """Exporta ata de assinaturas para PDF"""
        turma = self.class_combobox.get()
        initialfile = f"ATA_{turma.replace(' ', '_')}" if turma else "ATA"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("Arquivo PDF", "*.pdf")], 
            initialfile=initialfile,
            initialdir=self.last_save_location
        )
        
        if not filename:
            return
        
        self.last_save_location = os.path.dirname(filename)
        filename = filename.replace(" ", "_").replace("-", "_")
        
        # Preparar dados da ata
        data = []
        for i, row_id in enumerate(self.result_tree.get_children(), start=1):
            row = self.result_tree.item(row_id)['values']
            data.append([i, row[0], row[1], " " * 80 + "."])  # Espaço para assinatura
        
        if not data:
            self.show_custom_message("Erro", "Nenhum dado para exportar")
            return
        
        # Configurar documento
        doc = SimpleDocTemplate(
            filename, 
            pagesize=letter, 
            leftMargin=20, 
            rightMargin=20,
            topMargin=20, 
            bottomMargin=20
        )
        elements = []
        
        # Título
        ata_title = "ATA DE ASSINATURAS"
        if turma:
            ata_title += f" - \"{turma}\""
        
        title_style = ParagraphStyle(
            name='TitleStyle', 
            fontSize=14, 
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"<b>{ata_title}</b>", title_style))
        
        # Data
        current_date = datetime.now().strftime("%d/%m/%Y - %A - %H:%M:%S")
        date_style = ParagraphStyle(
            name='DateStyle', 
            fontSize=12, 
            alignment=TA_CENTER
        )
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(current_date, date_style))
        elements.append(Spacer(1, 10))
        
        # Cabeçalho
        header = ["#", "Matrícula", "Nome", "Assinatura"]
        data.insert(0, header)
        
        # Estilos
        header_style = TableStyle([
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
            ('TOPPADDING', (0, 0), (-1, 0), 3)
        ])
        
        data_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        # Listras zebradas
        for i in range(0, len(data), 2):
            data_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.beige)
        
        # Criar tabela
        table = Table(data)
        table.setStyle(header_style)
        table.setStyle(data_style)
        elements.append(table)
        
        try:
            doc.build(elements)
            self.show_export_success_window(filename)
        except Exception as e:
            logging.error(f"Erro ao gerar ata: {str(e)}")
            self.show_custom_message("Erro", f"Falha ao gerar ata: {str(e)}")
    
    def export_results_to_pdf(self):
        """Exporta resultados da pesquisa para PDF"""
        data = []
        for row_id in self.result_tree.get_children():
            row = self.result_tree.item(row_id)['values']
            data.append(row)
        
        if not data:
            self.show_custom_message("Erro", "Nenhum resultado para exportar")
            return
        
        header = ["Matrícula", "Nome", "Nascimento", "Idade", "Turma", "Turno"]
        data.insert(0, header)
        
        self.export_to_pdf(data)
    
    def show_export_success_window(self, filename: str):
        """Mostra janela de sucesso na exportação"""
        export_success_window = tk.Toplevel(self.root)
        export_success_window.title("Exportação Concluída")
        export_success_window.configure(bg='#3B3B3B')
        export_success_window.transient(self.root)
        
        def close_about_window(event=None):
            export_success_window.destroy()
        
        export_success_window.bind("<Escape>", close_about_window)
        
        # Mensagem
        success_label = tk.Label(
            export_success_window, 
            text=f"Arquivo exportado com sucesso para:\n{filename}", 
            font=('JetBrains Mono', 12), 
            bg='#3B3B3B', 
            fg='#ffffff'
        )
        success_label.pack(pady=10)
        
        # Frame para botões
        button_frame = tk.Frame(export_success_window, bg='#3B3B3B')
        button_frame.pack(pady=10)
        
        # Botões
        buttons = [
            ("Visualizar", self.visualize_pdf, filename),
            ("Abrir Local", self.open_directory, os.path.dirname(filename)),
            ("Sair", export_success_window.destroy, None)
        ]
        
        for text, command, arg in buttons:
            btn = tk.Button(
                button_frame, text=text, font=('JetBrains Mono', 12), 
                command=lambda c=command, a=arg: c(a) if a is not None else c(),
                bg='#007acc', fg='#ffffff'
            )
            btn.pack(side=tk.LEFT, padx=5)
    
    def visualize_pdf(self, filename: str):
        """Abre o PDF no visualizador padrão"""
        try:
            viewer = DEFAULT_PDF_VIEWER.get(platform.system(), 'xdg-open')
            subprocess.Popen([viewer, filename])
        except Exception as e:
            logging.error(f"Erro ao visualizar PDF: {str(e)}")
            self.show_custom_message("Erro", "Visualizador de PDF não encontrado")
    
    def open_directory(self, directory: str):
        """Abre o diretório no gerenciador de arquivos"""
        try:
            if platform.system() == 'Windows':
                os.startfile(directory)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', directory])
            else:
                subprocess.Popen(['xdg-open', directory])
        except Exception as e:
            logging.error(f"Erro ao abrir diretório: {str(e)}")
            self.show_custom_message("Erro", "Não foi possível abrir o diretório")
    
    def open_document(self, doc_name: str, doc_path: str):
        """Abre um documento no visualizador padrão"""
        full_path = os.path.join(DOCUMENTS_PATH, doc_path)
        
        if not os.path.exists(full_path):
            self.show_custom_message("Erro", f"{doc_name} não foi encontrado")
            return
        
        try:
            if platform.system() == 'Windows':
                os.startfile(full_path)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', full_path])
            else:
                subprocess.Popen(['xdg-open', full_path])
        except Exception as e:
            logging.error(f"Erro ao abrir documento {doc_name}: {str(e)}")
            self.show_custom_message("Erro", f"Não foi possível abrir {doc_name}")
    
    def open_declaration(self):
        """Abre declaração do Bolsa Família"""
        threading.Thread(
            target=self.open_document, 
            args=("Bolsa Familia", "DECLARAÇÃO BOLSA FAMÍLIA.docx"),
            daemon=True
        ).start()
    
    def open_presence(self):
        """Abre declaração de comparecimento"""
        threading.Thread(
            target=self.open_document, 
            args=("Presença", "DECLARAÇÃO DE COMPARECIMENTO.docx"),
            daemon=True
        ).start()
    
    def open_provisoria(self):
        """Abre declaração provisória"""
        threading.Thread(
            target=self.open_document, 
            args=("Provisória", "Provisória.docx"),
            daemon=True
        ).start()
    
    def open_siepe(self):
        """Abre o site do SIEPE"""
        try:
            webbrowser.open("https://www.siepe.educacao.pe.gov.br/")
        except Exception as e:
            logging.error(f"Erro ao abrir SIEPE: {str(e)}")
            self.show_custom_message("Erro", "Não foi possível abrir o SIEPE")
    
    def open_censo(self):
        """Abre o site do Censo Escolar"""
        try:
            webbrowser.open("https://censobasico.inep.gov.br/censobasico/#/")
        except Exception as e:
            logging.error(f"Erro ao abrir Censo Escolar: {str(e)}")
            self.show_custom_message("Erro", "Não foi possível abrir o Censo Escolar")
    
    def center_window(self, window: tk.Toplevel):
        """Centraliza uma janela na tela"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def show_custom_message(self, title: str, message: str):
        """Mostra uma mensagem personalizada"""
        custom_message_window = tk.Toplevel(self.root)
        custom_message_window.title(title)
        custom_message_window.configure(bg='#3B3B3B')
        custom_message_window.attributes('-topmost', 'true')
        
        # Centralizar janela
        self.center_window(custom_message_window)
        
        message_label = tk.Label(
            custom_message_window, 
            text=message, 
            font=('JetBrains Mono', 12), 
            bg='#3B3B3B', 
            fg='#ffffff'
        )
        message_label.pack(pady=10)
        
        close_button = tk.Button(
            custom_message_window, 
            text="Fechar", 
            font=('JetBrains Mono', 12), 
            command=custom_message_window.destroy, 
            bg='#007acc', 
            fg='#ffffff'
        )
        close_button.pack(pady=10)
        
        # Vincular Escape para fechar
        custom_message_window.bind("<Escape>", lambda e: custom_message_window.destroy())
    
    def open_about_window(self):
        """Abre a janela 'Sobre'"""
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre")
        about_window.attributes('-topmost', True)
        about_window.geometry('400x300')
        about_window.resizable(False, False)
        about_window.configure(bg='#3B3B3B')
        
        def close_about_window(event=None):
            about_window.destroy()
        
        about_window.bind("<Escape>", close_about_window)
        
        # Estilo para as abas
        notebook_style = ttk.Style()
        notebook_style.configure("TNotebook.Tab", font=('JetBrains Mono', 12))
        
        notebook = ttk.Notebook(about_window, style="TNotebook")
        notebook.pack(fill='both', expand=True)
        
        # Aba Informações
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text='Informações')
        
        info_text = """SIGE - Sistema de Informações e Gerenciamento Escolar
Versão 1.0
Desenvolvido para gestão escolar"""
        
        ttk.Label(
            info_frame, 
            text=info_text, 
            font=('JetBrains Mono', 12)
        ).pack(padx=10, pady=10)
        
        # Aba Créditos
        credits_frame = ttk.Frame(notebook)
        notebook.add(credits_frame, text='Créditos')
        
        ttk.Label(
            credits_frame, 
            text="Desenvolvido por:\n[Seu Nome]\n[Seu Email]", 
            font=('JetBrains Mono', 12)
        ).pack(padx=10, pady=10)
        
        # Aba Licença
        license_frame = ttk.Frame(notebook)
        notebook.add(license_frame, text='Licença')
        
        ttk.Label(
            license_frame, 
            text="Licença MIT\n\nCopyright (c) [Ano] [Seu Nome]", 
            font=('JetBrains Mono', 12)
        ).pack(padx=10, pady=10)

if __name__ == "__main__":
    # Configurar logging
    logging.info("Iniciando aplicação SIGE")
    
    # Obter arquivo CSV se fornecido como argumento
    csv_file = sys.argv[1] if len(sys.argv) > 1 else ""
    
    # Criar e executar aplicação
    root = tk.Tk()
    app = SIGEApplication(root, csv_file)
    root.mainloop()
    
    logging.info("Aplicação SIGE encerrada")
