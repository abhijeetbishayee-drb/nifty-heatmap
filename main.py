import sys
import os
import traceback
import json
import threading
import webbrowser
import requests
from datetime import datetime

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp

# Debug log
LOG_PATH = '/data/data/com.nse.niftyheatmap/files/debug.log'
def dlog(msg):
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(str(msg) + '\n')
    except Exception:
        pass

try:
    open(LOG_PATH, 'w').close()
except Exception:
    pass

dlog("APP STARTING - Python: " + sys.version)

# Nifty 50 tickers — TATAMOTORS replaced with TVSMOTOR (TMPV)
NIFTY50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "HCLTECH.NS",
    "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "BAJFINANCE.NS", "WIPRO.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "NESTLEIND.NS", "TECHM.NS",
    "M&M.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "JSWSTEEL.NS",
    "TVSMOTOR.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "BPCL.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "INDUSINDBK.NS", "GRASIM.NS",
    "APOLLOHOSP.NS", "BRITANNIA.NS", "DIVISLAB.NS", "TATACONSUM.NS", "SBILIFE.NS",
    "HDFCLIFE.NS", "BAJAJ-AUTO.NS", "UPL.NS", "LTM.NS", "HINDALCO.NS",
]

INDICES = {
    "^NSEI": "nifty",
    "^NSEBANK": "banknifty",
}
INDEX_LABELS = {
    "nifty": "NIFTY 50",
    "banknifty": "BANK NIFTY",
}

SHORT_NAMES = {
    "HINDUNILVR.NS": "HINDUNLVR",
    "BHARTIARTL.NS": "BHARTIARTL",
    "BAJAJFINSV.NS": "BAJAJFINS",
    "APOLLOHOSP.NS": "APOLLOHOS",
    "TATACONSUM.NS": "TATACONSU",
    "HEROMOTOCO.NS": "HEROMOTOC",
    "INDUSINDBK.NS": "INDUSINDB",
    "ULTRACEMCO.NS": "ULTRACEMC",
    "BAJAJ-AUTO.NS": "BAJAJ-AUT",
    "ADANIPORTS.NS": "ADANIPORT",
    "BAJFINANCE.NS": "BAJFINANC",
    "COALINDIA.NS":  "COALINDIA",
    "TVSMOTOR.NS":   "TMPV",
}

def get_short_name(ticker):
    if ticker in SHORT_NAMES:
        return SHORT_NAMES[ticker]
    return ticker.replace(".NS", "").replace("-", "")[:9]

def nse_url(ticker):
    symbol = ticker.replace(".NS", "")
    return f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"

def pct_to_color(pct):
    if pct is None:
        return (0.25, 0.25, 0.25, 1)
    if pct >= 3:
        return (0.0, 0.50, 0.05, 1)
    elif pct >= 2:
        return (0.0, 0.60, 0.10, 1)
    elif pct >= 1:
        return (0.05, 0.70, 0.15, 1)
    elif pct > 0:
        return (0.10, 0.55, 0.30, 1)
    elif pct == 0:
        return (0.45, 0.45, 0.15, 1)  # neutral yellow-gray between green and red
    elif pct > -1:
        return (0.60, 0.10, 0.10, 1)
    elif pct > -2:
        return (0.72, 0.05, 0.05, 1)
    else:
        return (0.55, 0.0, 0.0, 1)

# Shared palette — matches the amber/near-black identity used across the
# NSE index constituents web heatmap, so the app and web page read as one product.
ACCENT_GOLD = (0.91, 0.72, 0.29, 1)      # #e8b84a
BG_PANEL = (0.08, 0.08, 0.08, 1)
BG_PANEL_2 = (0.10, 0.10, 0.10, 1)
BORDER_GRAY = (0.22, 0.22, 0.22, 1)
TILE_RADIUS = dp(8)


class PillButton(ButtonBehavior, BoxLayout):
    """A flat button with rounded corners and a pressed-state dim, used in
    place of Kivy's default Button so it matches the app's rounded-card look."""

    def __init__(self, text, bg_rgba=ACCENT_GOLD, text_color=(0.05, 0.05, 0.05, 1),
                 font_size=None, **kwargs):
        super().__init__(**kwargs)
        self._bg_rgba = bg_rgba
        with self.canvas.before:
            self._color = Color(*bg_rgba)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.label = Label(
            text=text, bold=True, color=text_color,
            font_size=font_size or sp(11.5))
        self.add_widget(self.label)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_press(self):
        r, g, b, a = self._bg_rgba
        self._color.rgba = (r * 0.8, g * 0.8, b * 0.8, a)

    def on_release(self):
        self._color.rgba = self._bg_rgba


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

def fetch_one(ticker):
    try:
        sym = ticker.replace('^', '%5E')
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5d'
        resp = requests.get(url, headers=HEADERS, timeout=8)
        data = resp.json()
        meta = data['chart']['result'][0]['meta']
        price = meta.get('regularMarketPrice')
        pct = meta.get('regularMarketChangePercent')
        pts = meta.get('fulldayChange')
        day_high = meta.get('regularMarketDayHigh')
        day_low = meta.get('regularMarketDayLow')
        return ticker, (price, pct, pts, day_high, day_low)
    except Exception as e:
        dlog(f"Error fetching {ticker}: {e}")
        return ticker, (None, None, None, None, None)


def fetch_nifty_data():
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = {}
    indices = {}

    all_tickers = list(INDICES.keys()) + NIFTY50
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_one, t): t for t in all_tickers}
        for future in as_completed(futures):
            ticker, value = future.result()
            if ticker in INDICES:
                price, pct, pts, day_high, day_low = value
                if price is not None and pct is not None:
                    indices[INDICES[ticker]] = {
                        'price': price, 'pct': pct, 'pts': pts,
                        'dayHigh': day_high, 'dayLow': day_low,
                    }
            else:
                results[ticker] = value

    dlog(f"Fetched {len(results)} stocks, indices={list(indices.keys())}")
    return results, indices


class DayRangeBar(Widget):
    """Small horizontal range bar: a line from day-low to day-high, with a
    dot marking where the current price sits between them."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.day_low = None
        self.day_high = None
        self.price = None
        self.line_color = Color(0.6, 0.6, 0.6, 0.5)
        self.dot_color = Color(1, 1, 1, 1)
        with self.canvas:
            self.canvas.add(self.line_color)
            self._line = Line(points=[], width=1.2)
            self.canvas.add(self.dot_color)
            self._dot = Ellipse(pos=(0, 0), size=(dp(6), dp(6)))
        self.bind(pos=self._redraw, size=self._redraw)

    def set_data(self, day_low, day_high, price, dot_rgba):
        self.day_low = day_low
        self.day_high = day_high
        self.price = price
        self.dot_color.rgba = dot_rgba
        self._redraw()

    def _redraw(self, *args):
        y = self.y + self.height / 2.0
        x0 = self.x + dp(3)
        x1 = self.x + self.width - dp(3)
        self._line.points = [x0, y, x1, y]

        if self.day_low is None or self.day_high is None or self.price is None:
            self._dot.size = (0, 0)
            return
        span = self.day_high - self.day_low
        if span <= 0:
            pos_ratio = 0.5
        else:
            pos_ratio = (self.price - self.day_low) / span
            pos_ratio = max(0.0, min(1.0, pos_ratio))
        dot_d = dp(6)
        dot_x = x0 + (x1 - x0) * pos_ratio - dot_d / 2.0
        self._dot.pos = (dot_x, y - dot_d / 2.0)
        self._dot.size = (dot_d, dot_d)


class StockTile(ButtonBehavior, BoxLayout):
    def __init__(self, ticker, tile_height=86, **kwargs):
        super().__init__(orientation='vertical', padding=(dp(4), dp(3)), spacing=dp(1), **kwargs)
        self.ticker = ticker
        self.size_hint_y = None
        self.height = tile_height

        with self.canvas.before:
            self.rect_color = Color(0.25, 0.25, 0.25, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[TILE_RADIUS])
        self.bind(pos=self._update_rect, size=self._update_rect)

        fs_name = sp(10)
        fs_price = sp(9.5)
        fs_pct = sp(10)
        fs_range = sp(7.5)

        self.name_label = Label(
            text=get_short_name(ticker), font_size=fs_name,
            bold=True, color=(1, 1, 1, 1),
            size_hint_y=0.22, halign='center', valign='middle')
        self.name_label.bind(size=self.name_label.setter('text_size'))

        self.price_label = Label(
            text='', font_size=fs_price, color=(1, 1, 1, 0.95),
            size_hint_y=0.19, halign='center', valign='middle')
        self.price_label.bind(size=self.price_label.setter('text_size'))

        self.pct_label = Label(
            text='', font_size=fs_pct, bold=True, color=(1, 1, 1, 1),
            size_hint_y=0.19, halign='center', valign='middle')
        self.pct_label.bind(size=self.pct_label.setter('text_size'))

        self.range_bar = DayRangeBar(size_hint_y=0.18)

        range_labels = BoxLayout(orientation='horizontal', size_hint_y=0.22)
        self.low_label = Label(
            text='', font_size=fs_range, color=(1, 1, 1, 0.75),
            halign='left', valign='middle')
        self.low_label.bind(size=self.low_label.setter('text_size'))
        self.high_label = Label(
            text='', font_size=fs_range, color=(1, 1, 1, 0.75),
            halign='right', valign='middle')
        self.high_label.bind(size=self.high_label.setter('text_size'))
        range_labels.add_widget(self.low_label)
        range_labels.add_widget(self.high_label)

        self.add_widget(self.name_label)
        self.add_widget(self.price_label)
        self.add_widget(self.pct_label)
        self.add_widget(self.range_bar)
        self.add_widget(range_labels)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update(self, price, pct, day_low, day_high):
        color = pct_to_color(pct)
        self.rect_color.rgba = color
        if price is not None:
            decimals = 0 if price >= 1000 else 1
            self.price_label.text = f'Rs.{price:,.{decimals}f}'
        else:
            self.price_label.text = 'N/A'
        if pct is not None:
            sign = '+' if pct >= 0 else ''
            self.pct_label.text = f'{sign}{pct:.2f}%'
        else:
            self.pct_label.text = ''

        if day_low is not None and day_high is not None and price is not None:
            # dot color: light on dark tiles, dark on light tiles — pick by luminance
            r, g, b, _a = color
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            dot_rgba = (0.08, 0.08, 0.08, 1) if luminance > 0.55 else (1, 1, 1, 1)
            self.range_bar.set_data(day_low, day_high, price, dot_rgba)
            self.low_label.text = f'{day_low:,.0f}'
            self.high_label.text = f'{day_high:,.0f}'
        else:
            self.range_bar.set_data(None, None, None, (1, 1, 1, 1))
            self.low_label.text = ''
            self.high_label.text = ''

    def on_release(self):
        try:
            webbrowser.open(nse_url(self.ticker))
        except Exception as e:
            dlog(f"Failed to open NSE page for {self.ticker}: {e}")


class MoverRow(ButtonBehavior, BoxLayout):
    """One row in the Top Gainers / Top Losers list: name, price, the
    off-low or off-high %, and the same day-range bar used on tiles."""

    def __init__(self, accent_rgba, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=dp(34),
                         spacing=dp(1), **kwargs)
        self.ticker = None
        self.accent_rgba = accent_rgba

        top = BoxLayout(orientation='horizontal', size_hint_y=0.5)
        self.name_label = Label(text='', font_size=sp(9.5), bold=True, color=accent_rgba,
                                halign='left', valign='middle', size_hint_x=0.36)
        self.name_label.bind(size=self.name_label.setter('text_size'))
        self.price_label = Label(text='', font_size=sp(9), color=accent_rgba,
                                 halign='center', valign='middle', size_hint_x=0.34)
        self.price_label.bind(size=self.price_label.setter('text_size'))
        self.value_label = Label(text='', font_size=sp(9.5), bold=True, color=accent_rgba,
                                 halign='right', valign='middle', size_hint_x=0.30)
        self.value_label.bind(size=self.value_label.setter('text_size'))
        top.add_widget(self.name_label)
        top.add_widget(self.price_label)
        top.add_widget(self.value_label)

        self.range_bar = DayRangeBar(size_hint_y=0.28)

        range_labels = BoxLayout(orientation='horizontal', size_hint_y=0.22)
        self.low_label = Label(text='', font_size=sp(7), color=(1, 1, 1, 0.6),
                               halign='left', valign='middle')
        self.low_label.bind(size=self.low_label.setter('text_size'))
        self.high_label = Label(text='', font_size=sp(7), color=(1, 1, 1, 0.6),
                                halign='right', valign='middle')
        self.high_label.bind(size=self.high_label.setter('text_size'))
        range_labels.add_widget(self.low_label)
        range_labels.add_widget(self.high_label)

        self.add_widget(top)
        self.add_widget(self.range_bar)
        self.add_widget(range_labels)

    def update(self, ticker, price, value_pct, day_low, day_high):
        self.ticker = ticker
        self.name_label.text = get_short_name(ticker) if ticker else ''
        self.price_label.text = f'Rs.{price:,.2f}' if price is not None else 'N/A'
        if value_pct is not None:
            sign = '+' if value_pct >= 0 else ''
            self.value_label.text = f'{sign}{value_pct:.2f}%'
        else:
            self.value_label.text = ''
        if day_low is not None and day_high is not None and price is not None:
            self.range_bar.set_data(day_low, day_high, price, self.accent_rgba)
            self.low_label.text = f'{day_low:,.0f}'
            self.high_label.text = f'{day_high:,.0f}'
        else:
            self.range_bar.set_data(None, None, None, self.accent_rgba)
            self.low_label.text = ''
            self.high_label.text = ''

    def on_release(self):
        if self.ticker:
            try:
                webbrowser.open(nse_url(self.ticker))
            except Exception as e:
                dlog(f"Failed to open NSE page for {self.ticker}: {e}")


class IndexCard(BoxLayout):
    """Compact index readout with an inline day-range bar, used for both
    NIFTY 50 and BANK NIFTY."""

    def __init__(self, label, **kwargs):
        super().__init__(orientation='vertical', padding=(dp(8), dp(4)), spacing=dp(2), **kwargs)
        self.label_text = label
        self.size_hint_y = None
        self.height = dp(48)

        with self.canvas.before:
            Color(*BG_PANEL)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        top_row = BoxLayout(orientation='horizontal', size_hint_y=0.55)
        self.name_label = Label(
            text=label, font_size=sp(10.5), bold=True, color=(0.8, 0.8, 0.8, 1),
            halign='left', valign='middle', size_hint_x=0.35)
        self.name_label.bind(size=self.name_label.setter('text_size'))
        self.value_label = Label(
            text='--', font_size=sp(10.5), bold=True, color=(1, 1, 1, 1),
            halign='right', valign='middle', markup=True)
        self.value_label.bind(size=self.value_label.setter('text_size'))
        top_row.add_widget(self.name_label)
        top_row.add_widget(self.value_label)

        self.range_bar = DayRangeBar(size_hint_y=0.45)

        self.add_widget(top_row)
        self.add_widget(self.range_bar)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def update(self, data):
        if not data:
            self.value_label.text = '--'
            self.range_bar.set_data(None, None, None, (1, 1, 1, 1))
            return
        price = data.get('price')
        pct = data.get('pct')
        pts = data.get('pts')
        day_low = data.get('dayLow')
        day_high = data.get('dayHigh')

        if price is not None and pct is not None:
            sign = '+' if pct >= 0 else ''
            color = '00cc44' if pct >= 0 else 'ff4444'
            self.value_label.text = (
                f'{price:,.2f}  [color={color}]{sign}{pct:.2f}% ({sign}{pts:.1f})[/color]'
            )
        else:
            self.value_label.text = '--'

        if day_low is not None and day_high is not None and price is not None:
            self.range_bar.set_data(day_low, day_high, price, (0.3, 0.7, 1, 1))
        else:
            self.range_bar.set_data(None, None, None, (1, 1, 1, 1))


class NiftyHeatmapApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.05, 1)
        self.stock_data = {}
        self.index_data = {}
        self.tiles = {}

        root = BoxLayout(orientation='vertical', spacing=0)

        # ── Header ──────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=dp(44),
                           padding=[dp(8), dp(4)], spacing=dp(6))
        with header.canvas.before:
            Color(0.10, 0.10, 0.10, 1)
            self.hdr_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(self.hdr_rect, 'pos', v),
                    size=lambda i, v: setattr(self.hdr_rect, 'size', v))

        title = Label(text='[b]NIFTY 50 · HEATMAP[/b]', markup=True,
                      font_size=sp(14), color=ACCENT_GOLD,
                      size_hint_x=0.38, halign='left', valign='middle')
        title.bind(size=title.setter('text_size'))

        self.status_label = Label(text='Tap refresh', font_size=sp(10),
                                  color=(0.75, 0.75, 0.75, 1),
                                  size_hint_x=0.42, halign='right', valign='middle')
        self.status_label.bind(size=self.status_label.setter('text_size'))

        refresh_btn = PillButton('REFRESH', bg_rgba=ACCENT_GOLD,
                                 size_hint=(None, None), width=dp(84), height=dp(30),
                                 pos_hint={'center_y': 0.5})
        refresh_btn.bind(on_release=self.start_refresh)

        header.add_widget(title)
        header.add_widget(self.status_label)
        header.add_widget(refresh_btn)

        # ── Index cards (Nifty 50 + Bank Nifty) ──────────────────
        indices_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(2),
                                padding=[dp(2), 0])
        self.index_cards = {}
        for key in ('nifty', 'banknifty'):
            card = IndexCard(INDEX_LABELS[key])
            self.index_cards[key] = card
            indices_row.add_widget(card)

        self.updated_label = Label(text='', font_size=sp(9.5),
                                   color=(0.55, 0.55, 0.55, 1),
                                   size_hint_y=None, height=dp(16),
                                   halign='center', valign='middle')
        self.updated_label.bind(size=self.updated_label.setter('text_size'))

        # ── Heatmap grid (scrollable) ────────────────────────────
        self.scroll = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=5, spacing=dp(2), padding=dp(2),
                               size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))

        for ticker in NIFTY50:
            tile = StockTile(ticker, tile_height=dp(98))
            self.tiles[ticker] = tile
            self.grid.add_widget(tile)

        self.scroll.add_widget(self.grid)

        # ── Gainers / Losers bar ─────────────────────────────────
        N_MOVERS = 5
        GREEN_ACCENT = (0.3, 1.0, 0.4, 1)
        RED_ACCENT = (1.0, 0.35, 0.35, 1)

        self.bottom_bar = BoxLayout(size_hint_y=None, height=dp(210),
                                    padding=[dp(6), dp(4)], spacing=dp(4))
        with self.bottom_bar.canvas.before:
            Color(0.08, 0.08, 0.08, 1)
            self.bot_rect = Rectangle(pos=self.bottom_bar.pos, size=self.bottom_bar.size)
        self.bottom_bar.bind(pos=lambda i, v: setattr(self.bot_rect, 'pos', v),
                             size=lambda i, v: setattr(self.bot_rect, 'size', v))

        gainers_box = BoxLayout(orientation='vertical', spacing=dp(2))
        self.gainers_title = Label(text='[b]TOP GAINERS[/b] [size=8](off low)[/size]', markup=True,
                                   font_size=sp(10), color=GREEN_ACCENT,
                                   size_hint_y=None, height=dp(18),
                                   halign='left', valign='middle')
        self.gainers_title.bind(size=self.gainers_title.setter('text_size'))
        gainers_box.add_widget(self.gainers_title)
        self.gainer_rows = [MoverRow(GREEN_ACCENT) for _ in range(N_MOVERS)]
        for row in self.gainer_rows:
            gainers_box.add_widget(row)

        losers_box = BoxLayout(orientation='vertical', spacing=dp(2))
        self.losers_title = Label(text='[b]TOP LOSERS[/b] [size=8](off high)[/size]', markup=True,
                                  font_size=sp(10), color=RED_ACCENT,
                                  size_hint_y=None, height=dp(18),
                                  halign='left', valign='middle')
        self.losers_title.bind(size=self.losers_title.setter('text_size'))
        losers_box.add_widget(self.losers_title)
        self.loser_rows = [MoverRow(RED_ACCENT) for _ in range(N_MOVERS)]
        for row in self.loser_rows:
            losers_box.add_widget(row)

        self.bottom_bar.add_widget(gainers_box)
        self.bottom_bar.add_widget(losers_box)

        # ── Assemble ─────────────────────────────────────────────
        root.add_widget(header)
        root.add_widget(indices_row)
        root.add_widget(self.updated_label)
        root.add_widget(self.scroll)
        root.add_widget(self.bottom_bar)

        Clock.schedule_once(lambda dt: self.start_refresh(), 0.5)
        Clock.schedule_interval(lambda dt: self.start_refresh(), 60)
        return root

    def start_refresh(self, *args):
        self.status_label.text = 'Loading...'
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        dlog("fetch_data called")
        try:
            results, indices = fetch_nifty_data()
            dlog(f"Got {len(results)} results, indices={indices}")

            def update_ui(dt):
                self.stock_data = results
                self.index_data = indices

                # Sort tiles by pct descending (session % change)
                sorted_tickers = sorted(
                    NIFTY50,
                    key=lambda t: (results.get(t, (None, None, None, None, None))[1]
                                   if results.get(t, (None,))[1] is not None else -999),
                    reverse=True
                )
                self.grid.clear_widgets()
                for ticker in sorted_tickers:
                    tile = self.tiles[ticker]
                    price, pct, pts, day_high, day_low = results.get(
                        ticker, (None, None, None, None, None))
                    tile.update(price, pct, day_low, day_high)
                    self.grid.add_widget(tile)

                # Update index cards
                for key, card in self.index_cards.items():
                    card.update(indices.get(key))

                now = datetime.now().strftime('%d %b %Y  %H:%M:%S IST')
                self.updated_label.text = f'Updated: {now}'

                # Top gainers/losers: biggest move off the day's low/high
                rows = []
                for t in NIFTY50:
                    price, pct, pts, day_high, day_low = results.get(
                        t, (None, None, None, None, None))
                    off_low = None
                    if price is not None and day_low:
                        off_low = (price - day_low) / day_low * 100
                    off_high = None
                    if price is not None and day_high:
                        off_high = (price - day_high) / day_high * 100
                    rows.append((t, price, off_low, off_high, day_low, day_high))

                valid_low = [r for r in rows if r[2] is not None]
                valid_high = [r for r in rows if r[3] is not None]
                gainers = sorted(valid_low, key=lambda r: r[2], reverse=True)[:5]
                losers = sorted(valid_high, key=lambda r: r[3])[:5]

                for i, row_widget in enumerate(self.gainer_rows):
                    if i < len(gainers):
                        t, price, off_low, off_high, day_low, day_high = gainers[i]
                        row_widget.update(t, price, off_low, day_low, day_high)
                    else:
                        row_widget.update(None, None, None, None, None)

                for i, row_widget in enumerate(self.loser_rows):
                    if i < len(losers):
                        t, price, off_low, off_high, day_low, day_high = losers[i]
                        row_widget.update(t, price, off_high, day_low, day_high)
                    else:
                        row_widget.update(None, None, None, None, None)

                loaded = sum(1 for v in results.values() if v[0] is not None)
                self.status_label.text = f'({loaded}/50)'

            Clock.schedule_once(update_ui, 0)

        except Exception as e:
            full_err = traceback.format_exc()
            dlog("FETCH ERROR: " + full_err)
            Clock.schedule_once(lambda dt: setattr(
                self.status_label, 'text', f'Err: {str(e)[:40]}'), 0)


if __name__ == '__main__':
    NiftyHeatmapApp().run()
