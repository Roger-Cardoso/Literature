#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from tkinter import font as tkfont


APP_TITLE = "Editor Semântico"
PROJECT_EXT = ".narrproj"
READING_WORDS_PER_MINUTE = 200

INLINE_ELEMENTS = {
    "q": {"label": "Citação curta <q>", "attrs": ("cite", "title")},
    "cite": {"label": "Referência de obra <cite>", "attrs": ("title",)},
    "code": {"label": "Código <code>", "attrs": ("class", "lang")},
    "mark": {"label": "Destaque <mark>", "attrs": ("class",)},
    "sub": {"label": "Subscrito <sub>", "attrs": ("class",)},
    "sup": {"label": "Sobrescrito <sup>", "attrs": ("class",)},
    "kbd": {"label": "Entrada de teclado <kbd>", "attrs": ("class",)},
    "samp": {"label": "Saída de programa <samp>", "attrs": ("class",)},
    "var": {"label": "Variável <var>", "attrs": ("class",)},
    "abbr": {"label": "Abreviação <abbr>", "attrs": ("title", "class", "lang")},
    "small": {"label": "Texto secundário <small>", "attrs": ("class",)},
    "ins": {"label": "Texto inserido <ins>", "attrs": ("cite", "datetime", "class")},
    "del": {"label": "Texto removido <del>", "attrs": ("cite", "datetime", "class")},
    "span": {"label": "Contêiner genérico <span>", "attrs": ("class", "lang", "title")},
}

COLORS = {
    "app_bg": "#EEF2F7",
    "surface": "#FFFFFF",
    "surface_alt": "#F7F9FC",
    "border": "#DCE3EC",
    "text": "#172033",
    "muted": "#667085",
    "primary": "#5B5BD6",
    "primary_hover": "#4B4BC4",
    "header": "#172033",
    "header_muted": "#AEB8C9",
    "success": "#16856B",
    "danger": "#C2414B",
    "warning": "#B7791F",
    "editor": "#FFFFFF",
    "overlay": "#202A3B",
}


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def split_tokens(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    return [x for x in str(value).split() if x]


class FieldEditor:
    """Editor genérico de um atributo descrito no schema.json."""

    def __init__(self, parent, app, name, spec, initial=None):
        self.app = app
        self.name = name
        self.spec = spec
        self.multiple = bool(spec.get("multiple"))
        self.kind = spec.get("kind", "text")
        self.var = None
        self.widget = None
        self.id_by_label = {}

        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=10, pady=4)
        self.frame = frame

        required = " *" if spec.get("required") else ""
        ttk.Label(frame, text=f"{name}{required}", width=24).pack(side="left", anchor="n")

        if self.kind == "const":
            value = str(spec.get("value", ""))
            ttk.Label(frame, text=value).pack(side="left", fill="x", expand=True)
            self.var = tk.StringVar(value=value)
            return

        if self.kind == "enum":
            values = list(spec.get("values", []))
            if self.multiple:
                lb = tk.Listbox(
                    frame, selectmode="multiple", exportselection=False,
                    height=min(max(len(values), 3), 8)
                )
                for v in values:
                    lb.insert("end", v)
                lb.pack(side="left", fill="x", expand=True)
                self.widget = lb
                selected = set(split_tokens(initial))
                for i, v in enumerate(values):
                    if v in selected:
                        lb.selection_set(i)
            else:
                self.var = tk.StringVar()
                cb = ttk.Combobox(frame, textvariable=self.var, values=values, state="readonly")
                cb.pack(side="left", fill="x", expand=True)
                default = initial if initial not in (None, "") else spec.get("default", "")
                if default in values:
                    self.var.set(default)
                elif default:
                    # Mantém valor antigo mesmo que o schema tenha mudado.
                    cb.configure(state="normal")
                    self.var.set(str(default))
                self.widget = cb
            return

        if self.kind == "entity_ref":
            allowed = set(spec.get("entity_types", []))
            entities = [
                e for e in app.entities.values()
                if not allowed or e.get("type") in allowed
            ]
            labels = []
            for e in sorted(entities, key=lambda x: (x.get("type", ""), x.get("name", "").lower())):
                label = f'{e.get("name", "(sem nome)")} [{e.get("type", "?")}] — {e["id"]}'
                labels.append(label)
                self.id_by_label[label] = e["id"]

            if self.multiple:
                lb = tk.Listbox(
                    frame, selectmode="multiple", exportselection=False,
                    height=min(max(len(labels), 3), 8)
                )
                for label in labels:
                    lb.insert("end", label)
                lb.pack(side="left", fill="x", expand=True)
                selected = set(split_tokens(initial))
                for i, label in enumerate(labels):
                    if self.id_by_label[label] in selected:
                        lb.selection_set(i)
                self.widget = lb
            else:
                self.var = tk.StringVar()
                cb = ttk.Combobox(frame, textvariable=self.var, values=labels, state="readonly")
                cb.pack(side="left", fill="x", expand=True)
                current = str(initial or "")
                for label, entity_id in self.id_by_label.items():
                    if entity_id == current:
                        self.var.set(label)
                        break
                self.widget = cb
            return

        if self.kind == "text_ref":
            ids = [m["id"] for m in app.marks.values()]
            if self.multiple:
                lb = tk.Listbox(
                    frame, selectmode="multiple", exportselection=False,
                    height=min(max(len(ids), 3), 8)
                )
                for value in ids:
                    lb.insert("end", value)
                lb.pack(side="left", fill="x", expand=True)
                selected = set(split_tokens(initial))
                for i, value in enumerate(ids):
                    if value in selected:
                        lb.selection_set(i)
                self.widget = lb
            else:
                self.var = tk.StringVar(value=str(initial or ""))
                cb = ttk.Combobox(frame, textvariable=self.var, values=ids)
                cb.pack(side="left", fill="x", expand=True)
                self.widget = cb
            return

        self.var = tk.StringVar(value=str(initial or ""))
        entry = ttk.Entry(frame, textvariable=self.var)
        entry.pack(side="left", fill="x", expand=True)
        self.widget = entry

    def get(self):
        if self.kind == "const":
            return self.spec.get("value", "")

        if self.kind == "enum" and self.multiple:
            values = [self.widget.get(i) for i in self.widget.curselection()]
            return " ".join(values)

        if self.kind == "entity_ref":
            if self.multiple:
                ids = []
                for i in self.widget.curselection():
                    label = self.widget.get(i)
                    if label in self.id_by_label:
                        ids.append(self.id_by_label[label])
                return " ".join(ids)
            label = self.var.get()
            return self.id_by_label.get(label, "")

        if self.kind == "text_ref" and self.multiple:
            return " ".join(self.widget.get(i) for i in self.widget.curselection())

        return self.var.get().strip() if self.var is not None else ""


class ScrollableFrame(ttk.Frame):
    """Área vertical rolável que mantém widgets ttk comuns em ``content``."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(
            self, bg=COLORS["surface"], highlightthickness=0, borderwidth=0
        )
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._fit_content_width)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _update_scrollregion(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        needs_scroll = self.content.winfo_reqheight() > self.canvas.winfo_height()
        if needs_scroll and not self.scrollbar.winfo_ismapped():
            self.scrollbar.pack(side="right", fill="y")
        elif not needs_scroll and self.scrollbar.winfo_ismapped():
            self.scrollbar.pack_forget()

    def _fit_content_width(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)
        self._update_scrollregion()

    def _bind_wheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_wheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta * 3, "units")
        return "break"

    def destroy(self):
        self._unbind_wheel()
        super().destroy()


class OverlayPanel(tk.Frame):
    """Painel modal interno; mantém toda interação dentro da janela principal."""

    def __init__(self, app, title, subtitle="", width=640, height=480, scrollable=False):
        super().__init__(app, bg=COLORS["overlay"], highlightthickness=0)
        self.app = app
        self.result = None
        self._done = tk.BooleanVar(app, False)
        self.place(x=0, y=0, relwidth=1, relheight=1)

        self.desired_width = width
        self.desired_height = height
        self.card = tk.Frame(
            self, bg=COLORS["surface"], highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        self.card.place(relx=.5, rely=.5, anchor="center")

        header = tk.Frame(self.card, bg=COLORS["surface"], padx=24, pady=18)
        header.pack(fill="x")
        heading = tk.Frame(header, bg=COLORS["surface"])
        heading.pack(side="left", fill="x", expand=True)
        tk.Label(
            heading, text=title, bg=COLORS["surface"], fg=COLORS["text"],
            font=("TkDefaultFont", 15, "bold"), anchor="w"
        ).pack(fill="x")
        if subtitle:
            tk.Label(
                heading, text=subtitle, bg=COLORS["surface"], fg=COLORS["muted"],
                font=("TkDefaultFont", 9), anchor="w", justify="left", wraplength=500
            ).pack(fill="x", pady=(4, 0))
        ttk.Button(header, text="Fechar", style="Ghost.TButton", command=self.close).pack(side="right")

        ttk.Separator(self.card).pack(fill="x")
        if scrollable:
            self.body_scroll = ScrollableFrame(self.card)
            self.body_scroll.pack(fill="both", expand=True, padx=24, pady=18)
            self.body = self.body_scroll.content
        else:
            self.body_scroll = None
            self.body = ttk.Frame(self.card, padding=(24, 18))
            self.body.pack(fill="both", expand=True)

        self.error_var = tk.StringVar()
        self.error_label = tk.Label(
            self.card, textvariable=self.error_var, bg="#FFF1F2", fg=COLORS["danger"],
            anchor="w", justify="left", padx=24, pady=8, wraplength=max(width - 48, 240)
        )
        self.footer = ttk.Frame(self.card, padding=(24, 14))
        self.footer.pack(fill="x")

        app._register_overlay(self)
        self.bind("<Configure>", self._fit_card)
        self.after_idle(self._fit_card)
        self.lift()

    def _fit_card(self, event=None):
        available_width = event.width if event is not None else self.winfo_width()
        available_height = event.height if event is not None else self.winfo_height()
        if available_width <= 1 or available_height <= 1:
            available_width = self.app.winfo_width()
            available_height = self.app.winfo_height()
        width = min(self.desired_width, max(340, available_width - 32))
        height = min(self.desired_height, max(300, available_height - 32))
        self.card.place_configure(width=width, height=height)
        if hasattr(self, "error_label"):
            self.error_label.configure(wraplength=max(width - 48, 240))

    def set_error(self, message):
        self.error_var.set(message)
        if not self.error_label.winfo_ismapped():
            self.error_label.pack(fill="x", before=self.footer)

    def clear_error(self):
        self.error_var.set("")
        if self.error_label.winfo_ismapped():
            self.error_label.pack_forget()

    def wait_result(self):
        self.wait_variable(self._done)
        return self.result

    def close(self, result=None):
        if result is not None:
            self.result = result
        if not self._done.get():
            self._done.set(True)
        self.app._unregister_overlay(self)
        tk.Frame.destroy(self)

    def destroy(self):
        self.close()


class MessageOverlay(OverlayPanel):
    def __init__(self, app, title, message, kind="info", choices=None):
        height = 275 if len(message) < 240 else 360
        super().__init__(app, title, width=590, height=height)
        palette = {
            "info": ("i", COLORS["primary"], "Informação"),
            "success": ("✓", COLORS["success"], "Concluído"),
            "warning": ("!", COLORS["warning"], "Atenção"),
            "error": ("×", COLORS["danger"], "Erro"),
        }
        symbol, color, label = palette.get(kind, palette["info"])
        row = tk.Frame(self.body, bg=COLORS["surface"])
        row.pack(fill="both", expand=True)
        tk.Label(
            row, text=symbol, bg=color, fg="#FFFFFF", width=3,
            font=("TkDefaultFont", 16, "bold"), pady=8
        ).pack(side="left", anchor="n", padx=(0, 16))
        content = tk.Frame(row, bg=COLORS["surface"])
        content.pack(side="left", fill="both", expand=True)
        tk.Label(
            content, text=label.upper(), bg=COLORS["surface"], fg=color,
            font=("TkDefaultFont", 8, "bold"), anchor="w"
        ).pack(fill="x")
        tk.Label(
            content, text=message, bg=COLORS["surface"], fg=COLORS["text"],
            justify="left", anchor="nw", wraplength=430, font=("TkDefaultFont", 10)
        ).pack(fill="both", expand=True, pady=(8, 0))

        choices = choices or [("Entendi", True, "Accent.TButton")]
        for text, value, style in reversed(choices):
            ttk.Button(
                self.footer, text=text, style=style,
                command=lambda selected=value: self.close(selected)
            ).pack(side="right", padx=(8, 0))

        self.wait_result()


class ChoiceOverlay(OverlayPanel):
    """Seletor interno para operações com múltiplas marcações sobrepostas."""

    def __init__(self, app, title, message, options):
        super().__init__(app, title, message, width=650, height=430)
        self.options = list(options)
        self.listbox = tk.Listbox(
            self.body, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)
        for _value, label in self.options:
            self.listbox.insert("end", label)
        if self.options:
            self.listbox.selection_set(0)
        self.listbox.bind("<Double-Button-1>", lambda _event: self.accept())
        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Selecionar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))
        self.wait_result()

    def accept(self):
        selection = self.listbox.curselection()
        if not selection:
            self.set_error("Selecione uma marcação para continuar.")
            return
        self.result = self.options[selection[0]][0]
        self.close()


class SemanticDialog(OverlayPanel):
    def __init__(self, app, initial=None):
        super().__init__(
            app, "Marcação semântica",
            "Defina o papel narrativo e os metadados do trecho selecionado.",
            width=720, height=640, scrollable=True
        )
        self.initial = initial or {}
        self.result = None

        top = ttk.Frame(self.body)
        top.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Label(top, text="Função textual:", width=24).pack(side="left")
        self.role_var = tk.StringVar()
        roles = list(app.schema.get("roles", {}).keys())
        self.role_combo = ttk.Combobox(top, textvariable=self.role_var, values=roles, state="readonly")
        self.role_combo.pack(side="left", fill="x", expand=True)

        self.fields_frame = ttk.Frame(self.body)
        self.fields_frame.pack(fill="both", expand=True)
        self.fields = {}

        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Aplicar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))

        role = self.initial.get("data-role") or (roles[0] if roles else "")
        self.role_var.set(role)
        self.role_combo.bind("<<ComboboxSelected>>", lambda e: self.build_fields())
        self.build_fields()
        self.wait_result()

    def build_fields(self):
        for child in self.fields_frame.winfo_children():
            child.destroy()
        self.fields = {}

        role = self.role_var.get()
        role_spec = self.app.schema.get("roles", {}).get(role, {})
        attrs = role_spec.get("attributes", {})

        for name, spec in attrs.items():
            if spec.get("kind") == "const":
                continue
            editor = FieldEditor(
                self.fields_frame,
                self.app,
                name,
                spec,
                self.initial.get(name)
            )
            self.fields[name] = editor

    def accept(self):
        role = self.role_var.get()
        if role not in self.app.schema.get("roles", {}):
            self.set_error("Selecione uma função textual.")
            return

        attrs = {"data-role": role}
        role_spec = self.app.schema["roles"][role]
        for name, spec in role_spec.get("attributes", {}).items():
            if spec.get("kind") == "const":
                value = spec.get("value", "")
            else:
                value = self.fields[name].get()

            if spec.get("required") and not value:
                self.set_error(f'O campo "{name}" é obrigatório.')
                return
            if value:
                attrs[name] = value

        self.result = attrs
        self.close()


class SectionDialog(OverlayPanel):
    def __init__(self, app, initial=None, title="Seção e ponto de vista"):
        self.initial = dict(initial or app.section_meta)
        super().__init__(
            app, title,
            "Configure os metadados da seção HTML. Seções internas podem representar cenas.",
            width=720, height=640, scrollable=True
        )
        self.result = None

        id_frame = ttk.Frame(self.body)
        id_frame.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(id_frame, text="id", width=24).pack(side="left")
        self.id_var = tk.StringVar(value=self.initial.get("id", ""))
        ttk.Entry(id_frame, textvariable=self.id_var).pack(side="left", fill="x", expand=True)

        self.fields = {}
        attrs = app.schema.get("section", {}).get("attributes", {})
        for name, spec in attrs.items():
            self.fields[name] = FieldEditor(
                self.body, app, name, spec, self.initial.get(name)
            )

        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Salvar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))

        self.wait_result()

    def accept(self):
        result = {}
        for name, spec in self.app.schema["section"]["attributes"].items():
            value = self.fields[name].get()
            if spec.get("required") and not value:
                self.set_error(f'O campo "{name}" é obrigatório.')
                return
            if value:
                result[name] = value

        scope = result.get("data-scope", "scene")
        section_id = self.id_var.get().strip()
        if not section_id:
            section_id = self.app.next_section_id(scope)
        result["id"] = section_id
        self.result = result
        self.close()


class SectionManager(OverlayPanel):
    """Gerencia a seção principal e subseções vinculadas a trechos do texto."""

    ROOT = "__root__"

    def __init__(self, app):
        self.captured_selection = app.normalized_section_selection()
        super().__init__(
            app, "Estrutura de seções",
            "A seção principal envolve o capítulo inteiro. Para criar uma cena, selecione antes o trecho no editor e use “Adicionar da seleção”.",
            width=820, height=620
        )
        self.listbox = tk.Listbox(
            self.body, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _event: self.edit())

        selection_text = "Seleção capturada e pronta para uma nova seção."
        if not self.captured_selection:
            selection_text = "Nenhum trecho foi selecionado antes de abrir este painel."
        self.selection_var = tk.StringVar(value=selection_text)
        ttk.Label(
            self.body, textvariable=self.selection_var, style="Muted.TLabel", anchor="w"
        ).pack(fill="x", pady=(8, 0))

        ttk.Button(self.footer, text="Adicionar da seleção", style="Accent.TButton", command=self.add).pack(side="left")
        ttk.Button(self.footer, text="Editar", command=self.edit).pack(side="left", padx=6)
        ttk.Button(self.footer, text="Excluir", style="Danger.TButton", command=self.delete).pack(side="left")
        ttk.Button(self.footer, text="Fechar", command=self.close).pack(side="right")
        self.refresh()
        self.wait_result()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.keys = [self.ROOT]
        root_scope = self.app.section_meta.get("data-scope", "chapter")
        self.listbox.insert(
            "end", f'▾ Principal — {self.app.section_meta.get("id", "sem id")} [{root_scope}]'
        )
        for tag in self.app.sorted_subsection_tags():
            section = self.app.subsections[tag]
            start, end = self.app.section_offsets(tag)
            depth = self.app.section_depth(tag)
            start_line = self.app.offset_to_index(start).split(".")[0]
            end_line = self.app.offset_to_index(end).split(".")[0]
            scope = section.get("meta", {}).get("data-scope", "scene")
            prefix = "    " * depth + "└─ "
            self.keys.append(tag)
            self.listbox.insert(
                "end", f'{prefix}{section["id"]} [{scope}] — linhas {start_line}–{end_line}'
            )

    def selected_key(self):
        selected = self.listbox.curselection()
        return self.keys[selected[0]] if selected else None

    def add(self):
        if not self.captured_selection:
            self.set_error("Selecione no editor os parágrafos da nova seção antes de abrir este painel.")
            return
        initial = self.app.default_section_meta(include_id=False)
        initial["data-scope"] = "scene"
        dialog = SectionDialog(self.app, initial=initial, title="Nova seção interna")
        if not dialog.result:
            return
        error = self.app.add_subsection(*self.captured_selection, dialog.result)
        if error:
            self.set_error(error)
            return
        self.captured_selection = None
        self.selection_var.set("Seção criada. Feche o painel e selecione outro trecho para adicionar mais uma.")
        self.refresh()

    def edit(self):
        key = self.selected_key()
        if not key:
            self.set_error("Selecione uma seção para editar.")
            return
        if key == self.ROOT:
            dialog = SectionDialog(self.app, initial=self.app.section_meta, title="Seção principal do capítulo")
            if not dialog.result:
                return
            error = self.app.update_section_meta(None, dialog.result)
        else:
            dialog = SectionDialog(
                self.app, initial=self.app.subsections[key]["meta"], title="Editar seção interna"
            )
            if not dialog.result:
                return
            error = self.app.update_section_meta(key, dialog.result)
        if error:
            self.set_error(error)
            return
        self.refresh()

    def delete(self):
        key = self.selected_key()
        if not key:
            self.set_error("Selecione uma seção para excluir.")
            return
        if key == self.ROOT:
            self.set_error("A seção principal não pode ser excluída; apenas editada.")
            return
        section_id = self.app.subsections[key]["id"]
        if not self.app.ask_confirmation(
            "Excluir seção", f'Excluir a seção "{section_id}"? O texto dentro dela será preservado.',
            destructive=True
        ):
            return
        self.app.delete_subsection(key)
        self.refresh()


class ListManager(OverlayPanel):
    """Gerencia as listas estruturais aplicadas aos parágrafos do editor."""

    def __init__(self, app):
        super().__init__(
            app, "Listas do documento",
            "Cada linha não vazia do intervalo vira um item <li>. Linhas vazias interrompem o agrupamento.",
            width=760, height=540
        )
        self.listbox = tk.Listbox(
            self.body, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)
        ttk.Button(self.footer, text="Converter em UL", command=lambda: self.convert("ul")).pack(side="left")
        ttk.Button(self.footer, text="Converter em OL", command=lambda: self.convert("ol")).pack(side="left", padx=6)
        ttk.Button(self.footer, text="Remover lista", style="Danger.TButton", command=self.delete).pack(side="left")
        ttk.Button(self.footer, text="Fechar", command=self.close).pack(side="right")
        self.refresh()
        self.wait_result()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.tags = self.app.sorted_list_tags()
        for tag in self.tags:
            item = self.app.lists[tag]
            start, end = self.app.list_offsets(tag)
            start_line = self.app.offset_to_index(start).split(".")[0]
            end_line = self.app.offset_to_index(end).split(".")[0]
            label = "Marcadores <ul>" if item["type"] == "ul" else "Numerada <ol>"
            self.listbox.insert(
                "end", f'{label} — {item["id"]} — linhas {start_line}–{end_line}'
            )

    def selected_tag(self):
        selected = self.listbox.curselection()
        return self.tags[selected[0]] if selected else None

    def convert(self, list_type):
        tag = self.selected_tag()
        if not tag:
            self.set_error("Selecione uma lista para converter.")
            return
        self.app.set_list_type(tag, list_type)
        self.refresh()

    def delete(self):
        tag = self.selected_tag()
        if not tag:
            self.set_error("Selecione uma lista para remover.")
            return
        list_id = self.app.lists[tag]["id"]
        if not self.app.ask_confirmation(
            "Remover lista",
            f'Remover a estrutura da lista "{list_id}"? O texto dos itens será preservado.',
            destructive=True
        ):
            return
        self.app.delete_list(tag)
        self.refresh()


class InlineStructureDialog(OverlayPanel):
    def __init__(self, app, element="span", attrs=None, title="Elemento inline"):
        self.initial_attrs = dict(attrs or {})
        super().__init__(
            app, title,
            "O elemento envolve exatamente o trecho selecionado e pode coexistir com outras marcações.",
            width=680, height=520, scrollable=True
        )
        row = ttk.Frame(self.body)
        row.pack(fill="x", pady=(0, 12))
        ttk.Label(row, text="Elemento", width=20).pack(side="left")
        self.element_var = tk.StringVar(value=element if element in INLINE_ELEMENTS else "span")
        self.element_combo = ttk.Combobox(
            row, textvariable=self.element_var, values=list(INLINE_ELEMENTS), state="readonly"
        )
        self.element_combo.pack(side="left", fill="x", expand=True)
        self.element_combo.bind("<<ComboboxSelected>>", lambda _event: self.build_fields())

        self.help_var = tk.StringVar()
        ttk.Label(self.body, textvariable=self.help_var, style="Muted.TLabel", anchor="w").pack(fill="x", pady=(0, 10))
        self.fields_frame = ttk.Frame(self.body)
        self.fields_frame.pack(fill="x")
        self.attr_vars = {}
        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Aplicar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))
        self.build_fields()
        self.wait_result()

    def build_fields(self):
        previous = {name: var.get() for name, var in self.attr_vars.items()}
        for child in self.fields_frame.winfo_children():
            child.destroy()
        self.attr_vars = {}
        element = self.element_var.get()
        spec = INLINE_ELEMENTS[element]
        self.help_var.set(spec["label"])
        for name in spec["attrs"]:
            row = ttk.Frame(self.fields_frame)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=name, width=20).pack(side="left")
            value = previous.get(name, self.initial_attrs.get(name, ""))
            var = tk.StringVar(value=value)
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            self.attr_vars[name] = var

    def accept(self):
        attrs = {
            name: var.get().strip() for name, var in self.attr_vars.items() if var.get().strip()
        }
        self.result = {"element": self.element_var.get(), "attrs": attrs}
        self.close()


class InlineStructureManager(OverlayPanel):
    def __init__(self, app):
        super().__init__(
            app, "Elementos inline",
            "Edite ou remova as estruturas HTML aplicadas aos trechos do documento.",
            width=820, height=590
        )
        self.listbox = tk.Listbox(
            self.body, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _event: self.edit())
        ttk.Button(self.footer, text="Editar", command=self.edit).pack(side="left")
        ttk.Button(self.footer, text="Remover", style="Danger.TButton", command=self.delete).pack(side="left", padx=6)
        ttk.Button(self.footer, text="Fechar", command=self.close).pack(side="right")
        self.refresh()
        self.wait_result()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.tags = self.app.sorted_inline_tags()
        full_text = self.app.text.get("1.0", "end-1c")
        for tag in self.tags:
            item = self.app.inline_structures[tag]
            start, end = self.app.inline_offsets(tag)
            excerpt = " ".join(full_text[start:end].split())
            if len(excerpt) > 58:
                excerpt = excerpt[:55] + "..."
            self.listbox.insert(
                "end", f'<{item["element"]}>  {item["id"]}  —  {excerpt or "(vazio)"}'
            )

    def selected_tag(self):
        selected = self.listbox.curselection()
        return self.tags[selected[0]] if selected else None

    def edit(self):
        tag = self.selected_tag()
        if not tag:
            self.set_error("Selecione um elemento inline para editar.")
            return
        item = self.app.inline_structures[tag]
        dialog = InlineStructureDialog(
            self.app, item["element"], item.get("attrs", {}), title="Editar elemento inline"
        )
        if not dialog.result:
            return
        self.app.update_inline_structure(tag, dialog.result)
        self.refresh()

    def delete(self):
        tag = self.selected_tag()
        if not tag:
            self.set_error("Selecione um elemento inline para remover.")
            return
        item = self.app.inline_structures[tag]
        if not self.app.ask_confirmation(
            "Remover elemento inline",
            f'Remover <{item["element"]}> de "{item["id"]}"? O texto será preservado.',
            destructive=True
        ):
            return
        self.app.delete_inline_structure(tag)
        self.refresh()


class HorizontalRuleManager(OverlayPanel):
    def __init__(self, app):
        super().__init__(
            app, "Separadores horizontais",
            "Cada separador ocupa uma linha estrutural e é exportado como <hr>.",
            width=680, height=480
        )
        self.listbox = tk.Listbox(
            self.body, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)
        ttk.Button(self.footer, text="Remover", style="Danger.TButton", command=self.delete).pack(side="left")
        ttk.Button(self.footer, text="Fechar", command=self.close).pack(side="right")
        self.refresh()
        self.wait_result()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.marks = self.app.sorted_hr_marks()
        for mark in self.marks:
            item = self.app.horizontal_rules[mark]
            line = self.app.text.index(mark).split(".")[0]
            self.listbox.insert("end", f'<hr>  {item["id"]} — linha {line}')

    def selected_mark(self):
        selected = self.listbox.curselection()
        return self.marks[selected[0]] if selected else None

    def delete(self):
        mark = self.selected_mark()
        if not mark:
            self.set_error("Selecione um separador para remover.")
            return
        self.app.delete_hr(mark)
        self.refresh()


class EntityDialog(OverlayPanel):
    def __init__(self, parent, app, entity=None):
        super().__init__(
            app, "Entidade narrativa",
            "Cadastre um elemento reutilizável para relacioná-lo às marcações.",
            width=600, height=360
        )
        self.entity = entity or {}
        self.result = None

        body = self.body

        ttk.Label(body, text="Nome").grid(row=0, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar(value=self.entity.get("name", ""))
        ttk.Entry(body, textvariable=self.name_var, width=42).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(body, text="Tipo").grid(row=1, column=0, sticky="w", pady=4)
        types = list(app.schema.get("entity_types", []))
        current_type = self.entity.get("type", "")
        if current_type and current_type not in types:
            types.append(current_type)
        self.type_var = tk.StringVar(value=current_type or (types[0] if types else ""))
        ttk.Combobox(body, textvariable=self.type_var, values=types, state="readonly").grid(
            row=1, column=1, sticky="ew", pady=4
        )
        body.columnconfigure(1, weight=1)

        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Salvar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))

        self.wait_result()

    def accept(self):
        name = self.name_var.get().strip()
        etype = self.type_var.get().strip()
        if not name or not etype:
            self.set_error("Nome e tipo são obrigatórios.")
            return
        self.result = {"name": name, "type": etype}
        self.close()


class EntityManager(OverlayPanel):
    def __init__(self, app):
        super().__init__(
            app, "Entidades",
            "Personagens, locais, objetos e outros elementos referenciáveis no texto.",
            width=780, height=560
        )

        main = self.body

        self.listbox = tk.Listbox(
            main, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Adicionar", command=self.add).pack(side="left")
        ttk.Button(buttons, text="Editar", command=self.edit).pack(side="left", padx=6)
        ttk.Button(buttons, text="Excluir", command=self.delete).pack(side="left")
        ttk.Button(buttons, text="Fechar", command=self.close).pack(side="right")

        self.refresh()
        self.wait_result()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.ids = []
        for entity in sorted(
            self.app.entities.values(),
            key=lambda e: (e.get("type", ""), e.get("name", "").lower())
        ):
            self.ids.append(entity["id"])
            self.listbox.insert(
                "end",
                f'{entity["name"]}   [{entity["type"]}]   {entity["id"]}'
            )

    def selected_id(self):
        sel = self.listbox.curselection()
        return self.ids[sel[0]] if sel else None

    def add(self):
        dlg = EntityDialog(self, self.app)
        if not dlg.result:
            return
        entity_id = self.app.next_entity_id(dlg.result["type"])
        self.app.entities[entity_id] = {
            "id": entity_id,
            "name": dlg.result["name"],
            "type": dlg.result["type"]
        }
        self.app.dirty = True
        self.app.update_status()
        self.refresh()

    def edit(self):
        old_id = self.selected_id()
        if not old_id:
            return
        entity = dict(self.app.entities[old_id])
        dlg = EntityDialog(self, self.app, entity)
        if not dlg.result:
            return

        new_type = dlg.result["type"]
        new_id = old_id
        if new_type != entity["type"]:
            new_id = self.app.change_entity_type(old_id, new_type)

        self.app.entities[new_id]["name"] = dlg.result["name"]
        self.app.dirty = True
        self.app.update_status()
        self.refresh()

    def delete(self):
        entity_id = self.selected_id()
        if not entity_id:
            return
        entity = self.app.entities[entity_id]
        if not self.app.ask_confirmation(
            "Excluir entidade",
            f'Excluir "{entity["name"]}"?\n\nAs referências a esta entidade serão removidas.',
            destructive=True
        ):
            return
        self.app.remove_entity_references(entity_id)
        del self.app.entities[entity_id]
        self.app.dirty = True
        self.app.update_status()
        self.refresh()


class ChapterElementDialog(OverlayPanel):
    """Editor dos elementos especiais de capítulo."""

    def __init__(self, app, element_key, initial=""):
        self.element_key = element_key
        self.confirmed = False
        self.result = None

        labels = {
            "anteriormente": ("Anteriormente", "Texto exibido antes do conteúdo principal do capítulo."),
            "previa": ("Prévia", "Texto exibido ao final como prévia do próximo capítulo."),
        }
        title, help_text = labels[element_key]
        super().__init__(app, title, help_text, width=820, height=680)

        body = self.body

        text_frame = ttk.Frame(body)
        text_frame.pack(fill="both", expand=True)
        self.editor = tk.Text(text_frame, wrap="word", undo=True, padx=12, pady=10)
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.editor.yview)
        self.editor.configure(yscrollcommand=scroll.set)
        self.editor.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.editor.insert("1.0", initial or "")

        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Salvar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))
        ttk.Button(self.footer, text="Remover elemento", style="Danger.TButton", command=self.remove).pack(side="left")

        self.editor.focus_set()
        self.wait_result()

    def accept(self):
        self.result = self.editor.get("1.0", "end-1c").strip()
        self.confirmed = True
        self.close()

    def remove(self):
        self.result = ""
        self.confirmed = True
        self.close()


class GlossaryEntryDialog(OverlayPanel):
    def __init__(self, parent, term="", definition=""):
        app = parent.app if isinstance(parent, OverlayPanel) else parent
        super().__init__(
            app, "Entrada do glossário",
            "O termo será reconhecido no HTML e exibirá sua definição ao leitor.",
            width=760, height=680
        )
        self.result = None

        body = self.body
        body.columnconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)

        ttk.Label(body, text="Termo").grid(row=0, column=0, sticky="w")
        self.term_var = tk.StringVar(value=term)
        term_entry = ttk.Entry(body, textvariable=self.term_var)
        term_entry.grid(row=1, column=0, sticky="ew", pady=(3, 12))

        ttk.Label(body, text="Definição").grid(row=2, column=0, sticky="w")
        text_frame = ttk.Frame(body)
        text_frame.grid(row=3, column=0, sticky="nsew", pady=(3, 0))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.definition_editor = tk.Text(
            text_frame, wrap="word", height=8, padx=12, pady=10,
            borderwidth=0, highlightthickness=1,
            highlightbackground=COLORS["border"], highlightcolor=COLORS["primary"]
        )
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.definition_editor.yview)
        self.definition_editor.configure(yscrollcommand=scroll.set)
        self.definition_editor.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.definition_editor.insert("1.0", definition or "")

        ttk.Button(self.footer, text="Cancelar", command=self.close).pack(side="right")
        ttk.Button(self.footer, text="Salvar", style="Accent.TButton", command=self.accept).pack(side="right", padx=(0, 8))
        term_entry.focus_set()
        self.wait_result()

    def accept(self):
        term = self.term_var.get().strip()
        definition = self.definition_editor.get("1.0", "end-1c").strip()
        if not term or not definition:
            self.set_error("Termo e definição são obrigatórios.")
            return
        self.result = (term, definition)
        self.close()


class GlossaryManager(OverlayPanel):
    def __init__(self, app):
        super().__init__(
            app, "Glossário",
            "Termos cadastrados são reconhecidos no texto exportado e recebem uma definição interativa.",
            width=820, height=590
        )

        body = self.body

        self.listbox = tk.Listbox(
            body, exportselection=False, bg=COLORS["surface_alt"], fg=COLORS["text"],
            selectbackground=COLORS["primary"], selectforeground="#FFFFFF",
            highlightbackground=COLORS["border"], highlightthickness=1,
            borderwidth=0, activestyle="none", font=("TkDefaultFont", 10)
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _e: self.edit())

        buttons = ttk.Frame(self.footer)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Adicionar", command=self.add).pack(side="left")
        ttk.Button(buttons, text="Editar", command=self.edit).pack(side="left", padx=6)
        ttk.Button(buttons, text="Excluir", command=self.delete).pack(side="left")
        ttk.Button(buttons, text="Fechar", command=self.close).pack(side="right")

        self.refresh()
        self.wait_result()

    def refresh(self):
        self.listbox.delete(0, "end")
        self.terms = sorted(self.app.glossary, key=str.casefold)
        for term in self.terms:
            definition = " ".join(self.app.glossary[term].split())
            if len(definition) > 90:
                definition = definition[:87] + "..."
            self.listbox.insert("end", f"{term} — {definition}")

    def selected_term(self):
        selection = self.listbox.curselection()
        return self.terms[selection[0]] if selection else None

    def add(self):
        dlg = GlossaryEntryDialog(self)
        if not dlg.result:
            return
        term, definition = dlg.result
        if term in self.app.glossary:
            self.set_error(f'O termo "{term}" já existe.')
            return
        self.app.glossary[term] = definition
        self.app.dirty = True
        self.app.update_status()
        self.refresh()

    def edit(self):
        old_term = self.selected_term()
        if not old_term:
            return
        dlg = GlossaryEntryDialog(self, old_term, self.app.glossary.get(old_term, ""))
        if not dlg.result:
            return
        term, definition = dlg.result
        if term != old_term and term in self.app.glossary:
            self.set_error(f'O termo "{term}" já existe.')
            return
        if term != old_term:
            del self.app.glossary[old_term]
        self.app.glossary[term] = definition
        self.app.dirty = True
        self.app.update_status()
        self.refresh()

    def delete(self):
        term = self.selected_term()
        if not term:
            return
        if not self.app.ask_confirmation(
            "Excluir termo", f'Excluir o termo "{term}"?', destructive=True
        ):
            return
        del self.app.glossary[term]
        self.app.dirty = True
        self.app.update_status()
        self.refresh()


class SemanticEditor(tk.Tk):
    SEM_PREFIX = "sem::"
    SECTION_PREFIX = "section::"
    LIST_PREFIX = "list::"
    INLINE_PREFIX = "inline::"
    HR_PREFIX = "hr::"
    HR_STYLE_PREFIX = "hr-style::"

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x820")
        self.minsize(980, 650)
        self.configure(bg=COLORS["app_bg"])
        self.overlay_stack = []
        self._metrics_job = None
        self._initialization_failed = False
        self.configure_styles()

        schema_candidates = [script_dir() / "schema.json", script_dir() / "schema(1).json"]
        self.schema_path = next((path for path in schema_candidates if path.exists()), schema_candidates[0])
        try:
            self.schema = load_schema(self.schema_path)
        except Exception as exc:
            self._initialization_failed = True
            tk.Label(
                self, text="Não foi possível iniciar o editor.", bg=COLORS["app_bg"],
                fg=COLORS["danger"], font=("TkDefaultFont", 14, "bold")
            ).pack(expand=True)
            self.after_idle(
                lambda: self.notify("Schema", f"Não foi possível abrir schema.json:\n{exc}", "error")
            )
            return

        self.project_path = None
        self.dirty = False
        self.entities = {}
        self.marks = {}
        self.chapter_elements = {"anteriormente": "", "previa": ""}
        self.glossary = {}
        self.section_meta = self.default_section_meta(scope="chapter")
        self.subsections = {}
        self.lists = {}
        self.inline_structures = {}
        self.horizontal_rules = {}
        self.tags_visible = tk.BooleanVar(self, True)

        self.build_ui()
        self.configure_text_tags()
        self.bind_shortcuts()
        self.update_status()
        self.update_document_metrics()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- UI ----------

    def configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("TkDefaultFont", 9), foreground=COLORS["text"])
        style.configure("TFrame", background=COLORS["surface"])
        style.configure("App.TFrame", background=COLORS["app_bg"])
        style.configure("Panel.TFrame", background=COLORS["surface"])
        style.configure("TLabel", background=COLORS["surface"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"])
        style.configure("Section.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("TkDefaultFont", 8, "bold"))
        style.configure("TButton", padding=(11, 8), relief="flat", background="#F2F4F7", borderwidth=0)
        style.map("TButton", background=[("active", "#E7EAF0"), ("pressed", "#DDE1E8")])
        style.configure("Accent.TButton", background=COLORS["primary"], foreground="#FFFFFF", font=("TkDefaultFont", 9, "bold"))
        style.map("Accent.TButton", background=[("active", COLORS["primary_hover"]), ("pressed", "#3F3FAF")])
        style.configure("Danger.TButton", background="#FFF1F2", foreground=COLORS["danger"])
        style.map("Danger.TButton", background=[("active", "#FFE4E6")])
        style.configure("Ghost.TButton", background=COLORS["surface"], foreground=COLORS["muted"], padding=(8, 6))
        style.map("Ghost.TButton", background=[("active", COLORS["surface_alt"])])
        style.configure("Header.TButton", background="#253149", foreground="#FFFFFF", padding=(12, 8))
        style.map("Header.TButton", background=[("active", "#34425E")])
        style.configure("Tool.TButton", background=COLORS["surface"], padding=(9, 7))
        style.map("Tool.TButton", background=[("active", COLORS["surface_alt"]), ("pressed", "#E8ECF3")])
        style.configure("Toggle.Toolbutton", background=COLORS["surface_alt"], foreground=COLORS["text"], padding=(12, 7), indicatorcolor=COLORS["primary"])
        style.map("Toggle.Toolbutton", background=[("selected", "#E8E8FF"), ("active", "#EEEFFC")], foreground=[("selected", COLORS["primary"])])
        style.configure("TEntry", fieldbackground="#FFFFFF", padding=7, bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"])
        style.configure("TCombobox", fieldbackground="#FFFFFF", padding=6)
        style.configure("Vertical.TScrollbar", background="#CBD3DF", troughcolor=COLORS["surface_alt"], borderwidth=0, arrowsize=12)

    def build_ui(self):
        self.build_menu()

        header = tk.Frame(self, bg=COLORS["header"], height=72, padx=22, pady=13)
        header.pack(fill="x")
        header.pack_propagate(False)
        logo = tk.Label(
            header, text="S", bg=COLORS["primary"], fg="#FFFFFF",
            font=("TkDefaultFont", 15, "bold"), width=2, pady=5
        )
        logo.pack(side="left", padx=(0, 12))
        identity = tk.Frame(header, bg=COLORS["header"])
        identity.pack(side="left", fill="y")
        tk.Label(
            identity, text=APP_TITLE, bg=COLORS["header"], fg="#FFFFFF",
            font=("TkDefaultFont", 13, "bold"), anchor="w"
        ).pack(anchor="w")
        self.project_name_var = tk.StringVar(value="Projeto sem título")
        tk.Label(
            identity, textvariable=self.project_name_var, bg=COLORS["header"],
            fg=COLORS["header_muted"], font=("TkDefaultFont", 9), anchor="w"
        ).pack(anchor="w", pady=(3, 0))
        ttk.Button(header, text="Exportar HTML", style="Accent.TButton", command=self.export_html).pack(side="right")
        ttk.Button(header, text="Salvar", style="Header.TButton", command=self.save_project).pack(side="right", padx=8)
        ttk.Button(header, text="Abrir", style="Header.TButton", command=self.open_project).pack(side="right")

        toolbar = tk.Frame(
            self, bg=COLORS["surface"], height=50,
            highlightbackground=COLORS["border"], highlightthickness=1, padx=16, pady=7
        )
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        ttk.Button(toolbar, text="B", width=3, style="Tool.TButton", command=lambda: self.toggle_format("fmt_bold")).pack(side="left")
        ttk.Button(toolbar, text="I", width=3, style="Tool.TButton", command=lambda: self.toggle_format("fmt_italic")).pack(side="left", padx=3)
        ttk.Button(toolbar, text="U", width=3, style="Tool.TButton", command=lambda: self.toggle_format("fmt_underline")).pack(side="left")
        ttk.Button(toolbar, text="• Lista", style="Tool.TButton", command=lambda: self.apply_list("ul")).pack(side="left", padx=(10, 3))
        ttk.Button(toolbar, text="1. Lista", style="Tool.TButton", command=lambda: self.apply_list("ol")).pack(side="left")
        inline_button = ttk.Menubutton(toolbar, text="Inline", style="Tool.TButton")
        inline_menu = tk.Menu(inline_button, tearoff=False)
        for element, spec in INLINE_ELEMENTS.items():
            inline_menu.add_command(
                label=spec["label"], command=lambda selected=element: self.apply_inline_structure(selected)
            )
        inline_menu.add_separator()
        inline_menu.add_command(label="Gerenciar elementos...", command=self.open_inline_manager)
        inline_button["menu"] = inline_menu
        inline_button.pack(side="left", padx=(10, 3))
        ttk.Button(toolbar, text="HR", style="Tool.TButton", command=self.insert_hr).pack(side="left")
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(toolbar, text="Marcar seleção", style="Tool.TButton", command=self.mark_selection).pack(side="left")
        ttk.Button(toolbar, text="Editar marca", style="Tool.TButton", command=self.edit_mark_at_cursor).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Remover marca", style="Tool.TButton", command=self.remove_mark_at_cursor).pack(side="left")
        self.tags_toggle = ttk.Checkbutton(
            toolbar, text="Perceber tags", variable=self.tags_visible,
            command=self.toggle_tag_visibility, style="Toggle.Toolbutton"
        )
        self.tags_toggle.pack(side="right")

        workspace = tk.Frame(self, bg=COLORS["app_bg"], padx=14, pady=14)
        workspace.pack(fill="both", expand=True)
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        left_card = tk.Frame(
            workspace, bg=COLORS["surface"], width=218,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_card.grid_propagate(False)
        left_scroll = ScrollableFrame(left_card)
        left_scroll.pack(fill="both", expand=True)
        left = ttk.Frame(left_scroll.content, padding=(14, 16))
        left.pack(fill="both", expand=True)
        self._build_action_group(left, "PROJETO", [
            ("Novo projeto", self.new_project),
            ("Abrir projeto", self.open_project),
            ("Salvar como", self.save_project_as),
        ])
        self._build_action_group(left, "SEMÂNTICA", [
            ("Marcar seleção", self.mark_selection),
            ("Editar marca", self.edit_mark_at_cursor),
            ("Remover marca", self.remove_mark_at_cursor),
            ("Entidades", lambda: EntityManager(self)),
            ("Seções e POV", self.edit_section),
        ])
        self._build_action_group(left, "CONTEÚDO", [
            ("Lista com marcadores", lambda: self.apply_list("ul")),
            ("Lista numerada", lambda: self.apply_list("ol")),
            ("Gerenciar listas", self.open_list_manager),
            ("Elementos inline", self.open_inline_manager),
            ("Inserir separador HR", self.insert_hr),
            ("Anteriormente", lambda: self.edit_chapter_element("anteriormente")),
            ("Prévia", lambda: self.edit_chapter_element("previa")),
            ("Glossário", self.open_glossary),
        ])

        editor_card = tk.Frame(
            workspace, bg=COLORS["surface"], highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        editor_card.grid(row=0, column=1, sticky="nsew")
        editor_heading = tk.Frame(editor_card, bg=COLORS["surface"], padx=22, pady=12)
        editor_heading.pack(fill="x")
        tk.Label(
            editor_heading, text="DOCUMENTO", bg=COLORS["surface"], fg=COLORS["muted"],
            font=("TkDefaultFont", 8, "bold")
        ).pack(side="left")
        self.editor_hint_var = tk.StringVar(value="Escreva e selecione trechos para aplicar semântica")
        tk.Label(
            editor_heading, textvariable=self.editor_hint_var, bg=COLORS["surface"],
            fg=COLORS["muted"], font=("TkDefaultFont", 8)
        ).pack(side="right")
        ttk.Separator(editor_card).pack(fill="x")
        editor_frame = tk.Frame(editor_card, bg=COLORS["editor"], padx=10, pady=6)
        editor_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            editor_frame,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1, padx=36, pady=28, bg=COLORS["editor"], fg=COLORS["text"],
            insertbackground=COLORS["primary"], selectbackground="#CFCFFC",
            selectforeground=COLORS["text"], borderwidth=0, highlightthickness=0,
            spacing1=3, spacing2=2, spacing3=9, font=("DejaVu Serif", 12)
        )
        yscroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=yscroll.set)

        self.text.pack(side="left", fill="both", expand=True, padx=(0, 4))
        yscroll.pack(side="right", fill="y")

        right = tk.Frame(
            workspace, bg=COLORS["surface"], width=278,
            highlightbackground=COLORS["border"], highlightthickness=1, padx=14, pady=16
        )
        right.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        right.grid_propagate(False)
        tk.Label(
            right, text="LEITURA DO DOCUMENTO", bg=COLORS["surface"], fg=COLORS["muted"],
            font=("TkDefaultFont", 8, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 10))
        metrics = tk.Frame(right, bg=COLORS["surface"])
        metrics.pack(fill="x")
        metrics.grid_columnconfigure(0, weight=1, uniform="metric")
        metrics.grid_columnconfigure(1, weight=1, uniform="metric")
        self.stats_vars = {
            "words": tk.StringVar(value="0"),
            "sentences": tk.StringVar(value="0"),
            "paragraphs": tk.StringVar(value="0"),
            "reading": tk.StringVar(value="0 min"),
            "chars_spaces": tk.StringVar(value="0"),
            "chars_no_spaces": tk.StringVar(value="0"),
        }
        cards = [
            ("Palavras", "words"), ("Frases", "sentences"),
            ("Parágrafos", "paragraphs"), ("Tempo de leitura", "reading"),
            ("Caracteres c/ espaço", "chars_spaces"), ("Caracteres s/ espaço", "chars_no_spaces"),
        ]
        for index, (label, key) in enumerate(cards):
            self._build_metric_card(metrics, index // 2, index % 2, label, self.stats_vars[key])
        tk.Label(
            right, text=f"Estimativa de leitura: {READING_WORDS_PER_MINUTE} palavras por minuto.",
            bg=COLORS["surface"], fg=COLORS["muted"], font=("TkDefaultFont", 7),
            anchor="w", justify="left", wraplength=238
        ).pack(fill="x", pady=(7, 0))

        ttk.Separator(right).pack(fill="x", pady=16)
        tk.Label(
            right, text="TAG NO CURSOR", bg=COLORS["surface"], fg=COLORS["muted"],
            font=("TkDefaultFont", 8, "bold"), anchor="w"
        ).pack(fill="x")
        self.tag_inspector_var = tk.StringVar(value="Nenhuma marcação no cursor.")
        tk.Label(
            right, textvariable=self.tag_inspector_var, bg=COLORS["surface_alt"],
            fg=COLORS["text"], justify="left", anchor="nw", wraplength=228,
            padx=12, pady=12, font=("TkDefaultFont", 9)
        ).pack(fill="x", pady=(8, 0))
        self.legend_frame = tk.Frame(right, bg=COLORS["surface"])
        self.legend_frame.pack(fill="x", pady=(14, 0))
        for label, color in (
            ("Narração", "#E8F0FF"), ("Descrição", "#EAF5E6"),
            ("Diálogo", "#FFF1D2"), ("Pensamento", "#F2E8FF")
        ):
            row = tk.Frame(self.legend_frame, bg=COLORS["surface"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text="  ", bg=color, width=2).pack(side="left", padx=(0, 8))
            tk.Label(row, text=label, bg=COLORS["surface"], fg=COLORS["muted"], anchor="w").pack(side="left")

        self.status_var = tk.StringVar()
        status = tk.Label(
            self, textvariable=self.status_var, anchor="w", bg="#E3E8F0", fg=COLORS["muted"],
            padx=16, pady=6, font=("TkDefaultFont", 8)
        )
        status.pack(fill="x")

        self.text.bind("<<Modified>>", self.on_text_modified)
        self.text.bind("<ButtonRelease-1>", lambda e: self.update_status())
        self.text.bind("<KeyRelease>", lambda e: self.update_status())

    def _build_action_group(self, parent, title, actions):
        tk.Label(
            parent, text=title, bg=COLORS["surface"], fg=COLORS["muted"],
            font=("TkDefaultFont", 8, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 7))
        for label, command in actions:
            ttk.Button(parent, text=label, command=command, style="Tool.TButton").pack(fill="x", pady=2)
        tk.Frame(parent, height=14, bg=COLORS["surface"]).pack()

    def _build_metric_card(self, parent, row, column, label, variable):
        card = tk.Frame(
            parent, bg=COLORS["surface_alt"], highlightbackground=COLORS["border"],
            highlightthickness=1, padx=9, pady=9
        )
        card.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 4, 4 if column == 0 else 0), pady=4)
        tk.Label(
            card, textvariable=variable, bg=COLORS["surface_alt"], fg=COLORS["text"],
            font=("TkDefaultFont", 13, "bold"), anchor="w"
        ).pack(fill="x")
        tk.Label(
            card, text=label, bg=COLORS["surface_alt"], fg=COLORS["muted"],
            font=("TkDefaultFont", 7), anchor="w", wraplength=100, justify="left"
        ).pack(fill="x", pady=(3, 0))

    def build_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Novo", accelerator="Ctrl+N", command=self.new_project)
        file_menu.add_command(label="Abrir projeto...", accelerator="Ctrl+O", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Salvar projeto", accelerator="Ctrl+S", command=self.save_project)
        file_menu.add_command(label="Salvar projeto como...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar HTML...", accelerator="Ctrl+Shift+S", command=self.export_html)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.on_close)
        menu.add_cascade(label="Arquivo", menu=file_menu)

        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Desfazer", accelerator="Ctrl+Z", command=lambda: self.safe_edit("undo"))
        edit_menu.add_command(label="Refazer", accelerator="Ctrl+Y", command=lambda: self.safe_edit("redo"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Marcar seleção...", accelerator="Ctrl+M", command=self.mark_selection)
        edit_menu.add_command(label="Editar marca no cursor...", command=self.edit_mark_at_cursor)
        edit_menu.add_command(label="Remover marca no cursor", command=self.remove_mark_at_cursor)
        menu.add_cascade(label="Editar", menu=edit_menu)

        data_menu = tk.Menu(menu, tearoff=False)
        data_menu.add_command(label="Entidades...", command=lambda: EntityManager(self))
        data_menu.add_command(label="Seções / POV...", command=self.edit_section)
        data_menu.add_command(label="Listas...", command=self.open_list_manager)
        data_menu.add_separator()
        data_menu.add_command(label="Recarregar schema.json", command=self.reload_schema)
        menu.add_cascade(label="Dados", menu=data_menu)

        structure_menu = tk.Menu(menu, tearoff=False)
        structure_menu.add_command(label="Lista com marcadores <ul>", command=lambda: self.apply_list("ul"))
        structure_menu.add_command(label="Lista numerada <ol>", command=lambda: self.apply_list("ol"))
        structure_menu.add_command(label="Gerenciar listas...", command=self.open_list_manager)
        structure_menu.add_separator()
        inline_structure_menu = tk.Menu(structure_menu, tearoff=False)
        for element, spec in INLINE_ELEMENTS.items():
            inline_structure_menu.add_command(
                label=spec["label"], command=lambda selected=element: self.apply_inline_structure(selected)
            )
        structure_menu.add_cascade(label="Elemento inline", menu=inline_structure_menu)
        structure_menu.add_command(label="Gerenciar elementos inline...", command=self.open_inline_manager)
        structure_menu.add_separator()
        structure_menu.add_command(label="Inserir <hr>", command=self.insert_hr)
        structure_menu.add_command(label="Gerenciar separadores...", command=self.open_hr_manager)
        structure_menu.add_separator()
        structure_menu.add_command(label="Seções...", command=self.edit_section)
        menu.add_cascade(label="Estrutura", menu=structure_menu)

        elements_menu = tk.Menu(menu, tearoff=False)
        elements_menu.add_command(label="Anteriormente...", command=lambda: self.edit_chapter_element("anteriormente"))
        elements_menu.add_command(label="Prévia...", command=lambda: self.edit_chapter_element("previa"))
        elements_menu.add_separator()
        elements_menu.add_command(label="Glossário...", command=self.open_glossary)
        menu.add_cascade(label="Elementos", menu=elements_menu)

    def _register_overlay(self, overlay):
        self.overlay_stack.append(overlay)
        overlay.lift()

    def _unregister_overlay(self, overlay):
        if overlay in self.overlay_stack:
            self.overlay_stack.remove(overlay)
        if self.overlay_stack:
            self.overlay_stack[-1].lift()

    def close_active_overlay(self):
        if self.overlay_stack:
            self.overlay_stack[-1].close()
            return "break"
        return None

    def notify(self, title, message, kind="info"):
        return MessageOverlay(self, title, message, kind=kind).result

    def ask_confirmation(self, title, message, destructive=False):
        confirm_style = "Danger.TButton" if destructive else "Accent.TButton"
        result = MessageOverlay(
            self, title, message, kind="warning",
            choices=[
                ("Cancelar", False, "TButton"),
                ("Excluir" if destructive else "Continuar", True, confirm_style),
            ]
        ).result
        return bool(result)

    def configure_text_tags(self):
        base_font = tkfont.Font(root=self, font=self.text.cget("font"))

        bold_font = base_font.copy()
        bold_font.configure(weight="bold")
        italic_font = base_font.copy()
        italic_font.configure(slant="italic")
        bold_italic_font = base_font.copy()
        bold_italic_font.configure(weight="bold", slant="italic")
        small_font = base_font.copy()
        base_size = abs(int(base_font.actual("size") or 12))
        small_font.configure(size=max(8, round(base_size * .78)))
        mono_font = tkfont.nametofont("TkFixedFont").copy()
        mono_font.configure(size=base_size)
        mono_italic_font = mono_font.copy()
        mono_italic_font.configure(slant="italic")

        self.fonts = {
            "base": base_font,
            "bold": bold_font,
            "italic": italic_font,
            "bold_italic": bold_italic_font,
            "small": small_font,
            "mono": mono_font,
            "mono_italic": mono_italic_font,
        }

        self.text.tag_configure("fmt_bold", font=bold_font)
        self.text.tag_configure("fmt_italic", font=italic_font)
        self.text.tag_configure("fmt_bold_italic", font=bold_italic_font)
        self.text.tag_configure("fmt_underline", underline=True)

        self.semantic_styles = {
            "narration": {"background": "#E8F0FF"},
            "description": {"background": "#EAF5E6"},
            "dialogue": {"background": "#FFF1D2"},
            "thought": {"background": "#F2E8FF"},
            "title": {"background": "#DDEBFF"},
            "subtitle": {"background": "#E7EEFF"},
            "epigraph": {"background": "#F0E8FF"},
            "quotation": {"background": "#F3E9FA"},
            "citation": {"background": "#EEEAF8"},
            "aside": {"background": "#E4F5F2"},
            "time_reference": {"background": "#FFF0D9"},
            "foreign_term": {"background": "#E1F4F7"},
            "marked_passage": {"background": "#FFF5B8"},
            "inserted_text": {"background": "#E3F7E8"},
            "deleted_text": {"background": "#FCE4E6"},
            "section_break": {"background": "#E9EDF3"},
        }

    def bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.new_project())
        self.bind_all("<Control-o>", lambda e: self.open_project())
        self.bind_all("<Control-s>", lambda e: self.save_project())
        self.bind_all("<Control-Shift-S>", lambda e: self.export_html())
        self.bind_all("<Control-b>", lambda e: self.toggle_format("fmt_bold"))
        self.bind_all("<Control-i>", lambda e: self.toggle_format("fmt_italic"))
        self.bind_all("<Control-u>", lambda e: self.toggle_format("fmt_underline"))
        self.bind_all("<Control-m>", lambda e: self.mark_selection())
        self.bind_all("<Escape>", lambda e: self.close_active_overlay())

    # ---------- Estado / IDs ----------

    def default_section_meta(self, include_id=True, scope=None):
        attrs = self.schema.get("section", {}).get("attributes", {})
        meta = {}
        for name, spec in attrs.items():
            if "default" in spec:
                meta[name] = spec["default"]
        meta.setdefault("data-scope", "scene")
        if scope:
            meta["data-scope"] = scope
        if include_id:
            meta["id"] = self.next_section_id(meta["data-scope"], existing=False)
        return meta

    def id_width(self):
        return int(self.schema.get("id_width", 9))

    def next_section_id(self, scope, existing=True):
        prefix = self.schema.get("section", {}).get("id_prefix_by_scope", {}).get(scope, scope)
        used = self.all_section_ids() if existing else set()
        n = 1
        while True:
            candidate = f"{prefix}-{n:0{self.id_width()}d}"
            if candidate not in used:
                return candidate
            n += 1

    def all_section_ids(self, excluding_tag=None):
        used = set()
        root = getattr(self, "section_meta", {})
        if root.get("id"):
            used.add(root["id"])
        for tag, section in getattr(self, "subsections", {}).items():
            if tag != excluding_tag and section.get("id"):
                used.add(section["id"])
        return used

    def next_section_tag(self):
        number = 1
        while f"{self.SECTION_PREFIX}{number}" in self.subsections:
            number += 1
        return f"{self.SECTION_PREFIX}{number}"

    def normalized_section_selection(self):
        selected = self.selection() if hasattr(self, "text") else None
        if not selected:
            return None
        start, end = selected
        if self.text.compare(end, ">", start) and end.split(".")[1] == "0":
            end = self.text.index(f"{end}-1c")
        start = self.text.index(f"{start} linestart")
        end = self.text.index(f"{end} lineend")
        start_offset = self.index_to_offset(start)
        end_offset = self.index_to_offset(end)
        if start_offset >= end_offset:
            return None
        return start_offset, end_offset

    def section_offsets(self, tag):
        ranges = self.tag_ranges_as_offsets(tag)
        return tuple(ranges[0]) if ranges else (0, 0)

    def sorted_subsection_tags(self):
        return sorted(
            self.subsections,
            key=lambda tag: (
                self.section_offsets(tag)[0],
                -self.section_offsets(tag)[1],
                self.subsections[tag].get("id", "")
            )
        )

    def section_depth(self, tag):
        start, end = self.section_offsets(tag)
        depth = 1
        for other in self.subsections:
            if other == tag:
                continue
            outer_start, outer_end = self.section_offsets(other)
            if outer_start <= start and outer_end >= end and (outer_start, outer_end) != (start, end):
                depth += 1
        return depth

    def section_parent_id(self, tag):
        start, end = self.section_offsets(tag)
        candidates = []
        for other, section in self.subsections.items():
            if other == tag:
                continue
            outer_start, outer_end = self.section_offsets(other)
            if outer_start <= start and outer_end >= end and (outer_start, outer_end) != (start, end):
                candidates.append((outer_end - outer_start, section["id"]))
        if candidates:
            return min(candidates)[1]
        return self.section_meta.get("id", "")

    def validate_subsection_range(self, start, end, excluding_tag=None):
        if start >= end:
            return "A seção precisa abranger ao menos um trecho de texto."
        for tag in self.subsections:
            if tag == excluding_tag:
                continue
            other_start, other_end = self.section_offsets(tag)
            if (start, end) == (other_start, other_end):
                return "Já existe uma seção abrangendo exatamente esse trecho."
            overlaps = start < other_end and end > other_start
            nested = (start <= other_start and end >= other_end) or (
                other_start <= start and other_end >= end
            )
            if overlaps and not nested:
                return (
                    "A seleção cruza parcialmente outra seção. Ajuste os limites para que as "
                    "seções fiquem separadas ou completamente aninhadas."
                )
        return None

    def add_subsection(self, start, end, meta):
        error = self.validate_subsection_range(start, end)
        if error:
            return error
        section_id = meta.get("id", "").strip()
        if not section_id:
            section_id = self.next_section_id(meta.get("data-scope", "scene"))
            meta["id"] = section_id
        if section_id in self.all_section_ids():
            return f'Já existe uma seção com o id "{section_id}".'
        tag = self.next_section_tag()
        self.subsections[tag] = {"id": section_id, "meta": dict(meta)}
        self.text.tag_add(tag, self.offset_to_index(start), self.offset_to_index(end))
        self.dirty = True
        self.update_status()
        return None

    def update_section_meta(self, tag, meta):
        section_id = meta.get("id", "").strip()
        if not section_id:
            section_id = self.next_section_id(meta.get("data-scope", "scene"))
            meta["id"] = section_id
        excluding = tag if tag is not None else "__root__"
        used = self.all_section_ids(excluding_tag=excluding)
        if tag is None:
            used.discard(self.section_meta.get("id"))
        if section_id in used:
            return f'Já existe uma seção com o id "{section_id}".'
        if tag is None:
            self.section_meta = dict(meta)
        else:
            self.subsections[tag]["id"] = section_id
            self.subsections[tag]["meta"] = dict(meta)
        self.dirty = True
        self.update_status()
        return None

    def delete_subsection(self, tag):
        self.text.tag_delete(tag)
        self.subsections.pop(tag, None)
        self.dirty = True
        self.update_status()

    def next_list_id(self):
        used = {item.get("id") for item in self.lists.values()}
        number = 1
        while True:
            candidate = f"list-{number:0{self.id_width()}d}"
            if candidate not in used:
                return candidate
            number += 1

    def next_list_tag(self):
        number = 1
        while f"{self.LIST_PREFIX}{number}" in self.lists:
            number += 1
        return f"{self.LIST_PREFIX}{number}"

    def list_offsets(self, tag):
        ranges = self.tag_ranges_as_offsets(tag)
        return tuple(ranges[0]) if ranges else (0, 0)

    def sorted_list_tags(self):
        return sorted(
            self.lists,
            key=lambda tag: (self.list_offsets(tag)[0], self.list_offsets(tag)[1])
        )

    def apply_list_style(self, tag, list_type):
        margin = 30 if list_type == "ol" else 24
        background = "#F6F7FF" if list_type == "ol" else "#F5FAF8"
        self.text.tag_configure(
            tag, lmargin1=margin, lmargin2=margin, spacing1=2, spacing3=2,
            background=background
        )
        self.text.tag_lower(tag)

    def apply_list(self, list_type):
        if list_type not in {"ul", "ol"}:
            return
        selected = self.normalized_section_selection()
        if not selected:
            self.notify(
                "Criar lista",
                "Selecione uma ou mais linhas. Cada linha não vazia será transformada em um item da lista."
            )
            return
        start, end = selected
        selected_text = self.text.get(self.offset_to_index(start), self.offset_to_index(end))
        if not any(line.strip() for line in selected_text.splitlines()):
            self.notify("Criar lista", "A seleção não contém nenhum item de texto.")
            return

        overlaps = []
        exact = None
        for tag in self.lists:
            other_start, other_end = self.list_offsets(tag)
            if (start, end) == (other_start, other_end):
                exact = tag
            elif start < other_end and end > other_start:
                overlaps.append(tag)
        if overlaps:
            self.notify(
                "Criar lista",
                "A seleção cruza parcialmente uma lista existente. Remova ou ajuste essa lista antes de continuar.",
                "warning"
            )
            return
        if exact:
            if self.lists[exact]["type"] == list_type:
                self.delete_list(exact)
            else:
                self.set_list_type(exact, list_type)
            return

        tag = self.next_list_tag()
        list_id = self.next_list_id()
        self.lists[tag] = {"id": list_id, "type": list_type}
        self.text.tag_add(tag, self.offset_to_index(start), self.offset_to_index(end))
        self.apply_list_style(tag, list_type)
        self.dirty = True
        self.update_status()

    def set_list_type(self, tag, list_type):
        if tag not in self.lists or list_type not in {"ul", "ol"}:
            return
        self.lists[tag]["type"] = list_type
        self.apply_list_style(tag, list_type)
        self.dirty = True
        self.update_status()

    def delete_list(self, tag):
        self.text.tag_delete(tag)
        self.lists.pop(tag, None)
        self.dirty = True
        self.update_status()

    def list_tag_for_range(self, start, end):
        if start >= end:
            return None
        for tag in self.sorted_list_tags():
            list_start, list_end = self.list_offsets(tag)
            if list_start <= start and list_end >= end:
                return tag
        return None

    def open_list_manager(self):
        ListManager(self)

    def next_inline_id(self):
        used = {item.get("id") for item in self.inline_structures.values()}
        number = 1
        while True:
            candidate = f"inline-{number:0{self.id_width()}d}"
            if candidate not in used:
                return candidate
            number += 1

    def next_inline_tag(self):
        number = 1
        while f"{self.INLINE_PREFIX}{number}" in self.inline_structures:
            number += 1
        return f"{self.INLINE_PREFIX}{number}"

    def inline_offsets(self, tag):
        ranges = self.tag_ranges_as_offsets(tag)
        return tuple(ranges[0]) if ranges else (0, 0)

    def sorted_inline_tags(self):
        return sorted(
            self.inline_structures,
            key=lambda tag: (
                self.inline_offsets(tag)[0], self.inline_offsets(tag)[1],
                self.inline_structures[tag].get("id", "")
            )
        )

    def apply_inline_style(self, tag, element):
        self.text.tag_configure(
            tag, font=self.fonts["base"], background="", foreground="",
            underline=False, overstrike=False, offset=0
        )
        styles = {
            "q": {"font": self.fonts["italic"], "background": "#F6F1FF"},
            "cite": {"font": self.fonts["italic"], "foreground": "#6941C6"},
            "code": {"font": self.fonts["mono"], "background": "#EEF2F6"},
            "mark": {"background": "#FFF1A8"},
            "sub": {"font": self.fonts["small"], "offset": -3},
            "sup": {"font": self.fonts["small"], "offset": 4},
            "kbd": {"font": self.fonts["mono"], "background": "#E8ECF2"},
            "samp": {"font": self.fonts["mono"], "foreground": "#344054"},
            "var": {"font": self.fonts["mono_italic"], "foreground": "#175CD3"},
            "abbr": {"underline": True, "foreground": "#175CD3"},
            "small": {"font": self.fonts["small"]},
            "ins": {"underline": True, "foreground": "#067647"},
            "del": {"overstrike": True, "foreground": "#B42318"},
            "span": {"background": "#F2F4F7"},
        }
        self.text.tag_configure(tag, **styles.get(element, {}))

    def apply_inline_structure(self, element):
        selected = self.selection()
        if not selected:
            self.notify("Elemento inline", "Selecione o trecho que deverá receber o elemento HTML.")
            return
        if element not in INLINE_ELEMENTS:
            return
        dialog = InlineStructureDialog(self, element=element, title="Aplicar elemento inline")
        if not dialog.result:
            return
        ranges = self.split_selection_by_lines(*selected)
        if not ranges:
            self.notify("Elemento inline", "A seleção não contém texto aplicável.")
            return
        for start, end in ranges:
            start_offset = self.index_to_offset(start)
            end_offset = self.index_to_offset(end)
            existing = None
            for tag, item in self.inline_structures.items():
                if item.get("element") == dialog.result["element"] and self.inline_offsets(tag) == (start_offset, end_offset):
                    existing = tag
                    break
            if existing:
                self.update_inline_structure(existing, dialog.result)
                continue
            tag = self.next_inline_tag()
            inline_id = self.next_inline_id()
            self.inline_structures[tag] = {
                "id": inline_id,
                "element": dialog.result["element"],
                "attrs": dict(dialog.result.get("attrs", {}))
            }
            self.text.tag_add(tag, start, end)
            self.apply_inline_style(tag, dialog.result["element"])
        self.dirty = True
        self.update_status()

    def update_inline_structure(self, tag, result):
        if tag not in self.inline_structures or result.get("element") not in INLINE_ELEMENTS:
            return
        item = self.inline_structures[tag]
        item["element"] = result["element"]
        allowed = set(INLINE_ELEMENTS[result["element"]]["attrs"])
        item["attrs"] = {
            key: str(value) for key, value in result.get("attrs", {}).items()
            if key in allowed and str(value).strip()
        }
        self.apply_inline_style(tag, item["element"])
        self.dirty = True
        self.update_status()

    def delete_inline_structure(self, tag):
        self.text.tag_delete(tag)
        self.inline_structures.pop(tag, None)
        self.dirty = True
        self.update_status()

    def open_inline_manager(self):
        InlineStructureManager(self)

    def next_hr_id(self):
        used = {item.get("id") for item in self.horizontal_rules.values()}
        number = 1
        while True:
            candidate = f"hr-{number:0{self.id_width()}d}"
            if candidate not in used:
                return candidate
            number += 1

    def next_hr_mark(self):
        number = 1
        while f"{self.HR_PREFIX}{number}" in self.horizontal_rules:
            number += 1
        return f"{self.HR_PREFIX}{number}"

    def sorted_hr_marks(self):
        return sorted(
            self.horizontal_rules,
            key=lambda mark: self.index_to_offset(self.text.index(mark))
        )

    def insert_hr(self):
        line_start = self.text.index("insert linestart")
        line_end = self.text.index("insert lineend")
        line_text = self.text.get(line_start, line_end)
        if line_text.strip():
            self.text.insert(line_end, "\n")
            hr_index = self.text.index(f"{line_end}+1c")
        else:
            hr_index = line_start
        hr_line = self.text.index(f"{hr_index} linestart")
        for mark in self.horizontal_rules:
            if self.text.index(f"{mark} linestart") == hr_line:
                self.notify("Separador horizontal", "Já existe um <hr> nesta linha.")
                return
        mark = self.next_hr_mark()
        self.text.mark_set(mark, hr_line)
        self.text.mark_gravity(mark, "left")
        self.horizontal_rules[mark] = {"id": self.next_hr_id()}
        self.refresh_hr_styles()
        self.dirty = True
        self.update_status()

    def refresh_hr_styles(self):
        for mark, item in self.horizontal_rules.items():
            style_tag = self.HR_STYLE_PREFIX + item["id"]
            self.text.tag_remove(style_tag, "1.0", "end")
            try:
                start = self.text.index(f"{mark} linestart")
                end = self.text.index(f"{mark} lineend+1c")
            except tk.TclError:
                continue
            self.text.tag_add(style_tag, start, end)
            self.text.tag_configure(
                style_tag, background="#E4E7EC", spacing1=7, spacing3=7
            )
            self.text.tag_lower(style_tag)

    def hr_for_line(self, line_start):
        for mark in self.sorted_hr_marks():
            mark_offset = self.index_to_offset(self.text.index(f"{mark} linestart"))
            if mark_offset == line_start:
                return mark
        return None

    def delete_hr(self, mark):
        item = self.horizontal_rules.pop(mark, None)
        if not item:
            return
        self.text.mark_unset(mark)
        self.text.tag_delete(self.HR_STYLE_PREFIX + item["id"])
        self.dirty = True
        self.update_status()

    def open_hr_manager(self):
        HorizontalRuleManager(self)

    def next_entity_id(self, entity_type):
        n = 1
        while True:
            candidate = f"{entity_type}-{n:0{self.id_width()}d}"
            if candidate not in self.entities:
                return candidate
            n += 1

    def next_text_id(self):
        max_n = 0
        for mark in self.marks.values():
            m = re.search(r"(\d+)$", mark.get("id", ""))
            if m:
                max_n = max(max_n, int(m.group(1)))
        return f"text-{max_n + 1:0{self.id_width()}d}"

    # ---------- Formatação ----------

    def selection(self):
        try:
            return self.text.index("sel.first"), self.text.index("sel.last")
        except tk.TclError:
            return None

    def toggle_format(self, tag):
        sel = self.selection()
        if not sel:
            self.notify("Formatação", "Selecione um trecho antes de aplicar a formatação.")
            return
        start, end = sel
        ranges = self.text.tag_ranges(tag)
        fully_tagged = False
        for i in range(0, len(ranges), 2):
            if self.text.compare(ranges[i], "<=", start) and self.text.compare(ranges[i + 1], ">=", end):
                fully_tagged = True
                break

        if fully_tagged:
            self.text.tag_remove(tag, start, end)
        else:
            self.text.tag_add(tag, start, end)

        self.refresh_combined_formatting()
        self.dirty = True

    def refresh_combined_formatting(self):
        """Mantém a visualização correta quando negrito e itálico se sobrepõem."""
        self.text.tag_remove("fmt_bold_italic", "1.0", "end")

        bold_ranges = self.text.tag_ranges("fmt_bold")
        italic_ranges = self.text.tag_ranges("fmt_italic")

        for i in range(0, len(bold_ranges), 2):
            b_start, b_end = bold_ranges[i], bold_ranges[i + 1]
            for j in range(0, len(italic_ranges), 2):
                i_start, i_end = italic_ranges[j], italic_ranges[j + 1]
                start = b_start if self.text.compare(b_start, ">=", i_start) else i_start
                end = b_end if self.text.compare(b_end, "<=", i_end) else i_end
                if self.text.compare(start, "<", end):
                    self.text.tag_add("fmt_bold_italic", start, end)

        self.text.tag_raise("fmt_bold_italic")

    def safe_edit(self, op):
        try:
            self.text.edit_undo() if op == "undo" else self.text.edit_redo()
        except tk.TclError:
            pass

    # ---------- Entidades ----------

    def change_entity_type(self, old_id, new_type):
        entity = self.entities[old_id]
        suffix_match = re.search(r"(\d+)$", old_id)
        suffix = suffix_match.group(1) if suffix_match else None
        preferred = f"{new_type}-{suffix}" if suffix else None

        if preferred and preferred not in self.entities:
            new_id = preferred
        else:
            new_id = self.next_entity_id(new_type)

        new_entity = dict(entity)
        new_entity["id"] = new_id
        new_entity["type"] = new_type

        del self.entities[old_id]
        self.entities[new_id] = new_entity
        self.replace_reference_everywhere(old_id, new_id)

        # Mantém data-target-type coerente quando possível.
        for mark in self.marks.values():
            targets = split_tokens(mark.get("meta", {}).get("data-target"))
            if new_id in targets and "data-target-type" in mark.get("meta", {}):
                mark["meta"]["data-target-type"] = new_type

        return new_id

    def replace_reference_everywhere(self, old_id, new_id):
        section_metas = [self.section_meta] + [
            section["meta"] for section in self.subsections.values()
        ]
        for meta in section_metas:
            for key, value in list(meta.items()):
                tokens = split_tokens(value)
                if old_id in tokens:
                    meta[key] = " ".join(new_id if x == old_id else x for x in tokens)

        for mark in self.marks.values():
            meta = mark.get("meta", {})
            for key, value in list(meta.items()):
                tokens = split_tokens(value)
                if old_id in tokens:
                    meta[key] = " ".join(new_id if x == old_id else x for x in tokens)

    def remove_entity_references(self, entity_id):
        section_metas = [self.section_meta] + [
            section["meta"] for section in self.subsections.values()
        ]
        for meta in section_metas:
            for key, value in list(meta.items()):
                tokens = split_tokens(value)
                if entity_id in tokens:
                    remaining = [x for x in tokens if x != entity_id]
                    if remaining:
                        meta[key] = " ".join(remaining)
                    else:
                        meta.pop(key, None)

        for mark in self.marks.values():
            meta = mark.get("meta", {})
            for key, value in list(meta.items()):
                tokens = split_tokens(value)
                if entity_id in tokens:
                    remaining = [x for x in tokens if x != entity_id]
                    if remaining:
                        meta[key] = " ".join(remaining)
                    else:
                        meta.pop(key, None)

    # ---------- Marcação semântica ----------

    def mark_selection(self):
        sel = self.selection()
        if not sel:
            self.notify("Marcação", "Selecione um trecho de texto para criar uma marcação.")
            return

        dlg = SemanticDialog(self)
        if not dlg.result:
            return

        start, end = sel
        ranges = self.split_selection_by_lines(start, end)
        if not ranges:
            return

        for a, b in ranges:
            mark_id = self.next_text_id()
            tag = self.SEM_PREFIX + mark_id
            meta = dict(dlg.result)
            self.marks[tag] = {
                "id": mark_id,
                "meta": meta
            }
            self.text.tag_add(tag, a, b)
            self.apply_semantic_style(tag, meta.get("data-role"))

        self.dirty = True
        self.update_status()

    def split_selection_by_lines(self, start, end):
        start_off = self.index_to_offset(start)
        end_off = self.index_to_offset(end)
        all_text = self.text.get("1.0", "end-1c")
        selected = all_text[start_off:end_off]
        ranges = []

        cursor = start_off
        for part in selected.splitlines(keepends=True):
            content = part[:-1] if part.endswith("\n") else part
            if content:
                ranges.append((self.offset_to_index(cursor), self.offset_to_index(cursor + len(content))))
            cursor += len(part)

        if selected and "\n" not in selected and not ranges:
            ranges.append((start, end))
        return ranges

    def semantic_tags_at(self, index):
        return [t for t in self.text.tag_names(index) if t.startswith(self.SEM_PREFIX)]

    def semantic_tags_overlapping(self, start, end):
        result = []
        for tag in self.marks:
            ranges = self.text.tag_ranges(tag)
            for i in range(0, len(ranges), 2):
                a, b = ranges[i], ranges[i + 1]
                if self.text.compare(a, "<", end) and self.text.compare(b, ">", start):
                    result.append(tag)
                    break
        return result

    def current_semantic_tag(self):
        sel = self.selection()
        index = sel[0] if sel else self.text.index("insert")
        tags = self.semantic_tags_at(index)
        if not tags and self.text.compare(index, ">", "1.0"):
            tags = self.semantic_tags_at(f"{index}-1c")
        return tags[-1] if tags else None

    def current_semantic_tags(self):
        sel = self.selection()
        index = sel[0] if sel else self.text.index("insert")
        tags = self.semantic_tags_at(index)
        if not tags and self.text.compare(index, ">", "1.0"):
            tags = self.semantic_tags_at(f"{index}-1c")
        return [tag for tag in tags if tag in self.marks]

    def choose_semantic_tag(self, action):
        tags = self.current_semantic_tags()
        if not tags:
            return None
        if len(tags) == 1:
            return tags[0]
        options = []
        for tag in tags:
            mark = self.marks[tag]
            role = mark.get("meta", {}).get("data-role", "sem papel")
            options.append((tag, f'{mark["id"]}  —  {role}'))
        return ChoiceOverlay(
            self, f"{action} marcação",
            "Há mais de uma marcação neste trecho. Selecione qual deve receber a operação.",
            options
        ).result

    def edit_mark_at_cursor(self):
        tag = self.choose_semantic_tag("Editar")
        if not tag or tag not in self.marks:
            self.notify("Marcação", "Posicione o cursor dentro de uma marcação semântica.")
            return

        mark = self.marks[tag]
        dlg = SemanticDialog(self, initial=mark["meta"])
        if not dlg.result:
            return

        mark["meta"] = dlg.result
        self.apply_semantic_style(tag, dlg.result.get("data-role"))
        self.dirty = True
        self.update_status()

    def remove_mark_at_cursor(self):
        tag = self.choose_semantic_tag("Remover")
        if not tag:
            return
        self.delete_semantic_tag(tag)
        self.dirty = True
        self.update_status()

    def delete_semantic_tag(self, tag):
        self.text.tag_delete(tag)
        self.marks.pop(tag, None)

    def apply_semantic_style(self, tag, role):
        if not self.tags_visible.get():
            style = {"background": COLORS["editor"], "relief": "flat", "borderwidth": 0}
        else:
            style = dict(self.semantic_styles.get(role, {"background": "#EEF0F4"}))
            style.update({"relief": "flat", "borderwidth": 0})
        self.text.tag_configure(tag, **style)

    def toggle_tag_visibility(self):
        for tag, mark in self.marks.items():
            self.apply_semantic_style(tag, mark.get("meta", {}).get("data-role"))
        if self.tags_visible.get():
            self.legend_frame.pack(fill="x", pady=(14, 0))
            self.editor_hint_var.set("Tags perceptíveis — as cores indicam o papel narrativo")
        else:
            self.legend_frame.pack_forget()
            self.editor_hint_var.set("Tags preservadas, mas ocultas durante a escrita")
        self.update_status()

    # ---------- Elementos de capítulo / glossário ----------

    def edit_chapter_element(self, element_key):
        if element_key not in self.chapter_elements:
            return
        dlg = ChapterElementDialog(self, element_key, self.chapter_elements.get(element_key, ""))
        if not dlg.confirmed:
            return
        self.chapter_elements[element_key] = dlg.result or ""
        self.dirty = True
        self.update_status()

    def open_glossary(self):
        GlossaryManager(self)

    # ---------- Seção / schema ----------

    def edit_section(self):
        SectionManager(self)

    def reload_schema(self):
        try:
            new_schema = load_schema(self.schema_path)
        except Exception as exc:
            self.notify("Schema", f"Erro ao recarregar schema.json:\n{exc}", "error")
            return
        self.schema = new_schema
        self.notify(
            "Schema",
            "schema.json recarregado.\n\nMarcações existentes foram preservadas. "
            "A validação na exportação apontará valores que deixaram de ser válidos.",
            "success"
        )

    # ---------- Projeto ----------

    def new_project(self):
        if not self.confirm_discard():
            return
        self.text.delete("1.0", "end")
        for tag in list(self.marks):
            self.text.tag_delete(tag)
        for tag in list(self.subsections):
            self.text.tag_delete(tag)
        for tag in list(self.lists):
            self.text.tag_delete(tag)
        for tag in list(self.inline_structures):
            self.text.tag_delete(tag)
        for mark, item in list(self.horizontal_rules.items()):
            self.text.mark_unset(mark)
            self.text.tag_delete(self.HR_STYLE_PREFIX + item["id"])
        self.entities = {}
        self.marks = {}
        self.subsections = {}
        self.lists = {}
        self.inline_structures = {}
        self.horizontal_rules = {}
        self.chapter_elements = {"anteriormente": "", "previa": ""}
        self.glossary = {}
        self.section_meta = self.default_section_meta(scope="chapter")
        self.project_path = None
        self.dirty = False
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.refresh_project_identity()
        self.update_document_metrics()
        self.update_status()

    def open_project(self):
        if not self.confirm_discard():
            return
        path = filedialog.askopenfilename(
            title="Abrir projeto",
            filetypes=[("Projeto narrativo", f"*{PROJECT_EXT}"), ("JSON", "*.json"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.load_project_data(data)
        except Exception as exc:
            self.notify("Abrir projeto", f"Não foi possível abrir o projeto:\n{exc}", "error")
            return

        self.project_path = Path(path)
        self.dirty = False
        self.refresh_project_identity()
        self.update_status()

    def refresh_project_identity(self):
        if self.project_path:
            name = self.project_path.name
            self.title(f"{APP_TITLE} — {name}")
            if hasattr(self, "project_name_var"):
                self.project_name_var.set(name)
        else:
            self.title(APP_TITLE)
            if hasattr(self, "project_name_var"):
                self.project_name_var.set("Projeto sem título")

    def save_project(self):
        if self.project_path is None:
            return self.save_project_as()
        try:
            self.project_path.write_text(
                json.dumps(self.project_data(), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as exc:
            self.notify("Salvar projeto", f"Não foi possível salvar:\n{exc}", "error")
            return False
        self.dirty = False
        self.refresh_project_identity()
        self.update_status()
        return True

    def save_project_as(self):
        path = filedialog.asksaveasfilename(
            title="Salvar projeto",
            defaultextension=PROJECT_EXT,
            filetypes=[("Projeto narrativo", f"*{PROJECT_EXT}"), ("JSON", "*.json")]
        )
        if not path:
            return False
        self.project_path = Path(path)
        return self.save_project()

    def project_data(self):
        text_value = self.text.get("1.0", "end-1c")
        formatting = {}
        for tag in ("fmt_bold", "fmt_italic", "fmt_underline"):
            formatting[tag] = self.tag_ranges_as_offsets(tag)

        semantic = []
        for tag, mark in self.marks.items():
            ranges = self.tag_ranges_as_offsets(tag)
            for start, end in ranges:
                semantic.append({
                    "id": mark["id"],
                    "start": start,
                    "end": end,
                    "meta": mark["meta"]
                })

        sections = []
        for tag in self.sorted_subsection_tags():
            start, end = self.section_offsets(tag)
            section = self.subsections[tag]
            sections.append({
                "id": section["id"],
                "start": start,
                "end": end,
                "parent_id": self.section_parent_id(tag),
                "meta": dict(section["meta"])
            })

        lists = []
        for tag in self.sorted_list_tags():
            start, end = self.list_offsets(tag)
            item = self.lists[tag]
            lists.append({
                "id": item["id"],
                "type": item["type"],
                "start": start,
                "end": end
            })

        inline_structures = []
        for tag in self.sorted_inline_tags():
            start, end = self.inline_offsets(tag)
            item = self.inline_structures[tag]
            inline_structures.append({
                "id": item["id"],
                "element": item["element"],
                "attrs": dict(item.get("attrs", {})),
                "start": start,
                "end": end
            })

        horizontal_rules = []
        for mark in self.sorted_hr_marks():
            horizontal_rules.append({
                "id": self.horizontal_rules[mark]["id"],
                "offset": self.index_to_offset(self.text.index(mark))
            })

        return {
            "version": 5,
            "text": text_value,
            "section": self.section_meta,
            "sections": sections,
            "lists": lists,
            "inline_structures": inline_structures,
            "horizontal_rules": horizontal_rules,
            "entities": list(self.entities.values()),
            "formatting": formatting,
            "semantic": semantic,
            "elements": dict(self.chapter_elements),
            "glossary": dict(self.glossary)
        }

    def load_project_data(self, data):
        self.text.delete("1.0", "end")
        for tag in list(self.marks):
            self.text.tag_delete(tag)
        for tag in list(getattr(self, "subsections", {})):
            self.text.tag_delete(tag)
        for tag in list(getattr(self, "lists", {})):
            self.text.tag_delete(tag)
        for tag in list(getattr(self, "inline_structures", {})):
            self.text.tag_delete(tag)
        for mark, item in list(getattr(self, "horizontal_rules", {}).items()):
            self.text.mark_unset(mark)
            self.text.tag_delete(self.HR_STYLE_PREFIX + item["id"])

        self.text.insert("1.0", data.get("text", ""))
        self.entities = {e["id"]: e for e in data.get("entities", [])}
        self.section_meta = data.get("section") or self.default_section_meta(scope="chapter")

        elements = data.get("elements") if isinstance(data.get("elements"), dict) else {}
        self.chapter_elements = {
            "anteriormente": str(elements.get("anteriormente", "") or ""),
            "previa": str(elements.get("previa", "") or "")
        }

        glossary = data.get("glossary") if isinstance(data.get("glossary"), dict) else {}
        self.glossary = {
            str(term): str(definition)
            for term, definition in glossary.items()
            if str(term).strip() and str(definition).strip()
        }
        self.marks = {}
        self.subsections = {}
        self.lists = {}
        self.inline_structures = {}
        self.horizontal_rules = {}

        for tag, ranges in data.get("formatting", {}).items():
            if tag not in ("fmt_bold", "fmt_italic", "fmt_underline"):
                continue
            for start, end in ranges:
                self.text.tag_add(tag, self.offset_to_index(start), self.offset_to_index(end))

        for item in data.get("semantic", []):
            mark_id = item["id"]
            tag = self.SEM_PREFIX + mark_id
            self.marks[tag] = {"id": mark_id, "meta": dict(item.get("meta", {}))}
            self.text.tag_add(
                tag,
                self.offset_to_index(item["start"]),
                self.offset_to_index(item["end"])
            )
            self.apply_semantic_style(tag, item.get("meta", {}).get("data-role"))

        text_length = len(self.text.get("1.0", "end-1c"))
        for item in data.get("sections", []):
            try:
                start = max(0, min(int(item.get("start", 0)), text_length))
                end = max(start, min(int(item.get("end", start)), text_length))
            except (TypeError, ValueError):
                continue
            if start >= end:
                continue
            meta = dict(item.get("meta", {}))
            section_id = str(item.get("id") or meta.get("id") or "").strip()
            if not section_id:
                section_id = self.next_section_id(meta.get("data-scope", "scene"))
            meta["id"] = section_id
            tag = self.next_section_tag()
            self.subsections[tag] = {"id": section_id, "meta": meta}
            self.text.tag_add(tag, self.offset_to_index(start), self.offset_to_index(end))

        for item in data.get("lists", []):
            try:
                start = max(0, min(int(item.get("start", 0)), text_length))
                end = max(start, min(int(item.get("end", start)), text_length))
            except (TypeError, ValueError):
                continue
            list_type = str(item.get("type", ""))
            if start >= end or list_type not in {"ul", "ol"}:
                continue
            list_id = str(item.get("id") or self.next_list_id())
            tag = self.next_list_tag()
            self.lists[tag] = {"id": list_id, "type": list_type}
            self.text.tag_add(tag, self.offset_to_index(start), self.offset_to_index(end))
            self.apply_list_style(tag, list_type)

        for item in data.get("inline_structures", []):
            try:
                start = max(0, min(int(item.get("start", 0)), text_length))
                end = max(start, min(int(item.get("end", start)), text_length))
            except (TypeError, ValueError):
                continue
            element = str(item.get("element", ""))
            if start >= end or element not in INLINE_ELEMENTS:
                continue
            inline_id = str(item.get("id") or self.next_inline_id())
            allowed = set(INLINE_ELEMENTS[element]["attrs"])
            raw_attrs = item.get("attrs", {}) if isinstance(item.get("attrs"), dict) else {}
            attrs = {key: str(value) for key, value in raw_attrs.items() if key in allowed}
            tag = self.next_inline_tag()
            self.inline_structures[tag] = {
                "id": inline_id, "element": element, "attrs": attrs
            }
            self.text.tag_add(tag, self.offset_to_index(start), self.offset_to_index(end))
            self.apply_inline_style(tag, element)

        for item in data.get("horizontal_rules", []):
            try:
                offset = max(0, min(int(item.get("offset", 0)), text_length))
            except (TypeError, ValueError):
                continue
            mark = self.next_hr_mark()
            hr_id = str(item.get("id") or self.next_hr_id())
            self.text.mark_set(mark, self.offset_to_index(offset))
            self.text.mark_gravity(mark, "left")
            self.horizontal_rules[mark] = {"id": hr_id}
        self.refresh_hr_styles()

        self.refresh_combined_formatting()
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.update_document_metrics()

    def confirm_discard(self):
        if not self.dirty:
            return True
        answer = MessageOverlay(
            self, "Alterações não salvas",
            "O documento possui alterações não salvas. O que deseja fazer antes de continuar?",
            kind="warning",
            choices=[
                ("Cancelar", "cancel", "TButton"),
                ("Descartar", "discard", "Danger.TButton"),
                ("Salvar", "save", "Accent.TButton"),
            ]
        ).result
        if answer in (None, "cancel"):
            return False
        if answer == "save":
            return bool(self.save_project())
        return True

    # ---------- Offsets / tags ----------

    def index_to_offset(self, index):
        result = self.text.count("1.0", index, "chars")
        return int(result[0]) if result else 0

    def offset_to_index(self, offset):
        return self.text.index(f"1.0+{int(offset)}c")

    def tag_ranges_as_offsets(self, tag):
        ranges = self.text.tag_ranges(tag)
        result = []
        for i in range(0, len(ranges), 2):
            result.append([
                self.index_to_offset(ranges[i]),
                self.index_to_offset(ranges[i + 1])
            ])
        return result

    # ---------- Validação ----------

    def validate_document(self):
        problems = []

        # Seção principal e seções internas
        section_items = [("Seção principal", self.section_meta)] + [
            (section["id"], section["meta"]) for section in self.subsections.values()
        ]
        seen_section_ids = set()
        for owner, meta in section_items:
            section_id = meta.get("id", "")
            if not section_id:
                problems.append(f"{owner}: id é obrigatório.")
            elif section_id in seen_section_ids:
                problems.append(f'Seções: o id "{section_id}" está duplicado.')
            seen_section_ids.add(section_id)
            for name, spec in self.schema.get("section", {}).get("attributes", {}).items():
                value = meta.get(name, "")
                if spec.get("required") and not value:
                    problems.append(f'{owner}: "{name}" é obrigatório.')
                self.validate_value(owner, name, value, spec, problems)

        tags = list(self.subsections)
        for index, tag in enumerate(tags):
            start, end = self.section_offsets(tag)
            if start >= end:
                problems.append(f'{self.subsections[tag]["id"]}: a seção não contém texto.')
            for other in tags[index + 1:]:
                other_start, other_end = self.section_offsets(other)
                overlaps = start < other_end and end > other_start
                nested = (start <= other_start and end >= other_end) or (
                    other_start <= start and other_end >= end
                )
                if overlaps and not nested:
                    problems.append(
                        f'{self.subsections[tag]["id"]} cruza parcialmente '
                        f'{self.subsections[other]["id"]}; sections HTML precisam ser aninhadas.'
                    )

        # Listas estruturais
        list_tags = list(self.lists)
        seen_list_ids = set()
        for index, tag in enumerate(list_tags):
            item = self.lists[tag]
            list_id = item.get("id", "")
            if not list_id:
                problems.append("Lista sem id interno.")
            elif list_id in seen_list_ids:
                problems.append(f'Listas: o id "{list_id}" está duplicado.')
            seen_list_ids.add(list_id)
            if item.get("type") not in {"ul", "ol"}:
                problems.append(f'{list_id}: tipo de lista inválido "{item.get("type")}".')
            start, end = self.list_offsets(tag)
            if start >= end:
                problems.append(f"{list_id}: a lista não contém texto.")
            for other in list_tags[index + 1:]:
                other_start, other_end = self.list_offsets(other)
                if start < other_end and end > other_start:
                    problems.append(
                        f'{list_id} sobrepõe {self.lists[other]["id"]}; intervalos de listas não podem se cruzar.'
                    )

        # Elementos inline independentes do schema
        seen_inline_ids = set()
        for tag, item in self.inline_structures.items():
            inline_id = item.get("id", "")
            element = item.get("element", "")
            if not inline_id or inline_id in seen_inline_ids:
                problems.append(f'Elemento inline com id ausente ou duplicado: "{inline_id}".')
            seen_inline_ids.add(inline_id)
            if element not in INLINE_ELEMENTS:
                problems.append(f'{inline_id}: elemento inline inválido <{element}>.')
                continue
            invalid_attrs = set(item.get("attrs", {})) - set(INLINE_ELEMENTS[element]["attrs"])
            if invalid_attrs:
                problems.append(
                    f'{inline_id}: atributos não permitidos em <{element}>: {", ".join(sorted(invalid_attrs))}.'
                )
            start, end = self.inline_offsets(tag)
            if start >= end:
                problems.append(f"{inline_id}: elemento inline sem texto.")

        seen_hr_ids = set()
        seen_hr_offsets = set()
        for mark in self.horizontal_rules:
            hr_id = self.horizontal_rules[mark].get("id", "")
            offset = self.index_to_offset(self.text.index(f"{mark} linestart"))
            if not hr_id or hr_id in seen_hr_ids:
                problems.append(f'Separador <hr> com id ausente ou duplicado: "{hr_id}".')
            if offset in seen_hr_offsets:
                problems.append(f"{hr_id}: existe mais de um <hr> na mesma linha.")
            seen_hr_ids.add(hr_id)
            seen_hr_offsets.add(offset)

        # Entidades
        valid_entity_types = set(self.schema.get("entity_types", []))
        for entity in self.entities.values():
            if entity.get("type") not in valid_entity_types:
                problems.append(
                    f'Entidade {entity["id"]}: tipo "{entity.get("type")}" não existe mais no schema.'
                )

        # Marcações
        for tag, mark in self.marks.items():
            meta = mark.get("meta", {})
            role = meta.get("data-role", "")
            role_spec = self.schema.get("roles", {}).get(role)
            if not role_spec:
                problems.append(f'{mark["id"]}: função "{role}" não existe no schema.')
                continue

            for name, spec in role_spec.get("attributes", {}).items():
                value = spec.get("value", "") if spec.get("kind") == "const" else meta.get(name, "")
                if spec.get("required") and not value:
                    problems.append(f'{mark["id"]}: "{name}" é obrigatório.')
                self.validate_value(mark["id"], name, value, spec, problems)

            response_to = split_tokens(meta.get("data-response-to"))
            if mark["id"] in response_to:
                problems.append(f'{mark["id"]}: data-response-to não pode apontar para si mesmo.')

            if role_spec.get("allow_inline") is False:
                ranges = self.tag_ranges_as_offsets(tag)
                full_text = self.text.get("1.0", "end-1c")
                for start, end in ranges:
                    line_start = full_text.rfind("\n", 0, start) + 1
                    next_nl = full_text.find("\n", end)
                    line_end = len(full_text) if next_nl == -1 else next_nl
                    if start != line_start or end != line_end:
                        problems.append(
                            f'{mark["id"]}: a função "{role}" deve ocupar uma linha/parágrafo inteiro.'
                        )
                        break

            target_type = meta.get("data-target-type")
            for target_id in split_tokens(meta.get("data-target")):
                entity = self.entities.get(target_id)
                if entity and target_type and entity.get("type") != target_type:
                    problems.append(
                        f'{mark["id"]}: data-target-type="{target_type}" mas {target_id} '
                        f'é do tipo "{entity.get("type")}".'
                    )

        return problems

    def validate_value(self, owner, name, value, spec, problems):
        if not value:
            return

        kind = spec.get("kind")
        tokens = split_tokens(value) if spec.get("multiple") else [str(value)]

        if kind == "enum":
            allowed = set(spec.get("values", []))
            for token in tokens:
                if token not in allowed:
                    problems.append(f'{owner}: "{name}" contém valor inválido "{token}".')

        elif kind == "entity_ref":
            allowed_types = set(spec.get("entity_types", []))
            for entity_id in tokens:
                entity = self.entities.get(entity_id)
                if not entity:
                    problems.append(f'{owner}: "{name}" referencia entidade inexistente "{entity_id}".')
                elif allowed_types and entity.get("type") not in allowed_types:
                    problems.append(
                        f'{owner}: "{name}" referencia {entity_id}, tipo "{entity.get("type")}", '
                        f'fora dos tipos permitidos.'
                    )

        elif kind == "text_ref":
            valid_ids = {m["id"] for m in self.marks.values()}
            for text_id in tokens:
                if text_id not in valid_ids:
                    problems.append(f'{owner}: "{name}" referencia texto inexistente "{text_id}".')

    # ---------- Exportação HTML ----------

    def html_tag_for_mark(self, mark, inline=False):
        """Retorna a tag HTML nativa configurada no schema para a marcação."""
        meta = mark.get("meta", {})
        role = meta.get("data-role", "")
        role_spec = self.schema.get("roles", {}).get(role, {})

        if inline:
            return role_spec.get("inline_tag") or "span"

        mapping = role_spec.get("html_tag_by_attribute")
        if mapping:
            attr_name = mapping.get("attribute")
            attr_value = meta.get(attr_name)
            tag = mapping.get("map", {}).get(attr_value)
            if tag:
                return tag
            if mapping.get("default"):
                return mapping["default"]

        return role_spec.get("html_tag", "p")

    def render_glossary_text(self, value):
        """Escapa texto e transforma termos cadastrados em elementos clicáveis."""
        value = str(value or "")
        if not value or not self.glossary:
            return html.escape(value)

        terms = [term for term in self.glossary if term]
        if not terms:
            return html.escape(value)

        by_fold = {term.casefold(): term for term in terms}
        pattern = re.compile(
            r"(?<!\w)(?:" + "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True)) + r")(?!\w)",
            re.IGNORECASE
        )

        pieces = []
        cursor = 0
        for match in pattern.finditer(value):
            pieces.append(html.escape(value[cursor:match.start()]))
            shown = match.group(0)
            canonical = by_fold.get(shown.casefold(), shown)
            pieces.append(
                '<span class="story-glossary-term lore-term" '
                f'data-glossary-term="{html.escape(canonical, quote=True)}">'
                f'{html.escape(shown)}</span>'
            )
            cursor = match.end()
        pieces.append(html.escape(value[cursor:]))
        return "".join(pieces)

    def render_special_element(self, element_key):
        value = self.chapter_elements.get(element_key, "").strip()
        if not value:
            return []

        spec = {
            "anteriormente": {
                "label": "Anteriormente...",
                "classes": "story-element story-previous recaptulation",
                "summary_class": "story-element-summary recaptulation-summary"
            },
            "previa": {
                "label": "No Próximo Capítulo...",
                "classes": "story-element story-preview preview",
                "summary_class": "story-element-summary preview-summary"
            }
        }[element_key]

        paragraphs = re.split(r"\n\s*\n", value)
        content = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            rendered = "<br>".join(self.render_glossary_text(line) for line in paragraph.splitlines())
            content.append(f'            <p>{rendered}</p>')

        return [
            f'        <details class="{spec["classes"]}" data-story-element="{element_key}">',
            f'            <summary class="{spec["summary_class"]}">{spec["label"]}</summary>',
            '            <div class="story-element-content">',
            *content,
            '            </div>',
            '        </details>'
        ]

    def glossary_runtime_script(self):
        """Runtime leve para HTML exportado diretamente; o leitor possui implementação própria."""
        return r"""    <script data-story-glossary-runtime>
    (() => {
      const dataNode = document.getElementById("story-glossary");
      if (!dataNode) return;
      let glossary = {};
      try { glossary = JSON.parse(dataNode.textContent || "{}"); } catch (_err) { return; }
      if (!glossary || typeof glossary !== "object") return;

      let panel = document.getElementById("story-glossary-popover");
      if (!panel) {
        const style = document.createElement("style");
        style.textContent = `
          .story-glossary-term,.lore-term{border-bottom:1px dashed currentColor;cursor:pointer;text-decoration:none}
          #story-glossary-popover{position:fixed;right:24px;bottom:24px;z-index:9999;width:min(360px,calc(100vw - 32px));padding:18px 42px 18px 18px;border:1px solid rgba(127,127,127,.35);border-radius:12px;background:Canvas;color:CanvasText;box-shadow:0 16px 42px rgba(0,0,0,.24);font:14px/1.55 system-ui,sans-serif}
          #story-glossary-popover[hidden]{display:none}#story-glossary-popover h4{margin:0 0 8px;font-size:16px}#story-glossary-popover p{margin:0}#story-glossary-popover button{position:absolute;right:10px;top:8px;border:0;background:transparent;color:inherit;cursor:pointer;font-size:18px}
        `;
        document.head.appendChild(style);
        panel = document.createElement("aside");
        panel.id = "story-glossary-popover";
        panel.hidden = true;
        panel.innerHTML = '<button type="button" aria-label="Fechar glossário">×</button><h4></h4><p></p>';
        document.body.appendChild(panel);
        panel.querySelector("button").addEventListener("click", () => { panel.hidden = true; });
      }

      const title = panel.querySelector("h4");
      const description = panel.querySelector("p");
      const open = element => {
        const term = element.dataset.glossaryTerm || element.textContent.trim();
        const definition = glossary[term];
        if (!definition) return;
        title.textContent = term;
        description.textContent = definition;
        panel.hidden = false;
      };

      document.querySelectorAll('.story-glossary-term[data-glossary-term], .lore-term[data-glossary-term]').forEach(element => {
        if (element.dataset.glossaryBound === "1") return;
        element.dataset.glossaryBound = "1";
        element.tabIndex = 0;
        element.setAttribute("role", "button");
        element.addEventListener("click", () => open(element));
        element.addEventListener("keydown", event => {
          if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(element); }
        });
      });
    })();
    </script>"""

    def export_html(self):
        problems = self.validate_document()
        if problems:
            shown = "\n".join(f"• {p}" for p in problems[:18])
            if len(problems) > 18:
                shown += f"\n• ... e mais {len(problems) - 18} problema(s)."
            if not self.ask_confirmation(
                "Validação",
                "Foram encontrados problemas:\n\n"
                f"{shown}\n\n"
                "Deseja exportar mesmo assim?"
            ):
                return

        path = filedialog.asksaveasfilename(
            title="Exportar HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")]
        )
        if not path:
            return

        try:
            output = self.build_html()
            Path(path).write_text(output, encoding="utf-8")
        except Exception as exc:
            self.notify("Exportar HTML", f"Erro ao exportar:\n{exc}", "error")
            return

        self.notify("Exportação concluída", f"HTML exportado para:\n{path}", "success")

    def build_html(self):
        text_value = self.text.get("1.0", "end-1c")
        section_attrs = dict(self.section_meta)
        section_id = section_attrs.pop("id", self.next_section_id("chapter"))

        lines = text_value.split("\n")
        result_lines = [
            f'    <section id="{html.escape(section_id, quote=True)}"{self.attrs_to_html(section_attrs)}>'
        ]
        result_lines.extend(self.render_special_element("anteriormente"))

        open_at = {}
        close_at = {}
        for tag in self.subsections:
            raw_start, raw_end = self.section_offsets(tag)
            start = text_value.rfind("\n", 0, raw_start) + 1
            next_newline = text_value.find("\n", raw_end)
            end = len(text_value) if next_newline == -1 else next_newline
            section = self.subsections[tag]
            entry = (start, end, section)
            open_at.setdefault(start, []).append(entry)
            close_at.setdefault(end, []).append(entry)

        for entries in open_at.values():
            entries.sort(key=lambda item: (-item[1], item[2]["id"]))
        for entries in close_at.values():
            entries.sort(key=lambda item: (item[0], item[2]["id"]), reverse=True)

        offset = 0
        open_depth = 0
        active_list_tag = None
        for line in lines:
            start = offset
            end = offset + len(line)

            if open_at.get(start) and active_list_tag:
                indent = "        " + "    " * open_depth
                result_lines.append(f"{indent}</{self.lists[active_list_tag]['type']}>")
                active_list_tag = None

            for _section_start, _section_end, section in open_at.get(start, []):
                attrs = dict(section.get("meta", {}))
                nested_id = attrs.pop("id", section["id"])
                indent = "        " + "    " * open_depth
                result_lines.append(
                    f'{indent}<section id="{html.escape(nested_id, quote=True)}"'
                    f'{self.attrs_to_html(attrs)}>'
                )
                open_depth += 1

            hr_mark = self.hr_for_line(start)
            line_list_tag = self.list_tag_for_range(start, end) if line.strip() and not hr_mark else None
            indent = "        " + "    " * open_depth

            if active_list_tag and active_list_tag != line_list_tag:
                result_lines.append(f"{indent}</{self.lists[active_list_tag]['type']}>")
                active_list_tag = None

            if hr_mark:
                hr_id = html.escape(self.horizontal_rules[hr_mark]["id"], quote=True)
                result_lines.append(f'{indent}<hr data-structure-id="{hr_id}">')
            elif line_list_tag:
                if active_list_tag != line_list_tag:
                    list_item = self.lists[line_list_tag]
                    list_type = list_item["type"]
                    list_id = html.escape(list_item["id"], quote=True)
                    result_lines.append(f'{indent}<{list_type} data-list-id="{list_id}">')
                    active_list_tag = line_list_tag
                inner = self.render_inline(start, end)
                result_lines.append(f'{indent}    <li>{inner or "<br>"}</li>')
            else:
                full_mark = self.full_semantic_mark_for_range(start, end) if line else None
                if full_mark:
                    mark = self.marks[full_mark]
                    attrs = {"id": mark["id"], **mark["meta"]}
                    tag_name = self.html_tag_for_mark(mark, inline=False)
                    role_spec = self.schema.get("roles", {}).get(mark["meta"].get("data-role", ""), {})

                    if role_spec.get("void_element"):
                        result_lines.append(f'{indent}<{tag_name}{self.attrs_to_html(attrs)}>')
                    else:
                        inner = self.render_inline(start, end, skip_semantic_tag=full_mark)
                        result_lines.append(
                            f'{indent}<{tag_name}{self.attrs_to_html(attrs)}>{inner or "<br>"}</{tag_name}>'
                        )
                else:
                    inner = self.render_inline(start, end)
                    result_lines.append(f'{indent}<p>{inner or "<br>"}</p>')

            section_closings = close_at.get(end, [])
            if section_closings and active_list_tag:
                result_lines.append(f"{indent}</{self.lists[active_list_tag]['type']}>")
                active_list_tag = None

            for _section_start, _section_end, _section in section_closings:
                open_depth = max(0, open_depth - 1)
                indent = "        " + "    " * open_depth
                result_lines.append(f"{indent}</section>")

            offset = end + 1  # newline

        if active_list_tag:
            indent = "        " + "    " * open_depth
            result_lines.append(f"{indent}</{self.lists[active_list_tag]['type']}>")
            active_list_tag = None

        while open_depth > 0:
            open_depth -= 1
            indent = "        " + "    " * open_depth
            result_lines.append(f"{indent}</section>")

        result_lines.extend(self.render_special_element("previa"))

        # Registro central de entidades para consumidores do HTML, como o leitor semântico.
        # As marcações continuam apontando para IDs estáveis; nome e tipo ficam
        # armazenados uma única vez neste JSON incorporado.
        entities_json = json.dumps(
            sorted(
                self.entities.values(),
                key=lambda e: (
                    str(e.get("type", "")),
                    str(e.get("name", "")).lower(),
                    str(e.get("id", ""))
                )
            ),
            ensure_ascii=False,
            indent=2
        ).replace("</script", "<\\/script")

        glossary_json = json.dumps(
            dict(sorted(self.glossary.items(), key=lambda item: item[0].casefold())),
            ensure_ascii=False,
            indent=2
        ).replace("</script", "<\\/script")

        result_lines.extend([
            "    </section>",
            '    <script id="story-entities" type="application/json">',
            *[f"    {line}" for line in entities_json.splitlines()],
            "    </script>",
            '    <script id="story-glossary" type="application/json">',
            *[f"    {line}" for line in glossary_json.splitlines()],
            "    </script>",
            self.glossary_runtime_script(),
            ""
        ])
        return "\n".join(result_lines)

    def full_semantic_mark_for_range(self, start, end):
        if start == end:
            return None
        for tag in self.marks:
            ranges = self.tag_ranges_as_offsets(tag)
            for a, b in ranges:
                if a <= start and b >= end:
                    return tag
        return None

    def render_inline(self, start, end, skip_semantic_tag=None):
        if start >= end:
            return ""

        boundaries = {start, end}
        relevant = (
            ["fmt_bold", "fmt_italic", "fmt_underline"]
            + list(self.marks.keys())
            + list(self.inline_structures.keys())
        )

        range_cache = {}
        for tag in relevant:
            if tag == skip_semantic_tag:
                continue
            ranges = self.tag_ranges_as_offsets(tag)
            range_cache[tag] = ranges
            for a, b in ranges:
                if a < end and b > start:
                    boundaries.add(max(start, a))
                    boundaries.add(min(end, b))

        points = sorted(boundaries)
        raw_text = self.text.get("1.0", "end-1c")
        pieces = []

        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            if a >= b:
                continue
            segment = self.render_glossary_text(raw_text[a:b])
            active = []

            for tag, ranges in range_cache.items():
                if any(x <= a and y >= b for x, y in ranges):
                    active.append(tag)

            if "fmt_bold" in active:
                segment = f"<strong>{segment}</strong>"
            if "fmt_italic" in active:
                segment = f"<em>{segment}</em>"
            if "fmt_underline" in active:
                segment = f"<u>{segment}</u>"

            semantic = sorted(t for t in active if t.startswith(self.SEM_PREFIX))
            for tag in semantic:
                mark = self.marks.get(tag)
                if mark:
                    # A mesma marca pode aparecer em mais de um fragmento quando
                    # existem sobreposições. data-text-id preserva a identidade
                    # sem produzir IDs HTML duplicados.
                    attrs = {"data-text-id": mark["id"], **mark["meta"]}
                    inline_tag = self.html_tag_for_mark(mark, inline=True)
                    segment = (
                        f"<{inline_tag}{self.attrs_to_html(attrs)}>"
                        f"{segment}</{inline_tag}>"
                    )

            structural = sorted(
                (t for t in active if t.startswith(self.INLINE_PREFIX)),
                key=lambda t: self.inline_structures.get(t, {}).get("id", "")
            )
            for tag in structural:
                item = self.inline_structures.get(tag)
                if not item or item.get("element") not in INLINE_ELEMENTS:
                    continue
                attrs = {
                    "data-structure-id": item["id"],
                    **item.get("attrs", {})
                }
                element = item["element"]
                segment = f"<{element}{self.attrs_to_html(attrs)}>{segment}</{element}>"

            pieces.append(segment)

        return "".join(pieces)

    @staticmethod
    def attrs_to_html(attrs):
        parts = []
        for key, value in attrs.items():
            if value is None or value == "":
                continue
            parts.append(f' {key}="{html.escape(str(value), quote=True)}"')
        return "".join(parts)

    # ---------- Eventos / status ----------

    @staticmethod
    def text_statistics(value):
        """Calcula métricas editoriais sem contar marcas ou metadados."""
        value = str(value or "")
        word_pattern = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*|\d+(?:[.,]\d+)*", re.UNICODE)
        words = word_pattern.findall(value)
        paragraphs = sum(1 for line in value.splitlines() if line.strip())

        sentence_count = 0
        for paragraph in (line.strip() for line in value.splitlines() if line.strip()):
            protected = re.sub(r"(?<=\d)[.,](?=\d)", "¤", paragraph)
            protected = re.sub(
                r"\b(sr|sra|srta|dr|dra|prof|profa|etc|ex)\.",
                lambda match: match.group(0)[:-1] + "¤",
                protected,
                flags=re.IGNORECASE
            )
            fragments = re.split(r"[.!?…]+(?:[\"'»”’\)\]]*)", protected)
            sentence_count += sum(1 for fragment in fragments if word_pattern.search(fragment))

        visible_chars = value.replace("\r", "").replace("\n", "")
        reading_seconds = 0
        if words:
            reading_seconds = max(1, round(len(words) * 60 / READING_WORDS_PER_MINUTE))

        return {
            "words": len(words),
            "sentences": sentence_count,
            "paragraphs": paragraphs,
            "chars_spaces": len(visible_chars),
            "chars_no_spaces": len(re.sub(r"\s+", "", value)),
            "reading_seconds": reading_seconds,
        }

    @staticmethod
    def format_reading_time(seconds):
        if seconds <= 0:
            return "0 min"
        if seconds < 60:
            return "< 1 min"
        minutes = (seconds + 59) // 60
        if minutes < 60:
            return f"{minutes} min"
        hours, remainder = divmod(minutes, 60)
        return f"{hours} h {remainder:02d} min" if remainder else f"{hours} h"

    @staticmethod
    def format_count(value):
        return f"{int(value):,}".replace(",", ".")

    def schedule_document_metrics(self):
        if self._metrics_job is not None:
            self.after_cancel(self._metrics_job)
        self._metrics_job = self.after(140, self.update_document_metrics)

    def update_document_metrics(self):
        self._metrics_job = None
        if not hasattr(self, "text"):
            return
        stats = self.text_statistics(self.text.get("1.0", "end-1c"))
        for key in ("words", "sentences", "paragraphs", "chars_spaces", "chars_no_spaces"):
            self.stats_vars[key].set(self.format_count(stats[key]))
        self.stats_vars["reading"].set(self.format_reading_time(stats["reading_seconds"]))

    def on_text_modified(self, event=None):
        if self.text.edit_modified():
            self.dirty = True
            self.text.edit_modified(False)
            self.refresh_combined_formatting()
            self.refresh_hr_styles()
            self.schedule_document_metrics()
            self.update_status()

    def update_status(self):
        tags = []
        if hasattr(self, "text"):
            index = self.text.index("insert")
            tags = self.semantic_tags_at(index)
            if not tags and self.text.compare(index, ">", "1.0"):
                tags = self.semantic_tags_at(f"{index}-1c")
        tags = [tag for tag in tags if tag in self.marks]
        if tags:
            descriptions = []
            for tag in tags:
                mark = self.marks[tag]
                role = mark["meta"].get("data-role", "?")
                descriptions.append(f'{mark["id"]}\nPapel: {role}')
            self.tag_inspector_var.set("\n\n".join(descriptions))
            mark_text = f" | No cursor: {len(tags)} marcação(ões)"
        else:
            if hasattr(self, "tag_inspector_var"):
                self.tag_inspector_var.set("Nenhuma marcação no cursor.")
            mark_text = ""
        element_count = sum(bool(value.strip()) for value in self.chapter_elements.values())
        visibility = "visíveis" if self.tags_visible.get() else "ocultas"
        self.status_var.set(
            f"Entidades: {len(self.entities)} | Marcações: {len(self.marks)}"
            f" | Elementos: {element_count} | Glossário: {len(self.glossary)}"
            f" | Tags {visibility} | Inline: {len(self.inline_structures)}"
            f" | HR: {len(self.horizontal_rules)} | Listas: {len(self.lists)}"
            f" | Seções: {1 + len(self.subsections)}"
            f" | Principal: {self.section_meta.get('id', '')}{mark_text}"
        )
        if hasattr(self, "project_name_var"):
            base = self.project_path.name if self.project_path else "Projeto sem título"
            self.project_name_var.set(f"{base}{'  •  não salvo' if self.dirty else ''}")

    def on_close(self):
        if self.overlay_stack:
            self.close_active_overlay()
            return
        if self.confirm_discard():
            self.destroy()


if __name__ == "__main__":
    app = SemanticEditor()
    if app.winfo_exists():
        app.mainloop()
