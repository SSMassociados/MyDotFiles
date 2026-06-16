#!/usr/bin/env python3
"""
SIGE - Sistema de Informações e Gerenciamento Escolar
Versão 2.0 — Bugs corrigidos e melhorias aplicadas
"""

import csv
import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.font as tkf
import sys
import unicodedata
import pandas as pd
from dataclasses import dataclass
import locale
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
from typing import List, Optional

# Configura locale DEPOIS de todos os imports
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename="sige.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
# Índices das colunas no CSV — altere aqui se o layout mudar
COL_MATRICULA = 0
COL_NOME      = 1
COL_NASC      = 2
COL_TURMA     = 8
COL_MIN_COLS  = 9   # mínimo de colunas para uma linha ser válida

DATE_FORMAT = "%d/%m/%Y"  # formato esperado no CSV; ajuste se necessário

DOCUMENTS_PATH = os.path.expanduser("~/Área de trabalho/AUSTRO/DECLARAÇÕES")

# Prefixos de grupos de turmas — adicione novos padrões aqui
GRUPO_PREFIXOS = [
    ("EM35-", 6),   # EM35-1A, EM35-2B …  → pega os primeiros 6 chars
    ("EJAMED", 6),  # EJAMED-1, EJAMED-2 … → pega os primeiros 6 chars
]

# ---------------------------------------------------------------------------
# Modelo de dados
# ---------------------------------------------------------------------------
@dataclass
class Aluno:
    matricula: str
    nome: str
    nascimento: str
    turma: str

    # campos extras brutos para não perder dados do CSV
    dados_raw: tuple = ()

    def nome_normalizado(self) -> str:
        """Nome sem acentos e em minúsculas, para comparações."""
        sem_acento = unicodedata.normalize("NFD", self.nome)
        sem_acento = sem_acento.encode("ascii", "ignore").decode("ascii")
        return sem_acento.lower()


# ---------------------------------------------------------------------------
# Repositório — leitura do CSV
# ---------------------------------------------------------------------------
class StudentRepository:
    """Isola toda a lógica de leitura e consulta ao arquivo CSV."""

    ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")

    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self._alunos: List[Aluno] = []
        self._turmas: set = set()
        self._load()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def _open_csv(self):
        """Abre o CSV tentando encodings comuns, evitando UnicodeDecodeError."""
        for enc in self.ENCODINGS:
            try:
                f = open(self.csv_file, newline="", encoding=enc)
                f.read(512)          # lê um trecho para validar o encoding
                f.seek(0)
                logging.info(f"CSV aberto com encoding={enc}")
                return f
            except (UnicodeDecodeError, LookupError):
                continue
        raise ValueError(
            f"Não foi possível determinar o encoding de '{self.csv_file}'. "
            "Salve o arquivo como UTF-8 e tente novamente."
        )

    def _load(self):
        if not os.path.exists(self.csv_file):
            logging.error(f"Arquivo CSV não encontrado: {self.csv_file}")
            return

        try:
            with self._open_csv() as f:
                reader = csv.reader(f)
                next(reader, None)   # pula cabeçalho
                for row in reader:
                    if len(row) < COL_MIN_COLS:
                        continue
                    aluno = Aluno(
                        matricula=row[COL_MATRICULA],
                        nome=row[COL_NOME],
                        nascimento=row[COL_NASC],
                        turma=row[COL_TURMA],
                        dados_raw=tuple(row),
                    )
                    self._alunos.append(aluno)
                    self._turmas.add(aluno.turma)

            logging.info(f"Carregados {len(self._alunos)} alunos")
        except Exception as exc:
            logging.error(f"Erro ao carregar CSV: {exc}")
            raise

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    @property
    def turmas(self) -> set:
        return self._turmas

    def buscar_por_nome(self, texto: str) -> List[Aluno]:
        """Busca por nome completo ou parcial, sem distinção de acento."""
        # CORREÇÃO: não truncar aqui — a função recebe o texto completo
        busca = _normalizar(texto)
        resultado = [
            a for a in self._alunos
            if busca in a.nome_normalizado()
        ]
        return sorted(resultado, key=lambda a: a.nome.lower())

    def buscar_por_turma(self, turma: str) -> List[Aluno]:
        turma_low = turma.lower()
        return [a for a in self._alunos if a.turma.lower() == turma_low]

    def agrupar_turmas(self) -> dict:
        """Retorna {prefixo: [(turma, total), ...]} agrupado por padrão."""
        contagem: dict[str, int] = {}
        for a in self._alunos:
            contagem[a.turma] = contagem.get(a.turma, 0) + 1

        grupos: dict[str, list] = {}
        for turma, total in sorted(contagem.items()):
            prefixo = _extrair_prefixo(turma)
            grupos.setdefault(prefixo, []).append((turma, total))

        return grupos


# ---------------------------------------------------------------------------
# Exportador PDF — isolado da UI
# ---------------------------------------------------------------------------
class PDFExporter:
    """Centraliza geração de PDFs, sem dependências de Tkinter."""

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_filename(path: str) -> str:
        """
        CORREÇÃO: substitui espaços/hifens SOMENTE no nome do arquivo,
        nunca no caminho do diretório.
        """
        diretorio = os.path.dirname(path)
        nome = os.path.basename(path)
        nome = nome.replace(" ", "_").replace("-", "_")
        return os.path.join(diretorio, nome)

    @staticmethod
    def _titulo_paragrafo(text: str, size: int = 14) -> Paragraph:
        style = ParagraphStyle(
            name="T", fontSize=size, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )
        return Paragraph(f"<b>{text}</b>", style)

    @staticmethod
    def _data_paragrafo(text: str) -> Paragraph:
        style = ParagraphStyle(
            name="D", fontSize=11, alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
        )
        return Paragraph(text, style)

    @staticmethod
    def _make_table(data, col_widths=None) -> Table:
        """
        CORREÇÃO: mescla header_style e data_style num único TableStyle
        para evitar que o segundo setStyle() sobrescreva o primeiro.
        """
        table = Table(data, colWidths=col_widths)
        style = TableStyle([
            # Cabeçalho
            ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
            ("BACKGROUND",   (0, 0), (-1, 0),  colors.grey),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.whitesmoke),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("BOTTOMPADDING",(0, 0), (-1, 0),  12),
            ("TOPPADDING",   (0, 0), (-1, 0),  3),
            # Dados
            ("ALIGN",        (0, 1), (-1, -1), "LEFT"),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 10),
            ("GRID",         (0, 0), (-1, -1), 1, colors.black),
        ])
        # Linhas zebra
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add("BACKGROUND", (0, i), (-1, i), colors.beige)
        table.setStyle(style)
        return table

    # ------------------------------------------------------------------
    # Exportações públicas
    # ------------------------------------------------------------------
    def exportar_resultados(self, dados: list, filename: str) -> str:
        filename = self._safe_filename(filename)
        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50,
        )
        elements = [self._make_table(dados)]
        doc.build(elements)
        logging.info(f"Resultados exportados: {filename}")
        return filename

    def exportar_ata(self, dados: list, turma: str, filename: str) -> str:
        filename = self._safe_filename(filename)
        doc = SimpleDocTemplate(
            filename, pagesize=letter,
            leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20,
        )
        titulo = f'ATA DE ASSINATURAS{f" - \"{turma}\"" if turma else ""}'
        data_str = datetime.now().strftime("%d/%m/%Y - %A - %H:%M:%S")
#       data_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
        elements = [
            self._titulo_paragrafo(titulo),
            Spacer(1, 5),
            self._data_paragrafo(data_str),
            Spacer(1, 10),
            self._make_table(dados),
        ]
        doc.build(elements)
        logging.info(f"Ata exportada: {filename}")
        return filename

    def exportar_turmas(self, grupos: dict, total_geral: int, filename: str) -> str:
        filename = self._safe_filename(filename)
        doc = SimpleDocTemplate(
            filename, pagesize=A4,
            leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50,
        )

        data = [["GRUPO", "TURMA", "TOTAL ALUNOS"]]
        for grupo, turmas in sorted(grupos.items()):
            grupo_total = sum(t for _, t in turmas)
            data.append([grupo, "TOTAL DO GRUPO", str(grupo_total)])
            for turma, total in sorted(turmas):
                data.append(["", turma, str(total)])
        data.append(["", "TOTAL GERAL", str(total_geral)])

        col_widths = [180, 250, 100]
        table = Table(data, colWidths=col_widths)

        style = TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#2c3e50")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  11),
            ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  10),
            ("TOPPADDING",    (0, 0), (-1, 0),  10),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 10),
            ("VALIGN",        (0, 1), (-1, -1), "MIDDLE"),
            ("ALIGN",         (2, 1), (2, -1),  "CENTER"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
            ("BOX",           (0, 0), (-1, -1), 1,   colors.HexColor("#2c3e50")),
        ])

        for i, row in enumerate(data[1:], start=1):
            if row[1] in ("TOTAL DO GRUPO", "TOTAL GERAL"):
                style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#ecf0f1"))
                style.add("FONTNAME",   (0, i), (-1, i), "Helvetica-Bold")
            elif i % 2 == 0:
                style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8f9fa"))

        table.setStyle(style)

        data_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
        rodape = ParagraphStyle(
            name="F", fontSize=8, alignment=TA_CENTER,
            spaceBefore=20, textColor=colors.HexColor("#95a5a6"),
        )
        elements = [
            self._titulo_paragrafo("RELATÓRIO DE TURMAS", 16),
            Spacer(1, 6),
            self._data_paragrafo(f"Gerado em: {data_str}"),
            Spacer(1, 20),
            table,
            Spacer(1, 10),
            Paragraph("SIGE - Sistema de Informações e Gerenciamento Escolar", rodape),
        ]
        doc.build(elements)
        logging.info(f"Relatório de turmas exportado: {filename}")
        return filename


# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------
def _normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas."""
    sem = unicodedata.normalize("NFD", texto)
    sem = sem.encode("ascii", "ignore").decode("ascii")
    return sem.lower()


def _extrair_prefixo(turma: str) -> str:
    """Extrai o prefixo de grupo a partir do nome da turma."""
    for prefixo, tamanho in GRUPO_PREFIXOS:
        if turma.startswith(prefixo):
            return turma[:tamanho] if len(turma) >= tamanho else turma
    return turma


def _calcular_idade(data_nasc: str) -> str:
    """
    Calcula a idade a partir da data de nascimento.
    CORREÇÃO: tenta o formato fixo primeiro, evitando ambiguidade de locale.
    """
    try:
        hoje = datetime.now()
        # Tenta o formato configurado primeiro
        try:
            dt = datetime.strptime(data_nasc.strip(), DATE_FORMAT)
        except ValueError:
            dt = pd.to_datetime(data_nasc)
        idade = relativedelta(hoje, dt)
        return f"{idade.years} Anos, {idade.months} Meses e {idade.days} Dias"
    except Exception as exc:
        logging.warning(f"Data inválida '{data_nasc}': {exc}")
        return "Data inválida"


def _abrir_arquivo(caminho: str):
    """Abre um arquivo com o aplicativo padrão do sistema operacional."""
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(caminho)
        elif sistema == "Darwin":
            subprocess.Popen(["open", caminho])
        else:
            # CORREÇÃO: usa xdg-open como fallback universal no Linux
            subprocess.Popen(["xdg-open", caminho])
    except Exception as exc:
        logging.error(f"Erro ao abrir '{caminho}': {exc}")
        raise


# ---------------------------------------------------------------------------
# UI principal
# ---------------------------------------------------------------------------
class SIGEApplication:
    def __init__(self, root: tk.Tk, csv_file: str = ""):
        self.root = root
        self.csv_file = csv_file
        self.last_save_location = ""
        self.repo: Optional[StudentRepository] = None
        self.exporter = PDFExporter()

        if csv_file:
            self._carregar_repositorio(csv_file)

        self._setup_ui()
        self._setup_bindings()

    # ------------------------------------------------------------------
    # Carregamento
    # ------------------------------------------------------------------
    def _carregar_repositorio(self, csv_file: str):
        """Carrega o repositório com indicador de progresso."""
        try:
            self.repo = StudentRepository(csv_file)
        except Exception as exc:
            logging.error(f"Falha ao carregar repositório: {exc}")
            self._mensagem(
                "Erro ao abrir CSV",
                f"{exc}\n\nVerifique se o arquivo está íntegro e tente novamente.",
            )
            self.repo = None

    # ------------------------------------------------------------------
    # Configuração da UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        self.root.title("Sistema de Informações e Gerenciamento Escolar")
        self.root.configure(bg="#3B3B3B")

        style = ttk.Style(self.root)
        for widget, font in [
            ("Treeview.Heading", ("JetBrains Mono", 12)),
            ("TButton",          ("JetBrains Mono", 12)),
            ("TLabel",           ("JetBrains Mono", 12)),
            ("TEntry",           ("JetBrains Mono", 12)),
            ("Treeview",         ("JetBrains Mono", 11)),
        ]:
            style.configure(widget, font=font)
        style.configure("Treeview", rowheight=25)
        style.configure("Custom.Treeview", background="#3B3B3B", foreground="#ffffff")

        ttk.Label(
            self.root,
            text="SISTEMA DE INFORMAÇÕES E GERENCIAMENTO ESCOLAR",
            font=("JetBrains Mono", 12),
            background="#333333",
            foreground="#ffffff",
        ).pack(side=tk.TOP, pady=10)

        self.main_frame = tk.Frame(self.root, bg="#3B3B3B")
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self._setup_search_frame()
        self._setup_results_frame()
        self._setup_export_buttons()

        tk.Button(
            self.root, text="About", font=("JetBrains Mono", 10),
            command=self._open_about, bg="#333333", fg="#ffffff",
        ).pack(side=tk.RIGHT, anchor=tk.SE, padx=10, pady=10)

        self.entry_student.focus_set()

    def _setup_search_frame(self):
        f = tk.Frame(self.main_frame, bg="#3B3B3B")
        f.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Label(f, text="Aluno:", font=("JetBrains Mono", 12),
                 bg="#3B3B3B", fg="#ffffff").pack(side=tk.LEFT, padx=(5, 0))

        self.entry_student = tk.Entry(f, font=("JetBrains Mono", 12),
                                      bg="#2d2d32", fg="#ffffff")
        self.entry_student.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.search_button = tk.Button(
            f, text="Pesquisar", font=("JetBrains Mono", 12),
            command=self._pesquisar_aluno, bg="#007acc", fg="#ffffff",
        )
        self.search_button.pack(side=tk.LEFT, padx=(10, 5))

        tk.Label(f, text="Turma:", font=("JetBrains Mono", 12),
                 bg="#3B3B3B", fg="#ffffff").pack(side=tk.LEFT, padx=(5, 0))

        turmas = sorted(self.repo.turmas) if self.repo else []
        self.class_combobox = ttk.Combobox(
            f, values=turmas, font=("JetBrains Mono", 12), state="readonly",
        )
        self.class_combobox.pack(side=tk.LEFT, padx=(0, 5))
        self.class_combobox.bind("<<ComboboxSelected>>", self._selecionar_turma)

    def _setup_results_frame(self):
        f = tk.Frame(self.main_frame, bg="#3B3B3B")
        f.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(f, text="Resultados:", font=("JetBrains Mono", 12),
                 bg="#3B3B3B", fg="#ffffff").pack(pady=5)

        cols = ("Matrícula", "Nome", "Nascimento", "Idade", "Turma")
        self.result_tree = ttk.Treeview(f, columns=cols, show="headings",
                                         style="Custom.Treeview")
        for col in cols:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, stretch=True)
        self.result_tree.tag_configure("even", background="#2d2d32", foreground="#ffffff")
        self.result_tree.tag_configure("odd",  background="#3B3B3B", foreground="#ffffff")
        self.result_tree.pack(expand=True, fill="both")

        self.occurrences_label = tk.Label(
            self.main_frame, font=("JetBrains Mono", 12),
            bg="#3B3B3B", fg="#ffffff",
        )
        self.occurrences_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))

    def _setup_export_buttons(self):
        f = tk.Frame(self.root, bg="#3B3B3B")
        f.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        botoes = [
            ("Resultados",    self._export_resultados),
            ("Ata",           self._export_ata),
            ("Bolsa",         self._open_declaration),
            ("Presença",      self._open_presence),
            ("Provisória",    self._open_provisoria),
            ("Turmas",        self._open_turmas_window),
            ("SIEPE",         self._open_siepe),
            ("Censo Escolar", self._open_censo),
        ]
        for text, cmd in botoes:
            tk.Button(
                f, text=text, font=("JetBrains Mono", 12),
                command=cmd, bg="#007acc", fg="#ffffff", padx=12, pady=4,
            ).pack(side=tk.LEFT, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Atalhos de teclado
    # ------------------------------------------------------------------
    def _setup_bindings(self):
        self.root.bind("<Return>",    self._pesquisar_aluno)
        self.root.bind("<Escape>",    lambda e: self.root.destroy())
        self.root.bind("<Control-q>", lambda e: self.root.destroy())
        self.root.bind("<F1>",        lambda e: self._open_about())
        # CORREÇÃO: retorna "break" para bloquear o comportamento padrão do Tk
        self.root.bind("<Tab>",       self._tab_frente)
        self.root.bind("<Shift-Tab>", self._tab_atras)

    def _tab_frente(self, event):
        foco = self.root.focus_get()
        if foco == self.entry_student:
            self.class_combobox.focus_set()
        elif foco == self.class_combobox:
            self.search_button.focus_set()
        return "break"   # ← impede propagação dupla

    def _tab_atras(self, event):
        foco = self.root.focus_get()
        if foco == self.search_button:
            self.class_combobox.focus_set()
        elif foco == self.class_combobox:
            self.entry_student.focus_set()
        return "break"

    # ------------------------------------------------------------------
    # Pesquisa
    # ------------------------------------------------------------------
    def _pesquisar_aluno(self, event=None):
        """
        CORREÇÃO: não trunca o texto antes de buscar; passa o nome completo.
        A normalização de acentos acontece dentro do repositório.
        """
        texto = self.entry_student.get().strip()
        if not texto:
            self._mensagem("Atenção", "Digite o nome (ou parte do nome) do aluno.")
            return

        if not self.repo:
            self._mensagem("Erro", "Nenhum arquivo de dados carregado.")
            return

        self.result_tree.delete(*self.result_tree.get_children())
        self.class_combobox.set("")

        resultado = self.repo.buscar_por_nome(texto)
        self._popular_treeview(resultado)

        if not resultado:
            self._mensagem("Resultado", f"Nenhum aluno encontrado para \"{texto}\".")

        self.entry_student.select_range(0, tk.END)
        logging.info(f"Busca por nome='{texto}' → {len(resultado)} resultado(s)")

    def _selecionar_turma(self, event=None):
        turma = self.class_combobox.get()
        if not turma or not self.repo:
            return

        self.result_tree.delete(*self.result_tree.get_children())
        self.entry_student.delete(0, tk.END)

        resultado = self.repo.buscar_por_turma(turma)
        self._popular_treeview(resultado)

        if not resultado:
            self._mensagem("Resultado", f"Nenhum aluno encontrado na turma \"{turma}\".")

        logging.info(f"Seleção de turma='{turma}' → {len(resultado)} aluno(s)")

    def _popular_treeview(self, alunos: List[Aluno]):
        for i, aluno in enumerate(alunos):
            idade = _calcular_idade(aluno.nascimento)
            self.result_tree.insert(
                "", "end",
                values=(aluno.matricula, aluno.nome, aluno.nascimento, idade, aluno.turma),
                tags=("even" if i % 2 == 0 else "odd"),
            )
        total = len(alunos)
        self.occurrences_label.config(text=f"Ocorrências encontradas: {total}")
        if total:
            self._ajustar_colunas(self.result_tree)

    # ------------------------------------------------------------------
    # Exportações
    # ------------------------------------------------------------------
    def _export_resultados(self):
        linhas = [self.result_tree.item(rid)["values"]
                  for rid in self.result_tree.get_children()]
        if not linhas:
            self._mensagem("Erro", "Nenhum resultado para exportar.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialdir=self.last_save_location,
            initialfile="RESULTADOS",
        )
        if not filename:
            return

        self.last_save_location = os.path.dirname(filename)
        cabecalho = [["Matrícula", "Nome", "Nascimento", "Idade", "Turma"]]
        try:
            path = self.exporter.exportar_resultados(cabecalho + linhas, filename)
            self._sucesso_exportacao(path)
        except Exception as exc:
            self._mensagem("Erro", f"Falha ao exportar: {exc}")

    def _export_ata(self):
        turma = self.class_combobox.get()
        linhas = []
        for i, rid in enumerate(self.result_tree.get_children(), start=1):
            row = self.result_tree.item(rid)["values"]
            linhas.append([i, row[0], row[1], " " * 80 + "."])

        if not linhas:
            self._mensagem("Erro", "Nenhum dado para exportar na ata.")
            return

        fname_ini = f"ATA_{turma.replace(' ', '_')}" if turma else "ATA"
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialfile=fname_ini,
            initialdir=self.last_save_location,
        )
        if not filename:
            return

        self.last_save_location = os.path.dirname(filename)
        cabecalho = [["#", "Matrícula", "Nome", "Assinatura"]]
        try:
            path = self.exporter.exportar_ata(cabecalho + linhas, turma, filename)
            self._sucesso_exportacao(path)
        except Exception as exc:
            self._mensagem("Erro", f"Falha ao exportar ata: {exc}")

    # ------------------------------------------------------------------
    # Janela de turmas
    # ------------------------------------------------------------------
    def _open_turmas_window(self):
        if not self.repo or not self.repo.turmas:
            self._mensagem("Erro", "Nenhum dado de turmas disponível.")
            return

        grupos = self.repo.agrupar_turmas()
        total_geral = sum(t for lst in grupos.values() for _, t in lst)

        win = tk.Toplevel(self.root)
        win.title("Relatório de Turmas")
        win.configure(bg="#3B3B3B")
        win.bind("<Escape>", lambda e: win.destroy())

        container = tk.Frame(win, bg="#3B3B3B")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(container, text="RELATÓRIO DE TURMAS",
                 font=("JetBrains Mono", 14, "bold"),
                 bg="#3B3B3B", fg="#ffffff").pack(pady=(0, 15))

        table_frame = tk.Frame(container, bg="#3B3B3B")
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Grupo", "Turma", "Total Alunos")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col, anchor="center")
        tree.column("Grupo",       width=200, minwidth=150, anchor="w")
        tree.column("Turma",       width=250, minwidth=150, anchor="w")
        tree.column("Total Alunos",width=120, minwidth=100, anchor="center")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        tree.tag_configure("grupo", background="#2c3e50", foreground="white",
                            font=("JetBrains Mono", 10, "bold"))
        tree.tag_configure("turma_par",  background="#f8f9fa", foreground="#333333")
        tree.tag_configure("turma_impar",background="#ffffff",  foreground="#333333")
        tree.tag_configure("total", background="#ecf0f1", foreground="#2c3e50",
                            font=("JetBrains Mono", 10, "bold"))

        idx_turma = 0
        for grupo, turmas in sorted(grupos.items()):
            grupo_total = sum(t for _, t in turmas)
            tree.insert("", "end", values=(grupo, "TOTAL DO GRUPO", grupo_total),
                        tags=("grupo",))
            for turma, total in sorted(turmas):
                tag = "turma_par" if idx_turma % 2 == 0 else "turma_impar"
                tree.insert("", "end", values=("", turma, total), tags=(tag,))
                idx_turma += 1
        tree.insert("", "end", values=("", "TOTAL GERAL", total_geral), tags=("total",))

        btn_frame = tk.Frame(container, bg="#3B3B3B")
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Button(
            btn_frame, text="Exportar para PDF",
            font=("JetBrains Mono", 10, "bold"),
            command=lambda: self._export_turmas(grupos, total_geral, win),
            bg="#007acc", fg="#ffffff", padx=20, pady=5,
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="Fechar",
            font=("JetBrains Mono", 10, "bold"),
            command=win.destroy,
            bg="#dc3545", fg="#ffffff", padx=20, pady=5,
        ).pack(side=tk.RIGHT, padx=5)

        win.update_idletasks()
        num_items = len(tree.get_children())
        altura = min(num_items * 25 + 150, 550)
        win.geometry(f"620x{altura}")
        self._centralizar(win)

    def _export_turmas(self, grupos: dict, total_geral: int, parent: tk.Toplevel):
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
            initialdir=self.last_save_location,
            initialfile="RELATORIO_TURMAS",
            parent=parent,
        )
        if not filename:
            return
        self.last_save_location = os.path.dirname(filename)
        try:
            path = self.exporter.exportar_turmas(grupos, total_geral, filename)
            self._sucesso_exportacao(path)
        except Exception as exc:
            self._mensagem("Erro", f"Falha ao exportar relatório de turmas: {exc}")

    # ------------------------------------------------------------------
    # Abrir documentos (thread-safe)
    # ------------------------------------------------------------------
    def _abrir_doc_async(self, nome: str, arquivo: str):
        """
        CORREÇÃO: separa a abertura do arquivo (pode ser lenta) da
        exibição de erros (deve ocorrer na thread principal via after()).
        """
        caminho = os.path.join(DOCUMENTS_PATH, arquivo)

        def _tarefa():
            try:
                _abrir_arquivo(caminho)
            except Exception as exc:
                # agenda a exibição da mensagem na thread principal
                self.root.after(
                    0,
                    lambda: self._mensagem("Erro", f"Não foi possível abrir {nome}:\n{exc}"),
                )

        threading.Thread(target=_tarefa, daemon=True).start()

    def _open_declaration(self):
        self._abrir_doc_async("Bolsa Família", "DECLARAÇÃO BOLSA FAMÍLIA.docx")

    def _open_presence(self):
        self._abrir_doc_async("Presença", "DECLARAÇÃO DE COMPARECIMENTO.docx")

    def _open_provisoria(self):
        self._abrir_doc_async("Provisória", "Provisória.docx")

    def _open_siepe(self):
        try:
            webbrowser.open("https://www.siepe.educacao.pe.gov.br/")
        except Exception as exc:
            self._mensagem("Erro", f"Não foi possível abrir o SIEPE:\n{exc}")

    def _open_censo(self):
        try:
            webbrowser.open("https://educacenso.inep.gov.br/educacenso/")
        except Exception as exc:
            self._mensagem("Erro", f"Não foi possível abrir o Censo Escolar:\n{exc}")

    # ------------------------------------------------------------------
    # Janela About
    # ------------------------------------------------------------------
    def _open_about(self):
        win = tk.Toplevel(self.root)
        win.title("Sobre")
        win.attributes("-topmost", True)
        win.geometry("400x300")
        win.resizable(False, False)
        win.configure(bg="#3B3B3B")
        win.bind("<Escape>", lambda e: win.destroy())

        ttk.Style().configure("TNotebook.Tab", font=("JetBrains Mono", 12))
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True)

        abas = [
            ("Informações", "SIGE - Sistema de Informações e Gerenciamento Escolar\nVersão 2.0\nDesenvolvido para gestão escolar"),
            ("Créditos",    "Desenvolvido por:\nSidiclei"),
            ("Licença",     "Licença MIT\n\nCopyright (c) 2024"),
        ]
        for titulo, texto in abas:
            frame = ttk.Frame(nb)
            nb.add(frame, text=titulo)
            ttk.Label(frame, text=texto, font=("JetBrains Mono", 12)).pack(padx=10, pady=10)

    # ------------------------------------------------------------------
    # Janela de sucesso na exportação
    # ------------------------------------------------------------------
    def _sucesso_exportacao(self, filename: str):
        win = tk.Toplevel(self.root)
        win.title("Exportação Concluída")
        win.configure(bg="#3B3B3B")
        win.transient(self.root)
        win.bind("<Escape>", lambda e: win.destroy())

        container = tk.Frame(win, bg="#3B3B3B", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text=f"Arquivo exportado com sucesso:\n{filename}",
            font=("JetBrains Mono", 11),
            bg="#3B3B3B", fg="#ffffff", justify=tk.CENTER,
        ).pack(pady=(0, 20))

        btn_frame = tk.Frame(container, bg="#3B3B3B")
        btn_frame.pack()

        acoes = [
            ("Visualizar",  lambda: _abrir_arquivo(filename)),
            ("Abrir pasta", lambda: _abrir_arquivo(os.path.dirname(filename))),
            ("Fechar",      win.destroy),
        ]
        for texto, cmd in acoes:
            tk.Button(
                btn_frame, text=texto, font=("JetBrains Mono", 10, "bold"),
                command=cmd, bg="#007acc", fg="#ffffff", padx=10,
            ).pack(side=tk.LEFT, padx=5)

        win.update_idletasks()
        win.geometry("")
        win.minsize(win.winfo_width(), win.winfo_height())
        self._centralizar(win)

    # ------------------------------------------------------------------
    # Utilitários de UI
    # ------------------------------------------------------------------
    def _ajustar_colunas(self, tree: ttk.Treeview):
        tree.update_idletasks()
        font = tkf.Font()
        larguras = {col: font.measure(col) for col in tree["columns"]}
        for child in tree.get_children():
            for idx, val in enumerate(tree.item(child)["values"]):
                col = tree["columns"][idx]
                w = font.measure(str(val))
                if w > larguras[col]:
                    larguras[col] = w
        for col, w in larguras.items():
            tree.column(col, width=w + 14)

    def _centralizar(self, win: tk.Toplevel):
        """
        CORREÇÃO: centraliza em relação à janela pai, não ao monitor primário,
        funcionando melhor em ambientes multi-monitor.
        """
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        px = self.root.winfo_x() + (self.root.winfo_width()  // 2) - (w // 2)
        py = self.root.winfo_y() + (self.root.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{px}+{py}")

    def _mensagem(self, titulo: str, mensagem: str):
        win = tk.Toplevel(self.root)
        win.title(titulo)
        win.configure(bg="#3B3B3B")
        win.attributes("-topmost", True)
        win.bind("<Escape>", lambda e: win.destroy())

        container = tk.Frame(win, bg="#3B3B3B", padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container, text=mensagem,
            font=("JetBrains Mono", 12),
            bg="#3B3B3B", fg="#ffffff",
        ).pack(pady=(0, 20))

        tk.Button(
            container, text="Fechar",
            font=("JetBrains Mono", 12, "bold"),
            command=win.destroy,
            bg="#007acc", fg="#ffffff", padx=20,
        ).pack()

        win.update_idletasks()
        win.geometry("")
        self._centralizar(win)


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.info("Iniciando SIGE v2.0")

    csv_file = sys.argv[1] if len(sys.argv) > 1 else ""

    if not csv_file:
        root = tk.Tk()
        root.withdraw()
        csv_file = filedialog.askopenfilename(
            title="Selecione o arquivo de dados CSV",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        root.destroy()

        if not csv_file:
            logging.info("Nenhum arquivo selecionado. Encerrando.")
            sys.exit(0)

    root = tk.Tk()
    app = SIGEApplication(root, csv_file)
    root.mainloop()
    logging.info("SIGE encerrado")
