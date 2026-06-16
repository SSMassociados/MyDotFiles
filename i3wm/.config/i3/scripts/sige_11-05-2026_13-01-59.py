#!/usr/bin/env python3

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
from typing import List, Tuple, Optional

# Configuração de logging
logging.basicConfig(
    filename='sige.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configurações de caminhos
DOCUMENTS_PATH = os.path.expanduser("~/Área de trabalho/AUSTRO/DECLARAÇÕES")
DEFAULT_PDF_VIEWER = {
    'Linux': 'qpdfview',
    'Windows': 'explorer',
    'Darwin': 'open'
}

class SIGEApplication:
    def __init__(self, root: tk.Tk, csv_file: str = ""):
        self.root = root
        self.csv_file = csv_file
        self.last_save_location = ""
        self.classes = self.load_classes() if csv_file else []
        self.students_data = []  # Para armazenar todos os alunos em memória
        
        # Carregar todos os alunos em memória se houver arquivo
        if self.csv_file:
            self.load_all_students()
        
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
            columns=("Matrícula", "Nome", "Nascimento", "Idade", "Turma"), 
            show="headings", 
            style="Custom.Treeview"
        )
        for col in ("Matrícula", "Nome", "Nascimento", "Idade", "Turma"):
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
            ("Turmas", self.open_turmas_window),
            ("SIEPE", self.open_siepe),
            ("Censo Escolar", self.open_censo)
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
                # TURMA está no índice 8
                return {row[8] for row in reader if len(row) > 8}
        except Exception as e:
            logging.error(f"Erro ao ler arquivo CSV: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao ler arquivo CSV: {str(e)}")
            return set()
    
    def load_all_students(self):
        """Carrega todos os alunos para memória"""
        try:
            with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Pular cabeçalho
                self.students_data = [tuple(row) for row in reader if len(row) >= 12]
                logging.info(f"Carregados {len(self.students_data)} alunos")
        except Exception as e:
            logging.error(f"Erro ao carregar alunos: {str(e)}")
            self.students_data = []
    
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
        
        notebook_style = ttk.Style()
        notebook_style.configure("TNotebook.Tab", font=('JetBrains Mono', 12))
        
        notebook = ttk.Notebook(about_window, style="TNotebook")
        notebook.pack(fill='both', expand=True)
        
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
        
        credits_frame = ttk.Frame(notebook)
        notebook.add(credits_frame, text='Créditos')
        
        ttk.Label(
            credits_frame, 
            text="Desenvolvido por:\nSidiclei\n", 
            font=('JetBrains Mono', 12)
        ).pack(padx=10, pady=10)
        
        license_frame = ttk.Frame(notebook)
        notebook.add(license_frame, text='Licença')
        
        ttk.Label(
            license_frame, 
            text="Licença MIT\n\nCopyright (c) 2024", 
            font=('JetBrains Mono', 12)
        ).pack(padx=10, pady=10)
    
    def search_student(self, student_name: str) -> List[Tuple[str, ...]]:
        """Pesquisa alunos pelo nome"""
        if not self.students_data:
            self.show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")
            return []
        
        try:
            found_students = []
            student_name_lower = student_name.lower()
            
            for row in self.students_data:
                if len(row) < 2:
                    continue
                
                nome_completo = row[1].lower()
                primeiro_nome = nome_completo.split()[0] if nome_completo else ""
                
                if student_name_lower == primeiro_nome or student_name_lower in nome_completo:
                    found_students.append(row)
            
            return sorted(found_students, key=lambda x: x[1].lower())
        except Exception as e:
            logging.error(f"Erro ao pesquisar aluno: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao pesquisar aluno: {str(e)}")
            return []
    
    def search_class(self, class_name: str) -> List[Tuple[str, ...]]:
        """Pesquisa alunos por turma"""
        if not self.students_data:
            self.show_custom_message("Erro", "Por favor, selecione um arquivo CSV.")
            return []
        
        try:
            return [row for row in self.students_data 
                   if len(row) > 8 and class_name.lower() == row[8].lower()]
        except Exception as e:
            logging.error(f"Erro ao pesquisar turma: {str(e)}")
            self.show_custom_message("Erro", f"Erro ao pesquisar turma: {str(e)}")
            return []
    
    def calculate_age(self, birth_date: str) -> str:
        """Calcula idade a partir da data de nascimento"""
        try:
            today = datetime.now()
            birth_date = pd.to_datetime(birth_date)
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
            tree.column(col, width=width + 10)
    
    def show_search_result(self, event=None):
        """Mostra resultados da pesquisa por aluno"""
        student_name = self.entry_student.get().strip()
        
        if not student_name:
            self.show_custom_message("Erro", "Por favor, insira o nome do aluno.")
            return
        
        student_name = student_name.split()[0]
        self.result_tree.delete(*self.result_tree.get_children())
        self.class_combobox.set("")
        
        found_students = self.search_student(student_name)
        
        if found_students:
            for i, student in enumerate(found_students):
                age = self.calculate_age(student[2])
                self.result_tree.insert(
                    "", "end", 
                    values=(student[0], student[1], student[2], age, student[8]), 
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
        
        self.result_tree.delete(*self.result_tree.get_children())
        self.entry_student.delete(0, tk.END)
        
        found_students = self.search_class(selected_class)
        
        if found_students:
            for i, student in enumerate(found_students):
                age = self.calculate_age(student[2])
                self.result_tree.insert(
                    "", "end", 
                    values=(student[0], student[1], student[2], age, selected_class), 
                    tags=('even' if i % 2 == 0 else 'odd')
                )
            
            self.occurrences_label.config(text=f"Ocorrências encontradas: {len(found_students)}")
            self.adjust_column_widths(self.result_tree)
        else:
            self.occurrences_label.config(text="Ocorrências encontradas: 0")
            self.show_custom_message("Resultado", "Nenhum aluno encontrado para esta turma.")
    
    def open_turmas_window(self):
        """Abre uma nova janela com informações das turmas em formato de tabela compacta"""
        if not self.students_data:
            self.show_custom_message("Erro", "Nenhum dado encontrado")
            return
        
        # Criar nova janela
        turmas_window = tk.Toplevel(self.root)
        turmas_window.title("Relatório de Turmas")
        turmas_window.configure(bg='#3B3B3B')
        
        # Frame principal
        main_container = tk.Frame(turmas_window, bg='#3B3B3B')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Título
        title_label = tk.Label(
            main_container,
            text="RELATÓRIO DE TURMAS",
            font=('JetBrains Mono', 14, 'bold'),
            bg='#3B3B3B',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 15))
        
        # Frame para a tabela (Treeview)
        table_frame = tk.Frame(main_container, bg='#3B3B3B')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Criar Treeview para exibir dados em formato de tabela
        columns = ("Grupo", "Turma", "Total Alunos")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10
        )
        
        # Configurar cabeçalhos
        tree.heading("Grupo", text="Grupo", anchor="center")
        tree.heading("Turma", text="Turma", anchor="center")
        tree.heading("Total Alunos", text="Total Alunos", anchor="center")
        
        # Configurar larguras das colunas
        tree.column("Grupo", width=200, minwidth=150, anchor="w")
        tree.column("Turma", width=250, minwidth=150, anchor="w")
        tree.column("Total Alunos", width=120, minwidth=100, anchor="center")
        
        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Processar dados e popular tabela
        turmas_dict = {}
        for student in self.students_data:
            turma = student[8] if len(student) > 8 else "Sem Turma"
            turmas_dict[turma] = turmas_dict.get(turma, 0) + 1
        
        # Identificar grupos
        grupos = {}
        for turma, total in sorted(turmas_dict.items()):
            if turma.startswith('EM35-'):
                prefixo = turma[:6] if len(turma) >= 6 else turma
            elif turma.startswith('EJAMED'):
                prefixo = turma.split('-')[0] if '-' in turma else turma
            else:
                prefixo = turma
            
            if prefixo not in grupos:
                grupos[prefixo] = []
            grupos[prefixo].append((turma, total))
        
        # Calcular total geral
        total_geral = sum(turmas_dict.values())
        
        # Popular a tabela
        for grupo, turmas in sorted(grupos.items()):
            grupo_total = sum(total for _, total in turmas)
            
            # Inserir linha do grupo
            tree.insert("", "end", values=(grupo, "TOTAL DO GRUPO", grupo_total), tags=('grupo',))
            
            # Inserir turmas do grupo
            for turma, total in sorted(turmas):
                tree.insert("", "end", values=("", turma, total), tags=('turma',))
        
        # Inserir linha de total geral
        tree.insert("", "end", values=("", "TOTAL GERAL", total_geral), tags=('total',))
        
        # Configurar tags para estilização
        tree.tag_configure('grupo', background='#2c3e50', foreground='white', font=('JetBrains Mono', 10, 'bold'))
        tree.tag_configure('turma', background='#f8f9fa', foreground='#333333')
        tree.tag_configure('total', background='#ecf0f1', foreground='#2c3e50', font=('JetBrains Mono', 10, 'bold'))
        
        # Alternar cores para turmas
        for i, item in enumerate(tree.get_children()):
            if tree.item(item, 'tags')[0] == 'turma':
                if i % 2 == 0:
                    tree.tag_configure('turma_even', background='#ffffff')
                    tree.item(item, tags=('turma', 'turma_even'))
                else:
                    tree.tag_configure('turma_odd', background='#f0f0f0')
                    tree.item(item, tags=('turma', 'turma_odd'))
        
        # Frame para botões
        button_frame = tk.Frame(main_container, bg='#3B3B3B')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Botão Exportar para PDF
        export_btn = tk.Button(
            button_frame,
            text="Exportar para PDF",
            font=('JetBrains Mono', 10, 'bold'),
            command=lambda: self.export_turmas_table_to_pdf(turmas_dict, grupos, total_geral, turmas_window),
            bg='#007acc',
            fg='#ffffff',
            padx=20,
            pady=5
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Botão Fechar
        close_btn = tk.Button(
            button_frame,
            text="Fechar",
            font=('JetBrains Mono', 10, 'bold'),
            command=turmas_window.destroy,
            bg='#dc3545',
            fg='#ffffff',
            padx=20,
            pady=5
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Atalho ESC para fechar
        turmas_window.bind("<Escape>", lambda e: turmas_window.destroy())
        
        # Ajustar tamanho da janela ao conteúdo
        turmas_window.update_idletasks()
        
        # Calcular altura baseada no número de linhas
        num_items = len(tree.get_children())
        row_height = 25
        header_height = 25
        calculated_height = min(num_items * row_height + header_height + 100, 500)
        
        # Definir geometria da janela
        turmas_window.geometry(f"600x{calculated_height}")
        self.center_window(turmas_window)
    
    def export_turmas_table_to_pdf(self, turmas_dict: dict, grupos: dict, total_geral: int, parent_window: tk.Toplevel):
        """Exporta o relatório de turmas para PDF em formato de tabela"""
        if not turmas_dict:
            self.show_custom_message("Erro", "Nenhum dado para exportar")
            return
        
        # Solicitar local para salvar
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialdir=self.last_save_location,
            initialfile="RELATORIO_TURMAS"
        )
        
        if not filename:
            return
        
        self.last_save_location = os.path.dirname(filename)
        filename = filename.replace(" ", "_").replace("-", "_")
        
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
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("<b>RELATÓRIO DE TURMAS</b>", title_style))
        
        # Subtítulo
        subtitle_style = ParagraphStyle(
            name='SubtitleStyle',
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#666666')
        )
        elements.append(Paragraph("Quantidade de Alunos por Turma", subtitle_style))
        
        # Data
        date_style = ParagraphStyle(
            name='DateStyle',
            fontSize=9,
            alignment=TA_CENTER,
            spaceAfter=25,
            textColor=colors.HexColor('#888888')
        )
        current_date = datetime.now().strftime("%d/%m/%Y às %H:%M")
        elements.append(Paragraph(f"Gerado em: {current_date}", date_style))
        
        # Preparar dados para a tabela
        table_data = [["GRUPO", "TURMA", "TOTAL ALUNOS"]]
        
        for grupo, turmas in sorted(grupos.items()):
            grupo_total = sum(total for _, total in turmas)
            
            # Adicionar linha do grupo
            table_data.append([grupo, "TOTAL DO GRUPO", str(grupo_total)])
            
            # Adicionar turmas
            for turma, total in sorted(turmas):
                table_data.append(["", turma, str(total)])
        
        # Adicionar total geral
        table_data.append(["", "TOTAL GERAL", str(total_geral)])
        
        # Configurar larguras
        col_widths = [180, 250, 100]
        pdf_table = Table(table_data, colWidths=col_widths)
        
        # Estilo da tabela
        table_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            
            # Alinhamento
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2c3e50')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
        ])
        
        # Destacar linhas de total
        for i in range(1, len(table_data)):
            if table_data[i][1] in ["TOTAL DO GRUPO", "TOTAL GERAL"]:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1'))
                table_style.add('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
        
        # Cores alternadas para turmas
        row_index = 1
        for i in range(1, len(table_data)):
            if table_data[i][1] not in ["TOTAL DO GRUPO", "TOTAL GERAL"] and table_data[i][0] == "":
                if row_index % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa'))
                row_index += 1
        
        pdf_table.setStyle(table_style)
        elements.append(pdf_table)
        
        # Rodapé
        footer_style = ParagraphStyle(
            name='FooterStyle',
            fontSize=8,
            alignment=TA_CENTER,
            spaceBefore=20,
            textColor=colors.HexColor('#95a5a6')
        )
        elements.append(Paragraph("SIGE - Sistema de Informações e Gerenciamento Escolar", footer_style))
        
        try:
            doc.build(elements)
            self.show_export_success_window(filename)
            logging.info(f"Relatório de turmas gerado: {filename}")
        except Exception as e:
            logging.error(f"Erro ao gerar relatório: {str(e)}")
            self.show_custom_message("Erro", f"Falha ao gerar relatório: {str(e)}")
    
    def export_turmas_to_pdf(self):
        """Exporta relatório de turmas com total por grupo e mesclagem vertical"""
        if not self.students_data:
            self.show_custom_message("Erro", "Nenhum dado encontrado")
            return
        
        # Agrupar alunos por turma
        turmas_dict = {}
        
        for student in self.students_data:
            turma = student[8] if len(student) > 8 else "Sem Turma"
            
            if turma in turmas_dict:
                turmas_dict[turma] += 1
            else:
                turmas_dict[turma] = 1
        
        if not turmas_dict:
            self.show_custom_message("Erro", "Nenhuma turma encontrada")
            return
        
        # Identificar grupos (turmas que compartilham o mesmo prefixo)
        grupos = {}
        turmas_por_grupo = {}
        
        for turma, total in sorted(turmas_dict.items()):
            # Extrair o prefixo da turma
            if turma.startswith('EM35-'):
                if len(turma) >= 6:
                    prefixo = turma[:6]  # EM35-1, EM35-2, EM35-3
                else:
                    prefixo = turma
            elif turma.startswith('EJAMED'):
                if '-' in turma:
                    prefixo = turma.split('-')[0]  # EJAMED
                else:
                    prefixo = turma
            else:
                prefixo = turma
            
            if prefixo not in grupos:
                grupos[prefixo] = []
                turmas_por_grupo[prefixo] = 0
            
            grupos[prefixo].append((turma, total))
            turmas_por_grupo[prefixo] += total
        
        # Ordenar grupos
        grupos_ordenados = sorted(grupos.items(), key=lambda x: x[0])
        
        # Solicitar local para salvar
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialdir=self.last_save_location,
            initialfile="RELATORIO_TURMAS"
        )
        
        if not filename:
            return
        
        self.last_save_location = os.path.dirname(filename)
        filename = filename.replace(" ", "_").replace("-", "_")
        
        # Criar documento PDF
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=60,
            bottomMargin=40
        )
        
        elements = []
        
        # Título principal
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("<b>RELATÓRIO DE TURMAS</b>", title_style))
        
        # Subtítulo
        subtitle_style = ParagraphStyle(
            name='SubtitleStyle',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#666666')
        )
        elements.append(Paragraph("Quantidade de Alunos por Turma", subtitle_style))
        
        # Data de geração
        date_style = ParagraphStyle(
            name='DateStyle',
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#888888')
        )
        current_date = datetime.now().strftime("%d de %B de %Y às %H:%M")
        elements.append(Paragraph(current_date, date_style))
        
        # Preparar dados para a tabela
        table_data = []
        span_positions = []  # Guardar informações de mesclagem
        
        # Adicionar cabeçalho
        table_data.append(["GRUPO/SÉRIE", "TURMA", "TOTAL ALUNOS"])
        
        for prefixo, turmas in grupos_ordenados:
            # Ordenar as turmas dentro do grupo
            turmas_ordenadas = sorted(turmas, key=lambda x: x[0])
            grupo_total = turmas_por_grupo[prefixo]
            num_turmas = len(turmas_ordenadas)
            
            # Guardar posição para mesclagem da coluna Grupo
            start_row = len(table_data)
            end_row = start_row + num_turmas - 1
            
            # Adicionar as linhas do grupo
            for i, (turma, total) in enumerate(turmas_ordenadas):
                if i == 0:
                    # Primeira linha do grupo: mostra o nome do grupo na coluna 1
                    table_data.append([prefixo, turma, str(total)])
                else:
                    # Linhas seguintes: apenas turma e total
                    table_data.append(["", turma, str(total)])
            
            # Registrar posição para mesclagem
            span_positions.append({
                'start': start_row,
                'end': end_row,
                'col': 0,  # Coluna Grupo (índice 0)
            })
            
            # Adicionar linha de total do grupo
            table_data.append(["", "TOTAL DO GRUPO", str(grupo_total)])
        
        # Calcular total geral
        total_geral = sum(turmas_por_grupo.values())
        
        # Adicionar linha de total geral
        table_data.append(["", "TOTAL GERAL", str(total_geral)])
        
        # Configurar larguras das colunas
        col_widths = [150, 250, 100]
        table = Table(table_data, colWidths=col_widths)
        
        # Estilo da tabela
        table_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Dados
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            
            # Alinhamento das colunas
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2c3e50')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
        ])
        
        # Destacar linhas de total do grupo
        for i in range(1, len(table_data)):
            if table_data[i][1] in ["TOTAL DO GRUPO", "TOTAL GERAL"]:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1'))
                table_style.add('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
        
        # Aplicar mesclagem vertical na coluna Grupo
        for span in span_positions:
            if span['start'] <= span['end']:
                table_style.add('SPAN', (span['col'], span['start']), (span['col'], span['end']))
                # Centralizar verticalmente o conteúdo mesclado
                for row in range(span['start'], span['end'] + 1):
                    table_style.add('ALIGN', (span['col'], row), (span['col'], row), 'CENTER')
                    table_style.add('VALIGN', (span['col'], row), (span['col'], row), 'MIDDLE')
        
        # Adicionar cores alternadas nas linhas de dados
        for i in range(1, len(table_data) - 1):
            if i % 2 == 0 and table_data[i][1] not in ["TOTAL DO GRUPO", "TOTAL GERAL"]:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa'))
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Rodapé
        footer_style = ParagraphStyle(
            name='FooterStyle',
            fontSize=8,
            alignment=TA_CENTER,
            spaceBefore=20,
            textColor=colors.HexColor('#95a5a6')
        )
        elements.append(Paragraph("SIGE - Sistema de Informações e Gerenciamento Escolar", footer_style))
        
        try:
            doc.build(elements)
            self.show_export_success_window(filename)
            logging.info(f"Relatório de turmas gerado: {filename}")
        except Exception as e:
            logging.error(f"Erro ao gerar relatório: {str(e)}")
            self.show_custom_message("Erro", f"Falha ao gerar relatório: {str(e)}")
    
    def create_pdf_table(self, data: List[List[str]], title: str = "", date: str = ""):
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
        
        header_style = TableStyle([
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12)
        ])
        
        data_style = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
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
        
        data = []
        for i, row_id in enumerate(self.result_tree.get_children(), start=1):
            row = self.result_tree.item(row_id)['values']
            data.append([i, row[0], row[1], " " * 80 + "."])
        
        if not data:
            self.show_custom_message("Erro", "Nenhum dado para exportar")
            return
        
        doc = SimpleDocTemplate(
            filename, 
            pagesize=letter, 
            leftMargin=20, 
            rightMargin=20,
            topMargin=20, 
            bottomMargin=20
        )
        elements = []
        
        ata_title = "ATA DE ASSINATURAS"
        if turma:
            ata_title += f" - \"{turma}\""
        
        title_style = ParagraphStyle(name='TitleStyle', fontSize=14, alignment=TA_CENTER)
        elements.append(Paragraph(f"<b>{ata_title}</b>", title_style))
        
        current_date = datetime.now().strftime("%d/%m/%Y - %A - %H:%M:%S")
        date_style = ParagraphStyle(name='DateStyle', fontSize=12, alignment=TA_CENTER)
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(current_date, date_style))
        elements.append(Spacer(1, 10))
        
        header = ["#", "Matrícula", "Nome", "Assinatura"]
        data.insert(0, header)
        
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
        
        for i in range(0, len(data), 2):
            data_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.beige)
        
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
        
        header = ["Matrícula", "Nome", "Nascimento", "Idade", "Turma"]
        data.insert(0, header)
        self.export_to_pdf(data)
    
    def show_export_success_window(self, filename: str):
        """Mostra janela de sucesso na exportação com auto-redimensionamento"""
        export_success_window = tk.Toplevel(self.root)
        export_success_window.title("Exportação Concluída")
        export_success_window.configure(bg='#3B3B3B')
        export_success_window.transient(self.root)
        
        container = tk.Frame(export_success_window, bg='#3B3B3B', padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        success_label = tk.Label(
            container, 
            text=f"Arquivo exportado com sucesso para:\n{filename}", 
            font=('JetBrains Mono', 11), 
            bg='#3B3B3B', 
            fg='#ffffff',
            justify=tk.CENTER
        )
        success_label.pack(pady=(0, 20))
        
        button_frame = tk.Frame(container, bg='#3B3B3B')
        button_frame.pack()
        
        buttons = [
            ("Visualizar", self.visualize_pdf, filename),
            ("Abrir Local", self.open_directory, os.path.dirname(filename)),
            ("Sair", export_success_window.destroy, None)
        ]
        
        for text, command, arg in buttons:
            btn = tk.Button(
                button_frame, text=text, font=('JetBrains Mono', 10, 'bold'), 
                command=lambda c=command, a=arg: c(a) if a is not None else c(),
                bg='#007acc', fg='#ffffff',
                padx=10
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        export_success_window.update_idletasks()
        export_success_window.geometry("") 
        export_success_window.minsize(export_success_window.winfo_width(), export_success_window.winfo_height())
        self.center_window(export_success_window)
        export_success_window.bind("<Escape>", lambda e: export_success_window.destroy())
    
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
            webbrowser.open("https://educacenso.inep.gov.br/educacenso/")
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
        """Mostra uma mensagem personalizada com auto-redimensionamento"""
        custom_message_window = tk.Toplevel(self.root)
        custom_message_window.title(title)
        custom_message_window.configure(bg='#3B3B3B')
        custom_message_window.attributes('-topmost', 'true')
        
        container = tk.Frame(custom_message_window, bg='#3B3B3B', padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        message_label = tk.Label(
            container, 
            text=message, 
            font=('JetBrains Mono', 12), 
            bg='#3B3B3B', 
            fg='#ffffff'
        )
        message_label.pack(pady=(0, 20))
        
        close_button = tk.Button(
            container, 
            text="Fechar", 
            font=('JetBrains Mono', 12, 'bold'), 
            command=custom_message_window.destroy, 
            bg='#007acc', 
            fg='#ffffff',
            padx=20
        )
        close_button.pack()
        
        custom_message_window.update_idletasks()
        custom_message_window.geometry("")
        self.center_window(custom_message_window)
        custom_message_window.bind("<Escape>", lambda e: custom_message_window.destroy())

if __name__ == "__main__":
    logging.info("Iniciando aplicação SIGE")
    csv_file = sys.argv[1] if len(sys.argv) > 1 else ""
    
    # Se não foi passado arquivo, pedir para selecionar
    if not csv_file:
        root = tk.Tk()
        root.withdraw()
        csv_file = filedialog.askopenfilename(
            title="Selecione o arquivo de dados CSV",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        root.destroy()
        
        if not csv_file:
            logging.info("Nenhum arquivo selecionado. Encerrando.")
            sys.exit(0)
    
    root = tk.Tk()
    app = SIGEApplication(root, csv_file)
    root.mainloop()
    logging.info("Aplicação SIGE encerrada")
