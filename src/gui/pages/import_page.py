from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableView,
    QHeaderView,
    QMessageBox,
    QComboBox,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QCheckBox,
)

from data import KanaCard, KanjiCard, PhraseCard, maybe_connection_commit

class ImportPage(QWidget):

    # ---------------- UI mode ----------------

    def _on_mode_toggle(self) -> None:
        loaded = self._model.rowCount() > 0
        use_flags = self._use_flag_mode.isChecked()

        # enable the relevant selector
        self._type_col_cb.setEnabled(use_flags and loaded)
        self._single_type_cb.setEnabled((not use_flags) and loaded)

        # hide flags when not used
        self._kana_flag.setVisible(use_flags)
        self._kanji_flag.setVisible(use_flags)
        self._phrase_flag.setVisible(use_flags)

        self._apply_type_enabled_state()
        self._recompute_types()

    # ---------------- File I/O ----------------

    def _on_clear(self) -> None:
        self._path = None
        self._path_lbl.setText("No file loaded")
        self._status_lbl.setText("")
        self._model.clear()
        self._type_col_cb.clear()
        self._set_controls_enabled(False)
        self._process_btn.setEnabled(False)
        self._on_mode_toggle()



    def _on_open(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV/TSV",
            "",
            "Delimited text (*.csv *.tsv *.txt);;CSV (*.csv);;TSV (*.tsv);;All files (*)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            self._load_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Import failed", f"Could not load file:\n{path}\n\n{e}")



    def _load_file(self, path: Path) -> None:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig", errors="replace")

        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        sample = text[:4096]
        try:
            sniffed = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            delim = sniffed.delimiter or delim
        except Exception:
            pass

        rows: list[list[str]] = []
        reader = csv.reader(text.splitlines(), delimiter=delim)
        for r in reader:
            rows.append([c if c is not None else "" for c in r])

        self._model.clear()
        self._path = path
        self._path_lbl.setText(str(path))
        self._status_lbl.setText("")

        if not rows:
            self._type_col_cb.clear()
            self._set_controls_enabled(False)
            self._process_btn.setEnabled(False)
            self._on_mode_toggle()
            return

        # First row is treated as "header shape" only
        header = rows[0]
        data_rows = rows[1:]

        col_count = len(header)
        for r in data_rows:
            if len(r) < col_count:
                r.extend([""] * (col_count - len(r)))
            elif len(r) > col_count:
                extra = len(r) - col_count
                header.extend([""] * extra)
                col_count = len(header)

        # Add computed Type column
        self._model.setColumnCount(col_count + 1)
        self._model.setHorizontalHeaderLabels([f"Column {i+1}" for i in range(col_count)] + ["Type"])

        for r in data_rows:
            if len(r) < col_count:
                r.extend([""] * (col_count - len(r)))

            items = []
            for c in r[:col_count]:
                it = QStandardItem(str(c))
                it.setEditable(False)
                items.append(it)

            t = QStandardItem("")
            t.setEditable(False)
            items.append(t)
            self._model.appendRow(items)

        # Type column choices (source columns only)
        self._type_col_cb.blockSignals(True)
        self._type_col_cb.clear()
        for i in range(col_count):
            self._type_col_cb.addItem(f"Column {i+1}", i)
        self._type_col_cb.setCurrentIndex(0)
        self._type_col_cb.blockSignals(False)

        # Fill mapping combos
        self._fill_column_combo(self._kana_kana_col, col_count, allow_none=False)
        self._fill_column_combo(self._kana_romaji_col, col_count, allow_none=False)

        self._fill_column_combo(self._kanji_kanji_col, col_count, allow_none=False)
        self._fill_column_combo(self._kanji_onyomi_col, col_count, allow_none=False)
        self._fill_column_combo(self._kanji_kunyomi_col, col_count, allow_none=False)
        self._fill_column_combo(self._kanji_meaning_col, col_count, allow_none=False)

        self._fill_column_combo(self._phrase_kanji_col, col_count, allow_none=True)
        self._fill_column_combo(self._phrase_kana_col, col_count, allow_none=True)
        self._fill_column_combo(self._phrase_grammar_col, col_count, allow_none=True)
        self._fill_column_combo(self._phrase_meaning_col, col_count, allow_none=False)

        self._set_controls_enabled(True)
        self._apply_type_enabled_state()
        self._recompute_types()
        self._table.resizeColumnsToContents()
        self._on_mode_toggle()

    # ---------------- Processing ----------------



    def _extract_raw_rows(self) -> list[list[str]]:
        raw_rows: list[list[str]] = []
        src_cols = max(0, self._model.columnCount() - 1)  # exclude computed Type
        for r in range(self._model.rowCount()):
            row: list[str] = []
            for c in range(src_cols):
                it = self._model.item(r, c)
                row.append("" if it is None else it.text())
            raw_rows.append(row)
        return raw_rows


    def _process_data(self, config: dict[str, Any], rows: list[list[str]]) -> None:
        type_col = self._model.columnCount() - 1

        def cell(row: int, col: int) -> str:
            if col < 0:
                return ""
            it = self._model.item(row, col)
            return "" if it is None else it.text().strip()

        errors: list[str] = []
        made = {"KanaCard": 0, "KanjiCard": 0, "PhraseCard": 0}

        for r in range(self._model.rowCount()):
            kind_item = self._model.item(r, type_col)
            kind = "" if kind_item is None else kind_item.text()

            if kind == "UNKNOWN":
                errors.append(f"Row {r+1}: UNKNOWN type")
                continue

            created: list[KanaCard | KanjiCard | PhraseCard] = []
            try:
                if kind == "KanaCard":
                    m = config["mapping"]["kana"]
                    kana = cell(r, m["kana"])
                    romaji = cell(r, m["romaji"])
                    if not kana or not romaji:
                        raise ValueError("KanaCard requires kana and romaji")
                    kc = KanaCard.create(kana=kana, romaji=romaji)
                    created.append(kc)
                    made["KanaCard"] += 1

                elif kind == "KanjiCard":
                    m = config["mapping"]["kanji"]
                    kanji = cell(r, m["kanji"])
                    onyomi = cell(r, m["onyomi"])
                    kunyomi = cell(r, m["kunyomi"])
                    meaning = cell(r, m["meaning"])
                    if not kanji or not meaning:
                        raise ValueError("KanjiCard requires kanji and meaning")
                    kc = KanjiCard.create(kanji=kanji, on_yomi=onyomi, kun_yomi=kunyomi, meaning=meaning)
                    created.append(kc)
                    made["KanjiCard"] += 1

                elif kind == "PhraseCard":
                    m = config["mapping"]["phrase"]
                    kanji_phrase = cell(r, m["kanji_phrase"]) if m["kanji_phrase"] != -1 else ""
                    kana_phrase = cell(r, m["kana_phrase"]) if m["kana_phrase"] != -1 else ""
                    grammar = cell(r, m["grammar"]) if m["grammar"] != -1 else ""
                    meaning = cell(r, m["meaning"])
                    if not meaning:
                        raise ValueError("PhraseCard requires meaning")
                    if not (kanji_phrase or kana_phrase):
                        raise ValueError("PhraseCard requires kanji_phrase or kana_phrase")
                    pc = PhraseCard.create(kanji_phrase=kanji_phrase, kana_phrase=kana_phrase, grammar=grammar, meaning=meaning)
                    created.append(pc)
                    made["PhraseCard"] += 1

                else:
                    errors.append(f"Row {r+1}: unrecognized type '{kind}'")

            except Exception as e:
                errors.append(f"Row {r+1} ({kind}): {e}")

            # Synchronize the new cards
            with maybe_connection_commit(None) as con:
                for c in created:
                    c.sync(con)
            

        msg = (
            f"Created:\n"
            f"  KanaCard: {made['KanaCard']}\n"
            f"  KanjiCard: {made['KanjiCard']}\n"
            f"  PhraseCard: {made['PhraseCard']}\n"
        )
        if errors:
            msg += "\nErrors:\n" + "\n".join(errors[:50])
            if len(errors) > 50:
                msg += f"\n... and {len(errors)-50} more"

        QMessageBox.information(self, "Import result", msg)


    def _on_process(self) -> None:
        ok, errs = self._all_valid()
        if not ok:
            QMessageBox.warning(self, "Invalid configuration", "\n".join(errs))
            return

        config = self._build_config()
        raw_rows = self._extract_raw_rows()

        try:
            self._process_data(config, raw_rows)
        except Exception as e:
            QMessageBox.critical(self, "Processing failed", str(e))

    # ---------------- Enable/Disable UI ----------------

    def _set_controls_enabled(self, enabled: bool) -> None:
        # NOTE: mode toggle will further refine what's enabled/visible
        for w in (
            self._type_col_cb,
            self._single_type_cb,
            self._use_flag_mode,
            self._kana_enabled, self._kanji_enabled, self._phrase_enabled,
            self._kana_flag, self._kanji_flag, self._phrase_flag,
            self._kana_kana_col, self._kana_romaji_col,
            self._kanji_kanji_col, self._kanji_onyomi_col, self._kanji_kunyomi_col, self._kanji_meaning_col,
            self._phrase_kanji_col, self._phrase_kana_col, self._phrase_grammar_col, self._phrase_meaning_col,
        ):
            w.setEnabled(enabled)

    def _on_type_toggle(self) -> None:
        self._apply_type_enabled_state()
        self._recompute_types()

    def _apply_type_enabled_state(self) -> None:
        loaded = self._model.rowCount() > 0
        kana_on = self._kana_enabled.isChecked()
        kanji_on = self._kanji_enabled.isChecked()
        phrase_on = self._phrase_enabled.isChecked()
        use_flags = self._use_flag_mode.isChecked()

        # flags enabled only in flag mode
        self._kana_flag.setEnabled(loaded and use_flags and kana_on)
        self._kanji_flag.setEnabled(loaded and use_flags and kanji_on)
        self._phrase_flag.setEnabled(loaded and use_flags and phrase_on)

        # mappings enabled whenever loaded + type enabled
        self._kana_kana_col.setEnabled(loaded and kana_on)
        self._kana_romaji_col.setEnabled(loaded and kana_on)

        self._kanji_kanji_col.setEnabled(loaded and kanji_on)
        self._kanji_onyomi_col.setEnabled(loaded and kanji_on)
        self._kanji_kunyomi_col.setEnabled(loaded and kanji_on)
        self._kanji_meaning_col.setEnabled(loaded and kanji_on)

        self._phrase_kanji_col.setEnabled(loaded and phrase_on)
        self._phrase_kana_col.setEnabled(loaded and phrase_on)
        self._phrase_grammar_col.setEnabled(loaded and phrase_on)
        self._phrase_meaning_col.setEnabled(loaded and phrase_on)

    # ---------------- Validation ----------------

    def _validate_mappings(self) -> list[str]:
        errs: list[str] = []

        kana_on = self._kana_enabled.isChecked()
        kanji_on = self._kanji_enabled.isChecked()
        phrase_on = self._phrase_enabled.isChecked()

        use_flags = self._use_flag_mode.isChecked()

        # Mode-specific checks
        if not use_flags:
            enabled: list[str] = []
            if kana_on:
                enabled.append("KanaCard")
            if kanji_on:
                enabled.append("KanjiCard")
            if phrase_on:
                enabled.append("PhraseCard")

            if len(enabled) != 1:
                errs.append("Single-type mode: enable exactly one card type.")
            else:
                chosen = self._single_type_cb.currentText()
                if enabled[0] != chosen:
                    errs.append("Single-type mode: enabled type must match 'Single type' selection.")
        else:
            if not (kana_on or kanji_on or phrase_on):
                errs.append("Enable at least one card type.")

            # Flag checks only in flag mode
            if kana_on and not self._kana_flag.text().strip():
                errs.append("KanaCard: Kana flag is empty.")
            if kanji_on and not self._kanji_flag.text().strip():
                errs.append("KanjiCard: Kanji flag is empty.")
            if phrase_on and not self._phrase_flag.text().strip():
                errs.append("PhraseCard: Phrase flag is empty.")

        # Mapping checks (both modes)
        if kana_on:
            kc = int(self._kana_kana_col.currentData())
            rc = int(self._kana_romaji_col.currentData())
            if kc == rc:
                errs.append("KanaCard: kana and romaji columns must be different.")

        if kanji_on:
            k = int(self._kanji_kanji_col.currentData())
            o = int(self._kanji_onyomi_col.currentData())
            ku = int(self._kanji_kunyomi_col.currentData())
            m = int(self._kanji_meaning_col.currentData())
            cols = [k, o, ku, m]
            if len(set(cols)) != len(cols):
                errs.append("KanjiCard: kanji/onyomi/kunyomi/meaning columns must all be different.")

        if phrase_on:
            pk = int(self._phrase_kanji_col.currentData())
            pa = int(self._phrase_kana_col.currentData())
            pm = int(self._phrase_meaning_col.currentData())
            pg = int(self._phrase_grammar_col.currentData())

            if pk == -1 and pa == -1:
                errs.append("PhraseCard: specify at least one of (kanji writing, kana writing).")

            used = [c for c in [pk, pa, pm, pg] if c != -1]
            if len(set(used)) != len(used):
                errs.append("PhraseCard: selected columns must be distinct (ignoring None).")

        return errs

    def _all_valid(self) -> tuple[bool, list[str]]:
        if self._model.rowCount() == 0:
            return False, ["No data loaded."]
        errs = self._validate_mappings()
        return (len(errs) == 0), errs

    def _build_config(self) -> dict[str, Any]:
        use_flags = self._use_flag_mode.isChecked()
        return {
            "mode": "flags" if use_flags else "single",
            "single_type": self._single_type_cb.currentText(),
            "type_column": int(self._type_col_cb.currentData()) if self._type_col_cb.count() else -1,
            "enabled": {
                "kana": self._kana_enabled.isChecked(),
                "kanji": self._kanji_enabled.isChecked(),
                "phrase": self._phrase_enabled.isChecked(),
            },
            "flags": {
                "kana": self._kana_flag.text().strip(),
                "kanji": self._kanji_flag.text().strip(),
                "phrase": self._phrase_flag.text().strip(),
            },
            "mapping": {
                "kana": {
                    "kana": int(self._kana_kana_col.currentData()),
                    "romaji": int(self._kana_romaji_col.currentData()),
                },
                "kanji": {
                    "kanji": int(self._kanji_kanji_col.currentData()),
                    "onyomi": int(self._kanji_onyomi_col.currentData()),
                    "kunyomi": int(self._kanji_kunyomi_col.currentData()),
                    "meaning": int(self._kanji_meaning_col.currentData()),
                },
                "phrase": {
                    "kanji_phrase": int(self._phrase_kanji_col.currentData()),
                    "kana_phrase": int(self._phrase_kana_col.currentData()),
                    "grammar": int(self._phrase_grammar_col.currentData()),
                    "meaning": int(self._phrase_meaning_col.currentData()),
                },
            },
        }

    # ---------------- Preview classification ----------------

    def _recompute_types(self) -> None:
        ok, errs = self._all_valid()

        if errs:
            self._status_lbl.setText("⚠ " + "\n⚠ ".join(errs))
        else:
            self._status_lbl.setText("")
        self._process_btn.setEnabled(ok)

        if self._model.rowCount() == 0 or self._model.columnCount() == 0:
            return

        computed_col = self._model.columnCount() - 1
        use_flags = self._use_flag_mode.isChecked()

        if not use_flags:
            chosen = self._single_type_cb.currentText()

            def classify(_: str) -> str:
                return chosen

            src_col = -1
        else:
            if self._type_col_cb.currentIndex() < 0:
                return
            src_col = int(self._type_col_cb.currentData())

            kana_on = self._kana_enabled.isChecked()
            kanji_on = self._kanji_enabled.isChecked()
            phrase_on = self._phrase_enabled.isChecked()

            kana_flag = self._kana_flag.text().strip().casefold()
            kanji_flag = self._kanji_flag.text().strip().casefold()
            phrase_flag = self._phrase_flag.text().strip().casefold()

            def classify(flag: str) -> str:
                f = flag.strip().casefold()
                if kana_on and kana_flag and f == kana_flag:
                    return "KanaCard"
                if kanji_on and kanji_flag and f == kanji_flag:
                    return "KanjiCard"
                if phrase_on and phrase_flag and f == phrase_flag:
                    return "PhraseCard"
                return "UNKNOWN"

        for r in range(self._model.rowCount()):
            if use_flags:
                src_item = self._model.item(r, src_col)
                flag_val = src_item.text() if src_item is not None else ""
                kind = classify(flag_val)
            else:
                kind = classify("")

            out_item = self._model.item(r, computed_col)
            if out_item is None:
                out_item = QStandardItem("")
                out_item.setEditable(False)
                self._model.setItem(r, computed_col, out_item)

            out_item.setText(kind)
            if kind == "UNKNOWN":
                out_item.setBackground(Qt.GlobalColor.yellow)
            else:
                out_item.setBackground(Qt.GlobalColor.transparent)

    # ---------------- helpers ----------------

    def _fill_column_combo(self, cb: QComboBox, col_count: int, allow_none: bool) -> None:
        cb.blockSignals(True)
        cb.clear()
        if allow_none:
            cb.addItem("(None)", -1)
        for i in range(col_count):
            cb.addItem(f"Column {i+1}", i)
        cb.setCurrentIndex(0)
        cb.blockSignals(False)

    # Constructor ##############################################################
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._path: Path | None = None
        self._model = QStandardItemModel(self)

        self._open_btn = QPushButton("Open CSV/TSV…")
        self._clear_btn = QPushButton("Clear")
        self._process_btn = QPushButton("Process / Import")
        self._process_btn.setEnabled(False)

        self._path_lbl = QLabel("No file loaded")
        self._path_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # ----- Row classification controls -----
        self._type_col_cb = QComboBox()
        self._type_col_cb.setEnabled(False)

        self._kana_enabled = QCheckBox("Enable Kana")
        self._kanji_enabled = QCheckBox("Enable Kanji")
        self._phrase_enabled = QCheckBox("Enable Phrase")
        self._kana_enabled.setChecked(True)
        self._kanji_enabled.setChecked(True)
        self._phrase_enabled.setChecked(True)

        # per-type flag fields
        self._kana_flag = QLineEdit("kana")
        self._kanji_flag = QLineEdit("kanji")
        self._phrase_flag = QLineEdit("phrase")

        # ----- Column mapping controls -----
        self._kana_kana_col = QComboBox()
        self._kana_romaji_col = QComboBox()

        self._kanji_kanji_col = QComboBox()
        self._kanji_onyomi_col = QComboBox()
        self._kanji_kunyomi_col = QComboBox()
        self._kanji_meaning_col = QComboBox()

        self._phrase_kanji_col = QComboBox()
        self._phrase_kana_col = QComboBox()
        self._phrase_grammar_col = QComboBox()
        self._phrase_meaning_col = QComboBox()

        # ---- Layout top row ----
        top = QHBoxLayout()
        top.addWidget(self._open_btn)
        top.addWidget(self._clear_btn)
        top.addWidget(self._process_btn)
        top.addStretch(1)

        # classification / flags group
        flags_box = QGroupBox("Row classification (optional)")
        flags_form = QFormLayout(flags_box)
        flags_form.setContentsMargins(8, 8, 8, 8)

        self._use_flag_mode = QCheckBox("Use type column + flags")
        self._use_flag_mode.setChecked(True)
        self._use_flag_mode.toggled.connect(self._on_mode_toggle)

        self._single_type_cb = QComboBox()
        self._single_type_cb.addItems(["KanaCard", "KanjiCard", "PhraseCard"])
        self._single_type_cb.setEnabled(False)
        self._single_type_cb.currentIndexChanged.connect(self._recompute_types)

        flags_form.addRow(self._use_flag_mode)
        flags_form.addRow("Single type:", self._single_type_cb)
        flags_form.addRow("Type column:", self._type_col_cb)

        en_row = QHBoxLayout()
        en_row.addWidget(self._kana_enabled)
        en_row.addWidget(self._kanji_enabled)
        en_row.addWidget(self._phrase_enabled)
        en_row.addStretch(1)
        flags_form.addRow("Enabled types:", en_row)

        flags_form.addRow("Kana flag:", self._kana_flag)
        flags_form.addRow("Kanji flag:", self._kanji_flag)
        flags_form.addRow("Phrase flag:", self._phrase_flag)

        # mapping group
        map_box = QGroupBox("Column mapping")
        map_form = QFormLayout(map_box)
        map_form.setContentsMargins(8, 8, 8, 8)

        kana_row = QHBoxLayout()
        kana_row.addWidget(QLabel("kana:"))
        kana_row.addWidget(self._kana_kana_col)
        kana_row.addSpacing(12)
        kana_row.addWidget(QLabel("romaji:"))
        kana_row.addWidget(self._kana_romaji_col)
        kana_row.addStretch(1)
        map_form.addRow("KanaCard:", kana_row)

        kanji_row = QHBoxLayout()
        kanji_row.addWidget(QLabel("kanji:"))
        kanji_row.addWidget(self._kanji_kanji_col)
        kanji_row.addSpacing(12)
        kanji_row.addWidget(QLabel("onyomi:"))
        kanji_row.addWidget(self._kanji_onyomi_col)
        kanji_row.addSpacing(12)
        kanji_row.addWidget(QLabel("kunyomi:"))
        kanji_row.addWidget(self._kanji_kunyomi_col)
        kanji_row.addSpacing(12)
        kanji_row.addWidget(QLabel("meaning:"))
        kanji_row.addWidget(self._kanji_meaning_col)
        kanji_row.addStretch(1)
        map_form.addRow("KanjiCard:", kanji_row)

        phrase_row = QHBoxLayout()
        phrase_row.addWidget(QLabel("kanji:"))
        phrase_row.addWidget(self._phrase_kanji_col)
        phrase_row.addSpacing(12)
        phrase_row.addWidget(QLabel("kana:"))
        phrase_row.addWidget(self._phrase_kana_col)
        phrase_row.addSpacing(12)
        phrase_row.addWidget(QLabel("grammar:"))
        phrase_row.addWidget(self._phrase_grammar_col)
        phrase_row.addSpacing(12)
        phrase_row.addWidget(QLabel("meaning:"))
        phrase_row.addWidget(self._phrase_meaning_col)
        phrase_row.addStretch(1)
        map_form.addRow("PhraseCard:", phrase_row)

        self._status_lbl = QLabel("")
        self._status_lbl.setWordWrap(True)

        # table
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        hh = self._table.horizontalHeader()
        if hh is not None:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            hh.setStretchLastSection(True)
        vh = self._table.verticalHeader()
        if vh is not None:
            vh.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self._path_lbl)
        layout.addWidget(flags_box)
        layout.addWidget(map_box)
        layout.addWidget(self._status_lbl)
        layout.addWidget(self._table, 1)

        # ----- Signals -----
        self._open_btn.clicked.connect(self._on_open)
        self._clear_btn.clicked.connect(self._on_clear)
        self._process_btn.clicked.connect(self._on_process)

        self._type_col_cb.currentIndexChanged.connect(self._recompute_types)

        self._kana_enabled.toggled.connect(self._on_type_toggle)
        self._kanji_enabled.toggled.connect(self._on_type_toggle)
        self._phrase_enabled.toggled.connect(self._on_type_toggle)

        self._kana_flag.textChanged.connect(self._recompute_types)
        self._kanji_flag.textChanged.connect(self._recompute_types)
        self._phrase_flag.textChanged.connect(self._recompute_types)

        for cb in (
            self._kana_kana_col, self._kana_romaji_col,
            self._kanji_kanji_col, self._kanji_onyomi_col, self._kanji_kunyomi_col, self._kanji_meaning_col,
            self._phrase_kanji_col, self._phrase_kana_col, self._phrase_grammar_col, self._phrase_meaning_col,
        ):
            cb.currentIndexChanged.connect(self._recompute_types)

        self._set_controls_enabled(False)
        self._apply_type_enabled_state()
        self._on_mode_toggle()
