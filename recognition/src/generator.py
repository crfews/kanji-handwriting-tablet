from random import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.input.motionevent import MotionEvent
import stroke_processor as sp


# GLOBALS #####################################################################

DB_FILE_NAME = 'sqlite.db'
DB_CURSOR = None
KANJI_TO_ADD_FILE = 'kanji_to_add.txt'

# FUNCTION DEFINITIONS ########################################################

# CLASS DEFINITIONS ###########################################################


class PaintWidget(Widget):
    lines = []

    def on_touch_down(self, touch: MotionEvent):
        color = (random(), 1, 1)

        with self.canvas:
            Color(*color, mode='hsv')
            Ellipse(pos=(touch.x - 5 / 2, touch.y - 5 / 2), size=(5, 5))
            self.lines.append(Line(points=(touch.x, touch.y)))

    def on_touch_move(self, touch):
        self.lines[-1].points += [touch.x, touch.y]

    def reset(self):
        self.canvas.clear()
        self.lines = []

    def get_lines(self):
        return [line.points for line in self.lines]

class MyPaintApp(App):
    parent = None
    characters = []
    textinput = None
    painter = None
    clearbtn = None
    submitbtn = None

    def build(self):
        self.parent = Widget()
        # self.take_character()
        with open(KANJI_TO_ADD_FILE, 'r') as ifile:
            self.characters = ifile.read()
            self.characters = self.characters.replace('\n', '')
            self.characters = self.characters.replace('\t', '')
            self.characters = self.characters.replace(' ', '')
        print('with characters:')
        for c in self.characters:
            print(f'\t{c}')
        self.take_drawing()
        return self.parent

    def take_drawing(self):
        if len(self.characters) > 0:
            print(f'draw {self.characters[0]}')
        else:
            print('No characters to draw')
        self.painter = PaintWidget()
        self.clearbtn = Button(text='Clear')
        self.clearbtn.bind(on_release=self.clear_canvas)
        self.submitbtn = Button(text='Submit')
        self.submitbtn.bind(on_release=self.submit_canvas)
        self.parent.add_widget(self.painter)
        self.parent.add_widget(self.clearbtn)
        self.parent.add_widget(self.submitbtn)

    def clear_canvas(self, _):
        assert self.painter is not None
        self.painter.reset()

    def submit_canvas(self, _):
        assert self.painter is not None

        if len(self.characters) > 0:
            strokes = self.painter.get_lines()
            sp.shelve_char(self.characters[0], strokes, override=True)
            self.characters = self.characters[1:]
            with open(KANJI_TO_ADD_FILE, 'w') as ofile:
                ofile.write('\n'.join(self.characters))

        self.painter.reset()


# SCRIPT ENTRY POINT ##########################################################

if __name__ == '__main__':
    MyPaintApp().run()
    pass
