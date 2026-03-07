from kivy.app import App
from kivy.uix.label import Label

class NiftyHeatmapApp(App):
    def build(self):
        return Label(text='Hello from Nifty Heatmap!')

if __name__ == '__main__':
    NiftyHeatmapApp().run()
