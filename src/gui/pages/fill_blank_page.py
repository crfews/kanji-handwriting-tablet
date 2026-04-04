from __future__ import annotations

from typing import Optional

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

from data import Drawing, KanaCard, KanjiCard
from gui.widgets.drawing_display import DrawingDisplay
from gui.widgets.writing_widgets import CharacterDrawing
from logic.grade_handwriting import grade_strokes
from logic.LLM_fill_blank import FillBlankExercise, generate_fill_blank_exercise


def _set_grade_badge(lbl: QtWidgets.QLabel, grade: int) -> None:
    if grade == 0:
        lbl.setText("Correct, continue to the next one!")
        lbl.setStyleSheet("font-size: 24px; color: #2e7d32;")
    elif grade == 1:
        lbl.setText("Close — try again.")
        lbl.setStyleSheet("font-size: 24px; color: #f9a825;")
    else:
        lbl.setText("Incorrect — try again. Use Reveal to compare stroke order.")
        lbl.setStyleSheet("font-size: 24px; color: #c62828;")


class _ExerciseLoader(QtCore.QThread):
    loaded = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def run(self) -> None:
        try:
            exercise = generate_fill_blank_exercise()
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.loaded.emit(exercise)


def _lookup_answer_strokes(glyph: str) -> list[list[float]] | None:
    kana = KanaCard.by_kana(glyph)
    if kana is not None and kana.drawing is not None and kana.drawing.strokes:
        return kana.drawing.strokes

    kanji = KanjiCard.by_kanji(glyph)
    if kanji is not None and kanji.drawing is not None and kanji.drawing.strokes:
        return kanji.drawing.strokes

    drawings = Drawing.by_glyph(glyph)
    if drawings:
        sample = next(iter(drawings.values()))
        if sample.strokes:
            return sample.strokes

    return None


class FillBlankPracticePage(QtWidgets.QWidget):
    """OpenAI-backed fill-in-the-blank page with handwriting input and animated reveal."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current: Optional[FillBlankExercise] = None
        self._last_grade: Optional[int] = None
        self._loader: Optional[_ExerciseLoader] = None

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self.page_stack = QtWidgets.QStackedWidget(self)
        root.addWidget(self.page_stack, 1)

        self.content_page = QtWidgets.QWidget(self.page_stack)
        content_root = QtWidgets.QVBoxLayout(self.content_page)
        content_root.setSpacing(12)

        subtitle = QtWidgets.QLabel(
            "Draw the missing kana or kanji. "
            "Use Reveal to watch the correct stroke animation.",
            self.content_page,
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setWordWrap(True)

        self.sentence_label = QtWidgets.QLabel("Press 'Next Question' to begin.", self.content_page)
        self.sentence_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.sentence_label.setWordWrap(True)
        sentence_font = self.sentence_label.font()
        sentence_font.setPointSize(32)
        sentence_font.setBold(True)
        self.sentence_label.setFont(sentence_font)

        self.meaning_label = QtWidgets.QLabel("", self.content_page)
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.meaning_label.setWordWrap(True)

        self.hint_label = QtWidgets.QLabel("", self.content_page)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.hint_label.setWordWrap(True)

        self.badge_label = QtWidgets.QLabel("", self.content_page)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.badge_label.setWordWrap(True)

        panels = QtWidgets.QHBoxLayout()
        panels.setSpacing(12)

        left_box = QtWidgets.QGroupBox("Reveal correct drawing", self.content_page)
        left_layout = QtWidgets.QVBoxLayout(left_box)
        left_layout.setSpacing(8)

        self.reveal_info_label = QtWidgets.QLabel(
            "Click Reveal Answer to draw the correct character animation.",
            left_box,
        )
        self.reveal_info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.reveal_info_label.setWordWrap(True)
        left_layout.addWidget(self.reveal_info_label)

        self.canonical_display = DrawingDisplay(parent=left_box, width=320, height=320)
        left_layout.addWidget(self.canonical_display, 1)

        rep_row = QtWidgets.QHBoxLayout()
        rep_row.addWidget(QtWidgets.QLabel("Animation Slider", left_box))
        self.representation_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal, left_box)
        self.representation_slider.setRange(0, 100)
        self.representation_slider.setEnabled(False)
        self.representation_slider.valueChanged.connect(self._on_representation_changed)
        rep_row.addWidget(self.representation_slider, 1)
        self.representation_label = QtWidgets.QLabel("0%", left_box)
        rep_row.addWidget(self.representation_label)
        left_layout.addLayout(rep_row)

        self.replay_btn = QtWidgets.QPushButton("Replay animation", left_box)
        self.replay_btn.setEnabled(False)
        self.replay_btn.clicked.connect(self._replay_canonical)
        left_layout.addWidget(self.replay_btn)

        right_box = QtWidgets.QGroupBox("Your drawing", self.content_page)
        right_layout = QtWidgets.QVBoxLayout(right_box)
        right_layout.setSpacing(8)

        self.drawing = CharacterDrawing(
            parent=right_box,
            on_submitted=self._on_drawing_submitted,
            on_cleared=self._on_cleared,
        )
        right_layout.addWidget(self.drawing, 1)

        panels.addWidget(left_box, 1)
        panels.addWidget(right_box, 1)

        action_row = QtWidgets.QHBoxLayout()
        self.reveal_btn = QtWidgets.QPushButton("Reveal Answer", self.content_page)
        self.reveal_btn.clicked.connect(self.reveal_answer)

        self.generate_btn = QtWidgets.QPushButton("Next Question", self.content_page)
        self.generate_btn.clicked.connect(self.generate_question)

        action_row.addWidget(self.reveal_btn)
        action_row.addWidget(self.generate_btn)

        self.full_sentence_label = QtWidgets.QLabel("", self.content_page)
        self.full_sentence_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.full_sentence_label.setWordWrap(True)

        content_root.addWidget(subtitle)
        content_root.addSpacing(8)
        content_root.addWidget(self.sentence_label)
        content_root.addWidget(self.meaning_label)
        content_root.addWidget(self.hint_label)
        content_root.addWidget(self.badge_label)
        content_root.addLayout(panels, 1)
        content_root.addLayout(action_row)
        content_root.addWidget(self.full_sentence_label)
        content_root.addStretch()

        self.loading_page = QtWidgets.QWidget(self.page_stack)
        loading_root = QtWidgets.QVBoxLayout(self.loading_page)
        loading_root.setSpacing(16)
        loading_root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loading_label = QtWidgets.QLabel("Preparing your next fill-in-the-blank...", self.loading_page)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.loading_label.setWordWrap(True)
        loading_font = self.loading_label.font()
        loading_font.setPointSize(20)
        loading_font.setBold(True)
        self.loading_label.setFont(loading_font)

        self.loading_bar = QtWidgets.QProgressBar(self.loading_page)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setMinimumWidth(260)

        loading_root.addWidget(self.loading_label)
        loading_root.addWidget(self.loading_bar)

        self.page_stack.addWidget(self.content_page)
        self.page_stack.addWidget(self.loading_page)
        self.page_stack.setCurrentWidget(self.content_page)

        self._reset_reveal_panel()

    def showEvent(self, a0) -> None:
        super().showEvent(a0)
        if self._current is None and self._loader is None:
            self.generate_question()

    def _set_feedback(self, text: str, color: str = "#333333") -> None:
        self.badge_label.setText(text)
        self.badge_label.setStyleSheet(f"font-size: 24px; color: {color};")

    def _set_info(self, text: str, color: str = "#333333") -> None:
        self.reveal_info_label.setText(text)
        self.reveal_info_label.setStyleSheet(f"color: {color};")

    def _reset_reveal_panel(self) -> None:
        self._set_info("Click Reveal Answer to draw the correct character animation.")
        self.canonical_display.clear()
        self.representation_slider.blockSignals(True)
        self.representation_slider.setValue(0)
        self.representation_slider.blockSignals(False)
        self.representation_slider.setEnabled(False)
        self.representation_label.setText("0%")
        self.replay_btn.setEnabled(False)

    def _begin_loading(self) -> None:
        self.generate_btn.setEnabled(False)
        self.reveal_btn.setEnabled(False)
        self.loading_label.setText("Loading...")
        self.page_stack.setCurrentWidget(self.loading_page)

    def _finish_loading(self) -> None:
        self.generate_btn.setEnabled(True)
        self.reveal_btn.setEnabled(self._current is not None)
        self.page_stack.setCurrentWidget(self.content_page)

    def _load_reveal_animation(self) -> bool:
        if self._current is None:
            return False

        strokes = _lookup_answer_strokes(self._current.answer)
        if not strokes:
            self._reset_reveal_panel()
            self._set_info(
                f"Answer: {self._current.answer} (no saved canonical drawing found for animation).",
                "#b26a00",
            )
            return False

        self.canonical_display.set_strokes(strokes)
        self.canonical_display.set_progress(0.0)
        self.representation_slider.blockSignals(True)
        self.representation_slider.setValue(0)
        self.representation_slider.blockSignals(False)
        self.representation_slider.setEnabled(True)
        self.representation_label.setText("0%")
        self.replay_btn.setEnabled(True)
        self._set_info(f"Revealed answer: {self._current.answer}", "#1f4e79")
        self.canonical_display.restart()
        return True

    @QtCore.pyqtSlot()
    def generate_question(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            return

        self._current = None
        self._last_grade = None
        self._set_feedback("")
        self.full_sentence_label.setText("")
        self.drawing.force_clear()
        self._reset_reveal_panel()
        self._begin_loading()

        self._loader = _ExerciseLoader(self)
        self._loader.loaded.connect(self._on_question_loaded)
        self._loader.failed.connect(self._on_question_failed)
        self._loader.finished.connect(self._on_loader_finished)
        self._loader.start()

    def _on_question_loaded(self, exercise: object) -> None:
        self._current = exercise if isinstance(exercise, FillBlankExercise) else None
        if self._current is None:
            self._on_question_failed("Invalid exercise returned.")
            return

        self._last_grade = None
        self.badge_label.setText("")
        self.badge_label.setStyleSheet("")
        self.drawing.force_clear()
        self._reset_reveal_panel()
        self.sentence_label.setText(self._current.blanked_sentence)
        self.meaning_label.setText(
            f"Meaning: {self._current.english_meaning}" if self._current.english_meaning else ""
        )
        self.hint_label.setText(f"Hint: {self._current.hint}" if self._current.hint else "")
        self.full_sentence_label.setText("")

    def _on_question_failed(self, message: str) -> None:
        self._current = None
        self.sentence_label.setText("Unable to build a fill-in-the-blank question right now.")
        self.meaning_label.setText("")
        self.hint_label.setText("")
        self.full_sentence_label.setText("")
        self._reset_reveal_panel()
        self._set_feedback(message or "Please try again.", "#b00020")

    def _on_loader_finished(self) -> None:
        self._finish_loading()
        if self._loader is not None:
            self._loader.deleteLater()
            self._loader = None

    def _on_drawing_submitted(self, drawing: list[list[float]]) -> None:
        if self._current is None:
            self._set_feedback("Generate a question first.", "#b26a00")
            return

        if not drawing or not any(stroke for stroke in drawing):
            self._set_feedback("Draw the missing character first.", "#b26a00")
            return

        try:
            grade = grade_strokes(drawing, self._current.answer)
        except Exception as exc:
            self._set_feedback(f"Could not grade this drawing: {exc}", "#b00020")
            self.drawing.force_clear()
            return

        self._last_grade = grade
        _set_grade_badge(self.badge_label, grade)

        if grade == 0:
            self.full_sentence_label.setText(
                f"Answer: {self._current.answer}   •   Full sentence: {self._current.sentence}"
            )
        elif grade == 1:
            self.full_sentence_label.setText("")
            self.drawing.force_clear()
        else:
            self.full_sentence_label.setText("")
            self.drawing.force_clear()

    def _on_cleared(self) -> None:
        return

    def _replay_canonical(self) -> None:
        if not self.replay_btn.isEnabled():
            return

        self.representation_slider.blockSignals(True)
        self.representation_slider.setValue(0)
        self.representation_slider.blockSignals(False)
        self.representation_label.setText("0%")
        self.canonical_display.set_progress(0.0)
        self.canonical_display.restart()

    def _on_representation_changed(self, value: int) -> None:
        pct = max(0, min(100, int(value)))
        self.representation_label.setText(f"{pct}%")
        self.canonical_display.set_progress(pct / 100.0)

    @QtCore.pyqtSlot()
    def reveal_answer(self) -> None:
        if self._current is None:
            return

        self.full_sentence_label.setText(
            f"Answer: {self._current.answer}   •   Full sentence: {self._current.sentence}"
        )
        self._load_reveal_animation()


FillBlankPracticeWidget = FillBlankPracticePage
