from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QMessageBox
from functools import partial


GOOD = 1    # Increase 0->1 day, 1->3days, etc
OK = -1     # Decrease 3->1day, 1->0days, etc
BAD = 0    # Restart, Due/study today
# SRS Incrementation(1 day, 3 days, 1 week, 2 weeks, 1 month, 3 months, 6 months, 1 year)
DAYS_INCREMENT = [0, 1, 3, 7, 14, 30, 90, 180, 365]

cards = {'name': "test", 'due_date_increment': 0, 'due_date': 0}

class ReviewScheduler(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Button Creation
        button1 = QPushButton("good",self)
        button2 = QPushButton("ok",self)
        button3 = QPushButton("bad",self)
        # Connect to scheduler function, perform SRS depending on what button clicked
        button1.clicked.connect(partial(self.scheduler,"good"))
        button2.clicked.connect(partial(self.scheduler,"ok"))
        button3.clicked.connect(partial(self.scheduler,"bad"))
        # Add Buttons to Widget in Horizontal Box Layout
        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)

    def scheduler(self,button_data):
        if button_data == "good":
            cards['due_date_increment'] += GOOD
            inc = cards['due_date_increment']
            
            if inc >= 9:
                inc = 0
                cards['due_date_increment'] = inc
                
                days = cards['due_date'] = DAYS_INCREMENT[inc]
                
                msg = f"Reached a year, Restarted Increment: {inc}, Due: {days}"
            else :
                days = cards['due_date'] = DAYS_INCREMENT[inc]
                
                msg = f"Pushed back, Increment: {inc}, Due: {days} days"
                
            msg_box = QMessageBox(self)
            msg_box.setText(msg)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

        elif button_data == "ok":
            # Leave the same position or push back half ? as long as good
            cards['due_date_increment'] += OK
            inc = cards['due_date_increment']
            
            if inc < 0:
                inc = 0

            days = cards['due_date'] = DAYS_INCREMENT[inc]

            msg = f"Pushed forward, Increment: {inc}, Due: {days} days"

            msg_box = QMessageBox(self)
            msg_box.setText(msg)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        elif button_data == "bad":
            # Push up when the card will be seen again
            inc = cards['due_date_increment'] = BAD
            days = cards['due_date'] = DAYS_INCREMENT[0]
            
            msg = f"Need to be Restudied, Increment: {inc}, Due: {days} days"
            
            msg_box = QMessageBox(self)
            msg_box.setText(msg)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

        reply = msg_box.exec() 
