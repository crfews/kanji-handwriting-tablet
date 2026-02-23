# Review & Scheduler
# Peyton McCade Moore
# The review page that prompts user with cards that are ready to be reviewed
#   today and also modifies the next instance of when that card will be seen

from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox,QInputDialog, QLineEdit, QLabel
from PyQt6.QtCore import Qt
from data import KanaCard
from data.database import maybe_connection
from typing import Iterator, Optional
from functools import partial
from datetime import datetime, timedelta



GOOD = 1    # Increase 0->1 day, 1->3days, etc
OK = -1     # Decrease 3->1day, 1->0days, etc
BAD = 0    # Restart, Due/study today
# SRS Incrementation(1 day, 3 days, 1 week, 2 weeks, 1 month, 3 months, 6 months, 1 year)
DAYS_INCREMENT = [0, 1, 3, 7, 14, 30, 90, 180, 365]
CURRENT_DATE = datetime.now().today()

cards = {'name': "test", 'due_date_increment': 0, 'due_date': 0}

class ReviewScheduler(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ------ Add button/textBox to switch between what card to review that are due today -----#
        # EX: pick KanaCard | KanjiCard | PhraseCard -> Optional[Iterator]
        CardType = KanaCard 
        text = "KanaCard"
        #-----Using Learn_kana.py session layout to test-----#
        self._it: Optional[Iterator[CardType]] = None
        self._current: Optional[CardType] = None
        
        
        if self._it is None: 
            with maybe_connection(None) as con:
                if (text == "KanaCard"):
                    from data.queries import query_reviewable_kana_card
                    self._it = iter(list(query_reviewable_kana_card(con)))
        self._current = next(self._it)

        root = QVBoxLayout(self)
        root.setSpacing(12)
        
        self.kana_label = QLabel("", self)
        self.kana_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.kana_label.font()
        f.setPointSize(64)
        f.setBold(True)
        self.kana_label.setFont(f)

        self.romaji_label = QLabel("", self)
        self.romaji_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        
        root.addWidget(self.kana_label)
        root.addWidget(self.romaji_label)
        root.addWidget(self.status_label)
        
        # -------Original Review------- #
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._render_current() # Print out card information
    
        #replace these inputs for the rating of correctness for given kana/kanji/phrase card
        #---------------------------------------------#
        button1 = QPushButton("I know it",self)
        button2 = QPushButton("I kinda know it",self)
        button3 = QPushButton("I don't know it",self)
        #---------------------------------------------#
        
        # Connect to scheduler function, perform SRS depending on what button clicked
        button1.clicked.connect(lambda: self.scheduler("good"))
        button2.clicked.connect(lambda: self.scheduler("ok"))
        button3.clicked.connect(lambda: self.scheduler("bad"))

        # Add Buttons to Widget in Horizontal Box Layout
        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)
        root.addLayout(layout) 
        
    def scheduler(self,button_data):
        current_card = self._current

        if button_data == "good":
            # Push back due_date_increment & push due_date back based on new increment
            print(f"before:  {current_card.card.due_date_increment}")
            current_card.card.due_date_increment += GOOD
            print(f"after: {current_card.card.due_date_increment}")   
            inc = current_card.card.due_date_increment
            
            if inc >= 9: 
                inc = 0
                current_card.card.due_date_increment = inc
            
            current_card.card.due_date_increment = inc
            current_card.card.due_date = self.add_dates(inc)

            msg = f"Review Due Date: {current_card.card.due_date}"
        elif button_data == "ok":
            # Leave the same due_date_increment, push back due_date
            print(f"before: {current_card.card.due_date_increment}")
            inc = current_card.card.due_date_increment
            current_card.card.due_date = self.add_dates(inc)
            print(f"after: {current_card.card.due_date_increment}")

            msg = f"Pushed due date forward, Increment: {current_card.card.due_date_increment}, Due: {current_card.card.due_date}"
        elif button_data == "bad":
            # Card due_date_increment is reset and due_date is reset to today
            print(f"ebfore: {current_card.card.due_date_increment}")
            inc = current_card.card.due_date_increment = BAD
            current_card.card.due_date = datetime.today()
            print(f"afrter: {current_card.card.due_date_increment}")

            msg = f"Need to be Restudied, Increment: {current_card.card.due_date_increment}, Due: {current_card.card.due_date}"

        msg_box = QMessageBox(self)
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        reply = msg_box.exec()
        
        self._current.sync()
        
        try:
            #self._current.sync()
            self._current = next(self._it) # this one
            self._render_current()
        except:
            QMessageBox.information(self, "Done", "No More Cards.")

    # Change the due dates of due_date field in card class
    # @params:
    #   inc - how many days to increment by(from card class[due_date_increment])
    def add_dates(self, inc):
        return (datetime.today() + timedelta(days=DAYS_INCREMENT[inc])).date() #SQLite Date Python required
    
    # Print Card Information
    def _render_current(self) -> None: 
        assert self._current is not None
        self.kana_label.setText(getattr(self._current, "kana", "") or "")
        self.romaji_label.setText(getattr(self._current, "romaji", "") or "")
        self.status_label.setText("Click Option")
