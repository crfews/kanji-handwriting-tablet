from PyQt6.QtCore import QMargins
from PyQt6.QtWidgets import QWidget, QFormLayout, QLineEdit, QTabWidget, QMessageBox, QLabel, QVBoxLayout
from gui.widgets.writing_widgets import CharacterDrawing
from recognition import stroke_processor as sp


class AddUpdateCharacterTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        form = QFormLayout()
        self.line_edit = QLineEdit(self)
        self.line_edit.setMaxLength(1)
        form.addRow('Character:', self.line_edit)
        character_drawing = CharacterDrawing(self)
        character_drawing.setContentsMargins(QMargins(30, 60, 30, 60))
        character_drawing.submitted.connect(self._on_submit)
        form.addRow(character_drawing)
        self.setLayout(form)

    def _on_submit(self, strokes: list[list[float]]) -> None:
        char = self.line_edit.text()

        error = False
        msg = ""
        if len(char) != 1:
            error = True
            msg = "'Character' field left empty\n"
        if len(strokes) < 1:
            msg += "Canvas must contain atleast one stroke\n"
            
                
        if error is False:
            print(self.line_edit.text())
            sp.add_character(char, strokes)
        else:
            msg += "drawing not submitted"
            QMessageBox.warning(self, "Warning", msg)
            

class TestCharacterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.char_label = QLabel(self)
        self.char_label.setText('')
        layout.addWidget(self.char_label)

        self.character_drawing = CharacterDrawing(self)
        self.character_drawing.setContentsMargins(QMargins(30, 60, 30, 60))
        self.character_drawing.submitted.connect(self._on_submit)
        layout.addWidget(self.character_drawing)


    def _on_submit(self, strokes: list[list[float]]) -> None:
        error = False
        msg = ""

        found_char = sp.search_strokes(strokes)

        if found_char is None:
            error = True
            msg = "No similar character found"
            QMessageBox.warning(self, "Warning", msg)
        else:
            self.char_label.setText(found_char)


class HandwritingManager(QTabWidget):

    _tab = None
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tab1 = AddUpdateCharacterTab(self)
        self.tab2 = TestCharacterTab(self)

        self.addTab(self.tab1, "Add/Update Character")
        self.addTab(self.tab2, "Test Character")
