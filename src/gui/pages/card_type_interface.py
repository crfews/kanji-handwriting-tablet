# card_type_widgets.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QGroupBox, QFormLayout, QRadioButton, QButtonGroup, QSpinBox,
    QMessageBox, QFrame
)

# Import your DB helpers (exact names as in database.py)
from data.database import (
    get_all_card_types_with_field_types,
    add_card_type,
    add_field_type,
)

# ---------------------------
# Read-only viewer
# ---------------------------
class CardTypesViewer(QWidget):
    """List all card types on the left, show their field types on the right."""
    refreshed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Card Types Viewer")

        root = QHBoxLayout(self)

        # Left: card types list
        left = QVBoxLayout()
        left.addWidget(QLabel("Card Types:", self))
        self.types_list = QListWidget(self)
        self.refresh_btn = QPushButton("Refresh", self)
        left.addWidget(self.types_list)
        left.addWidget(self.refresh_btn)

        # Right: fields table
        right = QVBoxLayout()
        right.addWidget(QLabel("Field Types:", self))
        self.fields_table = QTableWidget(self)
        self.fields_table.setColumnCount(4)
        self.fields_table.setHorizontalHeaderLabels(["Field Name", "is_text", "is_int", "is_pickle"])
        #self.fields_table.horizontalHeader().setStretchLastSection(True)
        right.addWidget(self.fields_table)

        root.addLayout(left, 1)
        root.addLayout(right, 2)

        self.refresh_btn.clicked.connect(self.load_data)
        self.types_list.currentItemChanged.connect(self._on_type_selected)

        self._cache = {}  # {card_type_name: {field_name: {...}}}
        self.load_data()

    def load_data(self):
        try:
            self._cache = get_all_card_types_with_field_types()  # {name: {field_name: flags}}
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load card types:\n{e}")
            return

        self.types_list.clear()
        for ct_name in sorted(self._cache.keys()):
            QListWidgetItem(ct_name, self.types_list)

        self.fields_table.setRowCount(0)
        self.refreshed.emit()

    def _on_type_selected(self, current: QListWidgetItem, _prev: QListWidgetItem):
        self.fields_table.setRowCount(0)
        if not current:
            return

        ct_name = current.text()
        field_map = self._cache.get(ct_name, {})
        self.fields_table.setRowCount(len(field_map))
        for r, (fname, flags) in enumerate(sorted(field_map.items())):
            self.fields_table.setItem(r, 0, QTableWidgetItem(fname))
            self.fields_table.setItem(r, 1, QTableWidgetItem("True" if flags["is_text"] else "False"))
            self.fields_table.setItem(r, 2, QTableWidgetItem("True" if flags["is_int"] else "False"))
            self.fields_table.setItem(r, 3, QTableWidgetItem("True" if flags["is_pickle"] else "False"))
        self.fields_table.resizeColumnsToContents()


# ---------------------------
# Editor (create new type + fields)
# ---------------------------
class FieldRow(QWidget):
    """One row in the 'new field types' editor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        fl = QHBoxLayout(self)
        fl.setContentsMargins(0, 0, 0, 0)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("field name")

        # Exactly one of these must be selected
        self.text_rb = QRadioButton("text", self)
        self.int_rb = QRadioButton("int", self)
        self.pickle_rb = QRadioButton("pickle", self)
        self.text_rb.setChecked(True)

        grp = QButtonGroup(self)
        grp.setExclusive(True)
        grp.addButton(self.text_rb)
        grp.addButton(self.int_rb)
        grp.addButton(self.pickle_rb)

        fl.addWidget(self.name_edit, 2)
        fl.addWidget(self.text_rb)
        fl.addWidget(self.int_rb)
        fl.addWidget(self.pickle_rb)

    def value(self):
        """Return (name, is_text, is_int, is_pickle) or None if invalid."""
        name = self.name_edit.text().strip()
        if not name:
            return None
        return (
            name,
            self.text_rb.isChecked(),
            self.int_rb.isChecked(),
            self.pickle_rb.isChecked(),
        )


class CardTypeEditor(QWidget):
    """
    Create a new card type and its field types.

    * Enter the card type name.
    * Add N field rows; for each, set the name and choose text/int/pickle.
    * Click 'Create' to persist via add_card_type(...) and add_field_type(...).
    """
    created = pyqtSignal(str)  # emits the card type name that was created

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Card Type Editor")

        root = QVBoxLayout(self)

        # Card type name
        form_box = QGroupBox("New Card Type", self)
        form = QFormLayout(form_box)
        self.type_name_edit = QLineEdit(self)
        self.type_name_edit.setPlaceholderText("e.g. Vocabulary, Kanji, ...")
        form.addRow("Name:", self.type_name_edit)

        # Field rows
        fields_box = QGroupBox("Field Types", self)
        fields_layout = QVBoxLayout(fields_box)

        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(6)

        # Add initial 3 rows (tweakable)
        self._rows = []
        for _ in range(3):
            self._add_row()

        fields_layout.addLayout(self.rows_container)

        # Row controls
        controls = QHBoxLayout()
        add_row_btn = QPushButton("Add Field", self)
        rem_row_btn = QPushButton("Remove Field", self)
        controls.addWidget(add_row_btn)
        controls.addWidget(rem_row_btn)
        controls.addStretch()
        fields_layout.addLayout(controls)

        # Action buttons
        btns = QHBoxLayout()
        btns.addStretch()
        create_btn = QPushButton("Create", self)
        reset_btn = QPushButton("Reset", self)
        btns.addWidget(create_btn)
        btns.addWidget(reset_btn)

        # Layout all
        root.addWidget(form_box)
        root.addWidget(fields_box)
        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(line)
        root.addLayout(btns)

        # Signals
        add_row_btn.clicked.connect(self._add_row)
        rem_row_btn.clicked.connect(self._remove_row)
        reset_btn.clicked.connect(self._reset)
        create_btn.clicked.connect(self._create)

    def _add_row(self):
        row = FieldRow(self)
        self._rows.append(row)
        self.rows_container.addWidget(row)

    def _remove_row(self):
        if not self._rows:
            return
        row = self._rows.pop()
        row.setParent(None)
        row.deleteLater()

    def _reset(self):
        self.type_name_edit.clear()
        while self._rows:
            self._remove_row()
        for _ in range(3):
            self._add_row()

    def _create(self):
        ct_name = self.type_name_edit.text().strip()
        if not ct_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a card type name.")
            return

        # Collect valid rows
        collected = []
        for r in self._rows:
            val = r.value()
            if val is not None:
                collected.append(val)

        if not collected:
            QMessageBox.warning(self, "No Fields", "Please add at least one valid field type.")
            return

        try:
            # 1) Create card type
            ct_id = add_card_type(ct_name)

            # 2) Create field types
            for (fname, is_text, is_int, is_pickle) in collected:
                add_field_type(
                    card_type_id=ct_id,
                    name=fname,
                    is_text=is_text,
                    is_int=is_int,
                    is_pickle=is_pickle,
                )

        except Exception as e:
            QMessageBox.critical(self, "Database Error",
                                 "Failed to create card type/field types:\n\n"
                                 f"{e}")
            return

        QMessageBox.information(self, "Success",
                                f"Created card type '{ct_name}' with {len(collected)} field(s).")
        self.created.emit(ct_name)
        self._reset()


# ---------------------------
# Optional combo widget
# ---------------------------
class CardTypeManager(QWidget):
    """
    A composite widget that shows the list on the left and an editor on the right.
    When a new type is created, the viewer refreshes automatically.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Card Types — Manager")

        root = QHBoxLayout(self)
        self.viewer = CardTypesViewer(self)
        self.editor = CardTypeEditor(self)
        root.addWidget(self.viewer, 1)
        root.addWidget(self.editor, 1)

        self.editor.created.connect(lambda _name: self.viewer.load_data())
