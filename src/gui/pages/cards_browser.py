from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional, Callable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from data import Card, KanaCard, KanjiCard, PhraseCard



@dataclass(frozen=True)
class _Row:
    kind: str                 # "Kana" | "Kanji" | "Phrase"
    card: Card
    obj: KanaCard | KanjiCard | PhraseCard                  # KanaCard | KanjiCard | PhraseCard

@dataclass(frozen=True)
class _Col:
    header: str
    value: Callable[[_Row], str]   # _Row -> cell text



class CardBrowserWidget(QWidget):
    """
    Minimal "Anki-like" browser:
      - Left: type filter tree
      - Center: QTableView (QStandardItemModel)
      - Right: fields panel (changes based on selected row type)
      - Top: search bar (filters rows)
    """

    COLS = ["ID", "Type", "Due", "Study", "Front", "Back"]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Card Browser")

        # ---------- UI: top search bar ----------
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search (kana/romaji, kanji/on/kun/meaning, phrase/meaning/grammar...)")
        self._search.textChanged.connect(self._rebuild_table)

        top = QHBoxLayout()
        top.addWidget(QLabel("Search:"))
        top.addWidget(self._search)

        # ---------- Left: type filter ----------
        self._filter_tree = QTreeWidget()
        self._filter_tree.setHeaderHidden(True)
        self._filter_tree.setMaximumWidth(260)

        root = QTreeWidgetItem(self._filter_tree, ["Card Types"])
        root.setExpanded(True)
        self._item_all = QTreeWidgetItem(root, ["All"])
        self._item_kana = QTreeWidgetItem(root, ["Kana"])
        self._item_kanji = QTreeWidgetItem(root, ["Kanji"])
        self._item_phrase = QTreeWidgetItem(root, ["Phrase"])
        self._filter_tree.setCurrentItem(self._item_all)
        self._filter_tree.currentItemChanged.connect(lambda *_: self._rebuild_table())

        # ---------- Center: table ----------
        self._table = QTableView()
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)

        self._model = QStandardItemModel(0, len(self.COLS), self)
        self._model.setHorizontalHeaderLabels(self.COLS)
        self._table.setModel(self._model)

        hh = self._table.horizontalHeader()
        assert hh
        hh.setStretchLastSection(True)
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Due
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Study

        self._table.verticalHeader().setVisible(False) # pyright: ignore

        # ---------- Right: fields panel (stacked by type) ----------
        self._fields_stack = QStackedWidget()
        self._fields_stack.setMinimumWidth(340)
        self._fields_stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._fields_none = QLabel("Select a card…")
        self._fields_none.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._fields_stack.addWidget(self._fields_none)

        self._fields_kana = self._make_kana_fields()
        self._fields_kanji = self._make_kanji_fields()
        self._fields_phrase = self._make_phrase_fields()

        self._fields_stack.addWidget(self._fields_kana["root"])
        self._fields_stack.addWidget(self._fields_kanji["root"])
        self._fields_stack.addWidget(self._fields_phrase["root"])

        # ---------- Main splitter layout ----------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._filter_tree)
        splitter.addWidget(self._table)
        splitter.addWidget(self._fields_stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(splitter)

        # ---------- Data ----------
        self._all_rows: list[_Row] = []
        self._visible_rows: list[_Row] = []

        self._load_rows()
        self._rebuild_table()

        # selection handler
        sel = self._table.selectionModel()
        sel.selectionChanged.connect(lambda *_: self._sync_fields_from_selection()) # pyright: ignore

    # -------------------------------------------------------------------------
    # Field panels
    # -------------------------------------------------------------------------
    def _make_ro_text(self) -> QPlainTextEdit:
        w = QPlainTextEdit()
        w.setReadOnly(True)
        w.setMaximumBlockCount(2000)
        return w

    def _make_ro_line(self) -> QLineEdit:
        w = QLineEdit()
        w.setReadOnly(True)
        return w

    def _make_kana_fields(self) -> dict[str, Any]:
        root = QWidget()
        form = QFormLayout(root)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        f = {
            "root": root,
            "id": self._make_ro_line(),
            "due": self._make_ro_line(),
            "study": self._make_ro_line(),
            "kana": self._make_ro_line(),
            "romaji": self._make_ro_line(),
            "tags": self._make_ro_line(),
        }
        form.addRow(QLabel("<b>Kana</b>"), QLabel(""))
        form.addRow("id", f["id"])
        form.addRow("due_date", f["due"])
        form.addRow("study_id", f["study"])
        form.addRow("kana", f["kana"])
        form.addRow("romaji", f["romaji"])
        form.addRow("tags", f["tags"])
        return f

    def _make_kanji_fields(self) -> dict[str, Any]:
        root = QWidget()
        form = QFormLayout(root)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        f = {
            "root": root,
            "id": self._make_ro_line(),
            "due": self._make_ro_line(),
            "study": self._make_ro_line(),
            "kanji": self._make_ro_line(),
            "on": self._make_ro_text(),
            "kun": self._make_ro_text(),
            "meaning": self._make_ro_text(),
            "tags": self._make_ro_line(),
        }
        form.addRow(QLabel("<b>Kanji</b>"), QLabel(""))
        form.addRow("id", f["id"])
        form.addRow("due_date", f["due"])
        form.addRow("study_id", f["study"])
        form.addRow("kanji", f["kanji"])
        form.addRow("on_yomi", f["on"])
        form.addRow("kun_yomi", f["kun"])
        form.addRow("meaning", f["meaning"])
        form.addRow("tags", f["tags"])
        return f

    def _make_phrase_fields(self) -> dict[str, Any]:
        root = QWidget()
        form = QFormLayout(root)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        f = {
            "root": root,
            "id": self._make_ro_line(),
            "due": self._make_ro_line(),
            "study": self._make_ro_line(),
            "kanji_phrase": self._make_ro_text(),
            "kana_phrase": self._make_ro_text(),
            "meaning": self._make_ro_text(),
            "grammar": self._make_ro_line(),
            "tags": self._make_ro_line(),
        }
        form.addRow(QLabel("<b>Phrase</b>"), QLabel(""))
        form.addRow("id", f["id"])
        form.addRow("due_date", f["due"])
        form.addRow("study_id", f["study"])
        form.addRow("kanji_phrase", f["kanji_phrase"])
        form.addRow("kana_phrase", f["kana_phrase"])
        form.addRow("meaning", f["meaning"])
        form.addRow("grammar", f["grammar"])
        form.addRow("tags", f["tags"])
        return f

    # -------------------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------------------
    def _load_rows(self) -> None:
        """
        Build a unified list of rows with (kind, Card, specific_card_obj).
        Uses your wrappers which already cache/load from sqlite.
        """
        self._all_rows.clear()

        # Note: these call _load_from_db internally
        for kc in KanaCard.in_db():
            self._all_rows.append(_Row("Kana", kc.card, kc))

        for kj in KanjiCard.in_db():
            self._all_rows.append(_Row("Kanji", kj.card, kj))

        for pc in PhraseCard.in_db():
            self._all_rows.append(_Row("Phrase", pc.card, pc))

        # Sort by due date then id (roughly like browser lists)
        def key(r: _Row):
            d = r.card.due_date if isinstance(r.card.due_date, date) else date.min
            return (d, r.card.id)

        self._all_rows.sort(key=key)

    # -------------------------------------------------------------------------
    # Filtering + table rebuild
    # -------------------------------------------------------------------------
    def _current_kind_filter(self) -> Optional[str]:
        it = self._filter_tree.currentItem()
        if it is None:
            return None
        text = it.text(0)
        if text in ("Kana", "Kanji", "Phrase"):
            return text
        return None  # All

    def _row_text(self, r: _Row) -> str:
        """
        A single searchable string containing relevant fields per type.
        """
        base = f"{r.card.id} {r.kind} {r.card.study_id} {r.card.due_date} {r.card.tags}"
        if isinstance(r.obj, KanaCard):
            kc: KanaCard = r.obj
            return base + f" {kc.kana} {kc.romaji}"
        elif isinstance(r.obj, KanjiCard):
            kj: KanjiCard = r.obj
            return base + f" {kj.kanji} {kj.on_yomi or ''} {kj.kun_yomi or ''} {kj.meaning or ''}"
        elif isinstance(r.obj, PhraseCard):
            pc: PhraseCard = r.obj
            return base + f" {pc.kanji_phrase or ''} {pc.kana_phrase or ''} {pc.meaning} {pc.grammar or ''}"
        return base

    # def _rebuild_table(self) -> None:
    #     kind = self._current_kind_filter()
    #     q = self._search.text().strip().casefold()

    #     # filter
    #     vis: list[_Row] = []
    #     for r in self._all_rows:
    #         if kind and r.kind != kind:
    #             continue
    #         if q:
    #             if q not in self._row_text(r).casefold():
    #                 continue
    #         vis.append(r)

    #     self._visible_rows = vis

    #     # rebuild model
    #     self._model.setRowCount(0)
    #     for r in self._visible_rows:
    #         items = self._row_to_items(r)
    #         self._model.appendRow(items)

    #     # auto select first row (optional, feels like browser)
    #     if self._visible_rows:
    #         self._table.selectRow(0)
    #     else:
    #         self._fields_stack.setCurrentIndex(0)
    #         self._fields_none.setText("No cards match your filter/search…")


    
    def _rebuild_table(self) -> None:
        kind = self._current_kind_filter()   # None means "All"
        q = self._search.text().strip().casefold()

        # filter rows (same as before)
        vis: list[_Row] = []
        for r in self._all_rows:
            if kind and r.kind != kind:
                continue
            if q and q not in self._row_text(r).casefold():
                continue
            vis.append(r)
        self._visible_rows = vis

        cols = self._columns_for_kind(kind)

        # rebuild model structure (dynamic columns)
        self._model.clear()
        self._model.setColumnCount(len(cols))
        self._model.setHorizontalHeaderLabels([c.header for c in cols])

        for r in self._visible_rows:
            items: list[QStandardItem] = []
            for c in cols:
                it = QStandardItem(c.value(r))
                it.setEditable(False)
                items.append(it)
            self._model.appendRow(items)

        # resizing (optional)
        hh = self._table.horizontalHeader()
        assert hh
        hh.setStretchLastSection(True)
        for i in range(len(cols)):
            hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        # keep selection driving fields
        if self._visible_rows:
            self._table.selectRow(0)
        else:
            self._fields_stack.setCurrentIndex(0)
            self._fields_none.setText("No cards match your filter/search…")
    
    def _row_to_items(self, r: _Row) -> list[QStandardItem]:
        # Columns: ID, Type, Due, Study, Front, Back
        id_item = QStandardItem(str(r.card.id))
        type_item = QStandardItem(r.kind)
        due_item = QStandardItem(str(r.card.due_date))
        study_item = QStandardItem(str(r.card.study_id))

        front, back = self._front_back(r)

        front_item = QStandardItem(front)
        back_item = QStandardItem(back)

        # make them non-editable, select whole row
        for it in (id_item, type_item, due_item, study_item, front_item, back_item):
            it.setEditable(False)

        return [id_item, type_item, due_item, study_item, front_item, back_item]

    def _front_back(self, r: _Row) -> tuple[str, str]:
        if isinstance(r.obj, KanaCard):
            kc: KanaCard = r.obj
            return (kc.kana, kc.romaji)
        elif isinstance(r.obj, KanjiCard):
            kj: KanjiCard = r.obj
            front = kj.kanji
            back = (kj.meaning or "").strip()
            return (front, back)
        elif isinstance(r.obj, PhraseCard):
            pc: PhraseCard = r.obj
            front = (pc.kanji_phrase or pc.kana_phrase or "").strip()
            back = pc.meaning.strip()
            return (front, back)
        return ("", "")

    # -------------------------------------------------------------------------
    # Selection -> fields
    # -------------------------------------------------------------------------
    def _selected_row_index(self) -> int:
        sel = self._table.selectionModel()
        if not sel:
            return -1
        rows = sel.selectedRows()
        if not rows:
            return -1
        return rows[0].row()

    def _sync_fields_from_selection(self) -> None:
        idx = self._selected_row_index()
        if idx < 0 or idx >= len(self._visible_rows):
            self._fields_stack.setCurrentIndex(0)
            return

        r = self._visible_rows[idx]
        if r.kind == "Kana":
            self._fill_kana(r)
        elif r.kind == "Kanji":
            self._fill_kanji(r)
        elif r.kind == "Phrase":
            self._fill_phrase(r)
        else:
            self._fields_stack.setCurrentIndex(0)

    def _fill_kana(self, r: _Row) -> None:
        assert isinstance(r.obj, KanaCard)
        kc: KanaCard = r.obj
        f = self._fields_kana
        f["id"].setText(str(r.card.id))
        f["due"].setText(str(r.card.due_date))
        f["study"].setText(str(r.card.study_id))
        f["kana"].setText(kc.kana)
        f["romaji"].setText(kc.romaji or "")
        f["tags"].setText(r.card.tags)
        self._fields_stack.setCurrentWidget(f["root"])

    def _fill_kanji(self, r: _Row) -> None:
        assert isinstance(r.obj, KanjiCard)
        kj: KanjiCard = r.obj
        f = self._fields_kanji
        f["id"].setText(str(r.card.id))
        f["due"].setText(str(r.card.due_date))
        f["study"].setText(str(r.card.study_id))
        f["kanji"].setText(kj.kanji)
        f["on"].setPlainText(kj.on_yomi or "")
        f["kun"].setPlainText(kj.kun_yomi or "")
        f["meaning"].setPlainText(kj.meaning or "")
        f["tags"].setText(r.card.tags)
        self._fields_stack.setCurrentWidget(f["root"])

    def _fill_phrase(self, r: _Row) -> None:
        assert isinstance(r.obj, PhraseCard)
        pc: PhraseCard = r.obj
        f = self._fields_phrase
        f["id"].setText(str(r.card.id))
        f["due"].setText(str(r.card.due_date))
        f["study"].setText(str(r.card.study_id))
        f["kanji_phrase"].setPlainText(pc.kanji_phrase or "")
        f["kana_phrase"].setPlainText(pc.kana_phrase or "")
        f["meaning"].setPlainText(pc.meaning or "")
        f["grammar"].setText(pc.grammar or "")
        f["tags"].setText(r.card.tags)
        self._fields_stack.setCurrentWidget(f["root"])


    def _columns_for_kind(self, kind: str | None) -> list[_Col]:
        # kind is None for "All"
        if kind is None:
            return [
                _Col("ID",   lambda r: str(r.card.id)),
                _Col("Type", lambda r: r.kind),
                _Col("Due",  lambda r: str(r.card.due_date)),
                _Col("Deck", lambda r: str(r.card.study_id)),
                _Col("Front", lambda r: self._front_back(r)[0]),
                _Col("Back",  lambda r: self._front_back(r)[1]),
            ]

        if kind == "Kana":
            def as_kana(r: _Row) -> KanaCard:
                assert isinstance(r.obj, KanaCard)
                return r.obj
            
            return [
                _Col("ID",     lambda r: str(r.card.id)),
                _Col("Due",    lambda r: str(r.card.due_date)),
                _Col("Kana",   lambda r: as_kana(r).kana),
                _Col("Romaji", lambda r: as_kana(r).romaji or ""),
                _Col("Tags",   lambda r: as_kana(r).card.tags),
            ]

        if kind == "Kanji":
            def as_kanji(r: _Row) -> KanjiCard:
                assert isinstance(r.obj, KanjiCard)
                return r.obj
            return [
                _Col("ID",      lambda r: str(r.card.id)),
                _Col("Due",     lambda r: str(r.card.due_date)),
                _Col("Kanji",   lambda r: as_kanji(r).kanji),
                _Col("On",      lambda r: as_kanji(r).on_yomi or ""),
                _Col("Kun",     lambda r: as_kanji(r).kun_yomi or ""),
                _Col("Meaning", lambda r: as_kanji(r).meaning or ""),
            ]

        if kind == "Phrase":
            def as_phrase(r: _Row) -> PhraseCard:
                assert isinstance(r.obj, PhraseCard)
                return r.obj
            return [
                _Col("ID",          lambda r: str(r.card.id)),
                _Col("Due",         lambda r: str(r.card.due_date)),
                _Col("Kanji phrase",lambda r: as_phrase(r).kanji_phrase or ""),
                _Col("Kana phrase", lambda r: as_phrase(r).kana_phrase or ""),
                _Col("Meaning",     lambda r: as_phrase(r).meaning or ""),
                _Col("Grammar",     lambda r: as_phrase(r).grammar or ""),
            ]

        return []
