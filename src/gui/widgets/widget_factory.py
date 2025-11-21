# PyQt Widget Factory and Controller (Basic Design)

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QProgressBar
)
from PyQt6.QtGui import QFont


class Card:
    """Generic card with type, prompt, answer, hints."""
    def __init__(self, card_type, prompt, answer, hints=None):
        self.card_type = card_type
        self.prompt = prompt
        self.answer = answer
        self.hints = hints or []


class CharacterQuestionWidget(QWidget):
    def __init__(self, card, on_submit):
        super().__init__()
        layout = QVBoxLayout(self)

        label = QLabel(f"Character: {card.prompt}")
        label.setFont(QFont("Arial", 24))
        layout.addWidget(label)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(on_submit)
        layout.addWidget(self.submit_button)

        # Optional hints
        for hint in card.hints:
            hlabel = QLabel(f"Hint: {hint}")
            hlabel.setStyleSheet("color: gray;")
            layout.addWidget(hlabel)



class CharacterAnswerWidget(QWidget):
    def __init__(self, card, user_correct):
        super().__init__()
        layout = QVBoxLayout(self)

        result_label = QLabel("Correct!" if user_correct else "Incorrect")
        result_label.setFont(QFont("Arial", 20))
        result_label.setStyleSheet(
            "color: green;" if user_correct else "color: red;"
        )

        layout.addWidget(result_label)

        answer_label = QLabel(f"Correct answer: {card.answer}")
        answer_label.setFont(QFont("Arial", 18))
        layout.addWidget(answer_label)



class WidgetFactory:
    @staticmethod
    def create_question_widget(card, on_submit):
        if card.card_type == "character":
            return CharacterQuestionWidget(card, on_submit)
        else:
            raise ValueError(f"Unknown card type: {card.card_type}")

    @staticmethod
    def create_answer_widget(card, user_correct):
        if card.card_type == "character":
            return CharacterAnswerWidget(card, user_correct)
        else:
            raise ValueError(f"Unknown card type: {card.card_type}")


class CardController(QWidget):
    def __init__(self, stacked_widget, progress_bar):
        super().__init__()
        self.stacked = stacked_widget
        self.progress = progress_bar

        self.current_card = None
        self.user_correct = False

    def load_card(self, card):
        self.current_card = card

        question_widget = WidgetFactory.create_question_widget(
            card, self.handle_submit
        )
        self.stacked.addWidget(question_widget)
        self.stacked.setCurrentWidget(question_widget)

    def handle_submit(self):
        # Here you would normally check the user's answer.
        # For now, assume correct for demo.
        self.user_correct = True

        answer_widget = WidgetFactory.create_answer_widget(
            self.current_card, self.user_correct
        )
        self.stacked.addWidget(answer_widget)
        self.stacked.setCurrentWidget(answer_widget)

        # Update progress
        value = self.progress.value() + 10
        self.progress.setValue(value)


