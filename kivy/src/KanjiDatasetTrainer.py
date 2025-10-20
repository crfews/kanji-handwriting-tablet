import time
from random import random
from kivy.app import App
from kivy.config import Config
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.input.postproc.dejitter import InputPostprocDejitter


class MyPaintWidget(Widget):

    def on_touch_down(self, touch):
        color = (random(), 1, 1)
        with self.canvas:
            d = 30.0
            Color(*color, mode='hsv')
            self.avg_x = touch.x
            self.avg_y = touch.y
            self.touch_down_time = time.perf_counter()
            touch.ud['line'] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        self.avg_x = int((self.avg_x + touch.x) / 2)
        self.avg_y = int((self.avg_y + touch.y) / 2)
        if 'line' in touch.ud.keys():
            touch.ud['line'].points += [self.avg_x, self.avg_y]


class MyPaintApp(App):

    def build_config(self, config):
        config.setdefaults('postproc', {
            'jitter_distance': '1.000',
            'retain_time': '500',
            'retain_distance': '200'
        })

    def build(self):
        parent = Widget()
        self.painter = MyPaintWidget()
        parent.add_widget(self.painter)
        clearbtn = Button(text='Submit')
        clearbtn.bind(on_release=self.submit_character)
        parent.add_widget(clearbtn)
        return parent
    
    def submit_character(self, obj):
        print(Line.points)
    


if __name__ == '__main__':
    MyPaintApp().run()