import threading
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

try:
    import yfinance as yf
except ImportError:
    yf = None

# Nifty 50 tickers on Yahoo Finance
NIFTY50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "HCLTECH.NS",
    "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "BAJFINANCE.NS", "WIPRO.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "NESTLEIND.NS", "TECHM.NS",
    "M&M.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "JSWSTEEL.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "BPCL.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "INDUSINDBK.NS", "GRASIM.NS",
    "APOLLOHOSP.NS", "BRITANNIA.NS", "DIVISLAB.NS", "TATACONSUM.NS", "SBILIFE.NS",
    "HDFCLIFE.NS", "BAJAJ-AUTO.NS", "UPL.NS", "LTIM.NS", "HINDALCO.NS",
]

def get_short_name(ticker):
    return ticker.replace(".NS", "").replace("-", "")[:8]

def pct_to_color(pct):
    """Return RGBA color: green for positive, red for negative, grey for zero."""
    if pct is None:
        return (0.3, 0.3, 0.3, 1)
    if pct > 3:
        return (0.0, 0.6, 0.1, 1)
    elif pct > 1.5:
        return (0.1, 0.75, 0.2, 1)
    elif pct > 0:
        return (0.2, 0.85, 0.35, 1)
    elif pct == 0:
        return (0.4, 0.4, 0.4, 1)
    elif pct > -1.5:
        return (0.9, 0.25, 0.2, 1)
    elif pct > -3:
        return (0.78, 0.1, 0.1, 1)
    else:
        return (0.6, 0.0, 0.0, 1)


class StockTile(BoxLayout):
    def __init__(self, symbol, **kwargs):
        super().__init__(orientation='vertical', padding=2, spacing=1, **kwargs)
        self.symbol = symbol
        self.bg_color = (0.3, 0.3, 0.3, 1)

        with self.canvas.before:
            self.rect_color = Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)

        self.name_label = Label(
            text=get_short_name(symbol),
            font_size='11sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=0.4,
            halign='center',
            valign='middle',
        )
        self.name_label.bind(size=self.name_label.setter('text_size'))

        self.price_label = Label(
            text='---',
            font_size='10sp',
            color=(1, 1, 1, 0.9),
            size_hint_y=0.35,
            halign='center',
            valign='middle',
        )
        self.price_label.bind(size=self.price_label.setter('text_size'))

        self.pct_label = Label(
            text='',
            font_size='10sp',
            color=(1, 1, 1, 1),
            size_hint_y=0.25,
            halign='center',
            valign='middle',
        )
        self.pct_label.bind(size=self.pct_label.setter('text_size'))

        self.add_widget(self.name_label)
        self.add_widget(self.price_label)
        self.add_widget(self.pct_label)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update(self, price, pct):
        color = pct_to_color(pct)
        self.rect_color.rgba = color
        if price is not None:
            self.price_label.text = f'₹{price:,.1f}'
        else:
            self.price_label.text = 'N/A'
        if pct is not None:
            sign = '+' if pct >= 0 else ''
            self.pct_label.text = f'{sign}{pct:.2f}%'
        else:
            self.pct_label.text = ''


class HeatmapGrid(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(cols=5, spacing=3, padding=3,
                         size_hint_y=None, **kwargs)
        self.tiles = {}
        for ticker in NIFTY50:
            tile = StockTile(ticker, size_hint_y=None, height=80)
            self.tiles[ticker] = tile
            self.add_widget(tile)
        self.bind(minimum_height=self.setter('height'))

    def refresh_tile(self, ticker, price, pct):
        if ticker in self.tiles:
            self.tiles[ticker].update(price, pct)


class NiftyHeatmapApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1)

        root = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(size_hint_y=None, height=50, padding=[8, 4],
                           spacing=8)
        with header.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.header_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(self.header_rect, 'pos', v),
                    size=lambda i, v: setattr(self.header_rect, 'size', v))

        title = Label(text='[b]NIFTY 50 Heatmap[/b]', markup=True,
                      font_size='16sp', color=(1, 0.85, 0.1, 1))
        self.status_label = Label(text='Tap Refresh', font_size='11sp',
                                  color=(0.7, 0.7, 0.7, 1),
                                  size_hint_x=0.45, halign='right',
                                  valign='middle')
        self.status_label.bind(size=self.status_label.setter('text_size'))

        refresh_btn = Button(text='⟳ Refresh', size_hint_x=None, width=90,
                             font_size='12sp', background_color=(0.2, 0.5, 0.9, 1),
                             background_normal='')
        refresh_btn.bind(on_release=self.start_refresh)

        header.add_widget(title)
        header.add_widget(self.status_label)
        header.add_widget(refresh_btn)

        # Scrollable heatmap grid
        scroll = ScrollView(do_scroll_x=False)
        self.grid = HeatmapGrid()
        scroll.add_widget(self.grid)

        root.add_widget(header)
        root.add_widget(scroll)

        # Auto-load on start
        Clock.schedule_once(lambda dt: self.start_refresh(), 0.5)
        return root

    def start_refresh(self, *args):
        self.status_label.text = 'Loading...'
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        if yf is None:
            Clock.schedule_once(lambda dt: setattr(
                self.status_label, 'text', 'yfinance not available'), 0)
            return

        results = {}
        try:
            # Batch download — much faster than one by one
            tickers_str = ' '.join(NIFTY50)
            data = yf.download(tickers_str, period='2d', interval='1d',
                               group_by='ticker', auto_adjust=True, progress=False)
            for ticker in NIFTY50:
                try:
                    if ticker in data.columns.get_level_values(0):
                        closes = data[ticker]['Close'].dropna()
                    else:
                        closes = data['Close'].dropna() if len(NIFTY50) == 1 else None
                    if closes is not None and len(closes) >= 2:
                        prev = float(closes.iloc[-2])
                        curr = float(closes.iloc[-1])
                        pct = ((curr - prev) / prev) * 100
                        results[ticker] = (curr, pct)
                    elif closes is not None and len(closes) == 1:
                        curr = float(closes.iloc[-1])
                        results[ticker] = (curr, None)
                    else:
                        results[ticker] = (None, None)
                except Exception:
                    results[ticker] = (None, None)

        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(
                self.status_label, 'text', f'Error: {str(e)[:30]}'), 0)
            return

        # Update UI on main thread
        def update_ui(dt):
            for ticker, (price, pct) in results.items():
                self.grid.refresh_tile(ticker, price, pct)
            from datetime import datetime
            now = datetime.now().strftime('%H:%M:%S')
            self.status_label.text = f'Updated {now}'

        Clock.schedule_once(update_ui, 0)


if __name__ == '__main__':
    NiftyHeatmapApp().run()
