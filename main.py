import sys
import os
import traceback
import json
import threading
import requests
from datetime import datetime
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp

LOG_PATH = '/data/data/com.nse.niftyheatmap/files/debug.log'

try:
    with open(LOG_PATH, 'w') as f:
        pass
except Exception:
    pass


def dlog(msg):
    try:
        with open(LOG_PATH, 'a') as f:
            f.write(str(msg) + '\n')
    except Exception:
        pass


dlog('APP STARTING - Python: ' + sys.version)

NIFTY50 = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
    'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'HCLTECH.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'BAJFINANCE.NS', 'WIPRO.NS',
    'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'NESTLEIND.NS', 'TECHM.NS',
    'M&M.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'COALINDIA.NS', 'JSWSTEEL.NS',
    'TVSMOTOR.NS', 'TATASTEEL.NS', 'BAJAJFINSV.NS', 'BPCL.NS', 'DRREDDY.NS',
    'CIPLA.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS', 'INDUSINDBK.NS', 'GRASIM.NS',
    'APOLLOHOSP.NS', 'BRITANNIA.NS', 'DIVISLAB.NS', 'TATACONSUM.NS',
    'SBILIFE.NS', 'HDFCLIFE.NS', 'BAJAJ-AUTO.NS', 'UPL.NS', 'LTM.NS',
    'HINDALCO.NS',
]

SHORT_NAMES = {
    'HINDUNILVR.NS': 'HINDUNLVR',
    'BHARTIARTL.NS': 'BHARTIARTL',
    'BAJAJFINSV.NS': 'BAJAJFINS',
    'APOLLOHOSP.NS': 'APOLLOHOS',
    'TATACONSUM.NS': 'TATACONSU',
    'HEROMOTOCO.NS': 'HEROMOTOC',
    'INDUSINDBK.NS': 'INDUSINDB',
    'ULTRACEMCO.NS': 'ULTRACEMC',
    'BAJAJ-AUTO.NS': 'BAJAJ-AUT',
    'ADANIPORTS.NS': 'ADANIPORT',
    'LTIMINDLTD.NS': 'LTIM',
    'COALINDIA.NS': 'COALINDIA',
    'TVSMOTOR.NS':  'TMPV',
}


def get_short_name(ticker):
    if ticker in SHORT_NAMES:
        return SHORT_NAMES[ticker]
    return ticker.replace('.NS', '').replace('-', '')[:9]


def pct_to_color(pct):
    if pct is None:
        return (0.25, 0.25, 0.25, 1)
    if pct >= 3:
        return (0.0, 0.5, 0.05, 1)
    if pct >= 2:
        return (0.0, 0.6, 0.1, 1)
    if pct >= 1:
        return (0.05, 0.7, 0.15, 1)
    if pct >= 0:
        return (0.1, 0.55, 0.3, 1)
    if pct >= -1:
        return (0.3, 0.3, 0.3, 1)
    if pct >= -2:
        return (0.6, 0.1, 0.1, 1)
    return (0.55, 0.0, 0.0, 1)


def fetch_nifty_data():
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # FIX: Updated headers and use query2 subdomain for better mobile reliability
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://finance.yahoo.com',
    }

    def fetch_one(ticker):
        try:
            # FIX: Use query2 instead of query1 — more reliable on mobile/Android IPs
            url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d'
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            closes = [
                c for c in
                data['chart']['result'][0]['indicators']['quote'][0]['close']
                if c is not None
            ]
            if len(closes) >= 2:
                prev = closes[-2]
                curr = closes[-1]
                pct = (curr - prev) / prev * 100
                return ticker, (curr, pct)
            elif len(closes) == 1:
                return ticker, (closes[-1], None)
            else:
                return ticker, (None, None)
        except Exception as e:
            dlog(f'Error fetching {ticker}: {e}')
            return ticker, (None, None)

    all_tickers = ['^NSEI'] + NIFTY50
    results = {}
    index_data = {}

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_one, t): t for t in all_tickers}
        for future in as_completed(futures):
            ticker, value = future.result()
            if ticker == '^NSEI':
                if value[0] is not None and value[1] is not None:
                    curr = value[0]
                    pct = value[1]
                    prev = curr / (1 + pct / 100)
                    pts = curr - prev
                    index_data = {'price': curr, 'pct': pct, 'pts': pts}
            else:
                results[ticker] = value

    dlog(f'Fetched {len(results)} stocks, index={index_data}')
    return results, index_data


class StockTile(BoxLayout):
    def __init__(self, ticker, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 0
        self.padding = dp(2)

        short = get_short_name(ticker)
        fs_name = sp(9.5)
        fs_price = sp(8.5)
        fs_pct = sp(9)

        with self.canvas.before:
            self.rect_color = Color(0.25, 0.25, 0.25, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)

        self.name_label = Label(
            text=short,
            font_size=fs_name,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=0.35,
            halign='center',
            valign='middle',
        )
        self.name_label.bind(size=self.name_label.setter('text_size'))

        self.price_label = Label(
            text='',
            font_size=fs_price,
            color=(1, 1, 1, 1),
            size_hint_y=0.35,
            halign='center',
            valign='middle',
        )
        self.price_label.bind(size=self.price_label.setter('text_size'))

        self.pct_label = Label(
            text='',
            font_size=fs_pct,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=0.3,
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
        self.rect_color.rgba = pct_to_color(pct)
        if price is not None:
            self.price_label.text = f'Rs.{price:,.1f}'
        else:
            self.price_label.text = 'N/A'
        if pct is not None:
            sign = '+' if pct >= 0 else ''
            self.pct_label.text = f'{sign}{pct:.2f}%'
        else:
            self.pct_label.text = ''


class NiftyHeatmapApp(App):

    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.05, 1)
        self.stock_data = {}
        self.index_data = {}
        self.tiles = {}

        root = BoxLayout(orientation='vertical', spacing=0)

        # ── Header bar ──────────────────────────────────────────────
        header = BoxLayout(
            size_hint_y=None,
            height=dp(44),
            padding=[dp(8), dp(4)],
            spacing=dp(6),
        )
        with header.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.hdr_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(
            pos=lambda inst, v: setattr(self.hdr_rect, 'pos', v),
            size=lambda inst, v: setattr(self.hdr_rect, 'size', v),
        )

        title = Label(
            text='[b]NIFTY 50  HEATMAP[/b]',
            markup=True,
            font_size=sp(14),
            color=(1, 0.85, 0.1, 1),
            size_hint_x=0.38,
            halign='left',
            valign='middle',
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)

        self.nifty_label = Label(
            text='NIFTY 50  --',
            markup=True,
            font_size=sp(11),
            color=(0.9, 0.9, 0.9, 1),
            size_hint_x=0.38,
            halign='left',
            valign='middle',
        )
        self.nifty_label.bind(size=self.nifty_label.setter('text_size'))
        header.add_widget(self.nifty_label)

        refresh_btn = Button(
            text='⟳ Refresh',
            font_size=sp(11),
            size_hint_x=0.24,
            background_color=(0.2, 0.45, 0.8, 1),
            color=(1, 1, 1, 1),
        )
        refresh_btn.bind(on_press=lambda x: self.start_refresh())
        header.add_widget(refresh_btn)
        root.add_widget(header)

        # ── Status bar ───────────────────────────────────────────────
        status_bar = BoxLayout(
            size_hint_y=None,
            height=dp(22),
            padding=[dp(8), 0],
        )
        with status_bar.canvas.before:
            Color(0.07, 0.07, 0.07, 1)
            self.idx_rect = Rectangle(pos=status_bar.pos, size=status_bar.size)
        status_bar.bind(
            pos=lambda inst, v: setattr(self.idx_rect, 'pos', v),
            size=lambda inst, v: setattr(self.idx_rect, 'size', v),
        )

        self.status_label = Label(
            text='Loading...',
            font_size=sp(9.5),
            color=(0.7, 0.7, 0.7, 1),
            halign='left',
            valign='middle',
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        status_bar.add_widget(self.status_label)

        self.updated_label = Label(
            text='',
            font_size=sp(9),
            color=(0.55, 0.55, 0.55, 1),
            halign='right',
            valign='middle',
        )
        self.updated_label.bind(size=self.updated_label.setter('text_size'))
        status_bar.add_widget(self.updated_label)
        root.add_widget(status_bar)

        # ── Heatmap grid ─────────────────────────────────────────────
        scroll = ScrollView()
        self.grid = GridLayout(
            cols=5,
            spacing=dp(2),
            padding=dp(2),
            size_hint_y=None,
        )
        self.grid.bind(minimum_height=self.grid.setter('height'))

        for ticker in NIFTY50:
            tile = StockTile(ticker, size_hint_y=None, height=dp(58))
            self.tiles[ticker] = tile
            self.grid.add_widget(tile)

        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        # ── Bottom bar (gainers / losers) ────────────────────────────
        bottom_bar = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            padding=[dp(6), dp(2)],
            spacing=dp(4),
        )
        with bottom_bar.canvas.before:
            Color(0.08, 0.08, 0.08, 1)
            self.bot_rect = Rectangle(pos=bottom_bar.pos, size=bottom_bar.size)
        bottom_bar.bind(
            pos=lambda inst, v: setattr(self.bot_rect, 'pos', v),
            size=lambda inst, v: setattr(self.bot_rect, 'size', v),
        )

        gainers_col = BoxLayout(orientation='vertical', spacing=0)
        gainers_title = Label(
            text='[b]TOP GAINERS[/b]',
            markup=True,
            font_size=sp(8.5),
            color=(0.3, 0.9, 0.4, 1),
            size_hint_y=0.35,
            halign='left',
            valign='middle',
        )
        gainers_title.bind(size=gainers_title.setter('text_size'))
        self.gainers_label = Label(
            text='',
            font_size=sp(8),
            color=(0.8, 0.95, 0.8, 1),
            size_hint_y=0.65,
            halign='left',
            valign='top',
        )
        self.gainers_label.bind(size=self.gainers_label.setter('text_size'))
        gainers_col.add_widget(gainers_title)
        gainers_col.add_widget(self.gainers_label)
        bottom_bar.add_widget(gainers_col)

        losers_col = BoxLayout(orientation='vertical', spacing=0)
        losers_title = Label(
            text='[b]TOP LOSERS[/b]',
            markup=True,
            font_size=sp(8.5),
            color=(0.95, 0.3, 0.3, 1),
            size_hint_y=0.35,
            halign='left',
            valign='middle',
        )
        losers_title.bind(size=losers_title.setter('text_size'))
        self.losers_label = Label(
            text='',
            font_size=sp(8),
            color=(1, 0.75, 0.75, 1),
            size_hint_y=0.65,
            halign='left',
            valign='top',
        )
        self.losers_label.bind(size=self.losers_label.setter('text_size'))
        losers_col.add_widget(losers_title)
        losers_col.add_widget(self.losers_label)
        bottom_bar.add_widget(losers_col)

        root.add_widget(bottom_bar)

        Clock.schedule_once(lambda dt: self.start_refresh(), 0.5)
        return root

    def start_refresh(self):
        self.status_label.text = 'Tap Refresh'
        dlog('fetch_data called')
        t = threading.Thread(target=self.fetch_data, daemon=True)
        t.start()

    def fetch_data(self):
        try:
            results, index_data = fetch_nifty_data()
            Clock.schedule_once(lambda dt: self._update_ui(results, index_data), 0)
        except Exception:
            err = traceback.format_exc()
            dlog('FETCH ERROR: ' + err)
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Err: ' + err[:60]), 0)

    def _update_ui(self, results, index_data):
        # Update NIFTY 50 index label
        if index_data:
            price = index_data.get('price')
            pct = index_data.get('pct')
            pts = index_data.get('pts')
            sign = '+' if pct and pct >= 0 else ''
            color = '00cc44' if pct and pct >= 0 else 'ff4444'
            if price and pct and pts:
                self.nifty_label.text = (
                    f'[b]NIFTY 50[/b]  [color={color}]{price:,.1f}  '
                    f'{sign}{pct:.2f}%  ({sign}{pts:.1f} pts)[/color]'
                )
        else:
            self.nifty_label.text = 'NIFTY 50  --'

        # Update all tiles
        for ticker in NIFTY50:
            if ticker in results:
                price, pct = results[ticker]
                self.stock_data[ticker] = (price, pct)
                if ticker in self.tiles:
                    self.tiles[ticker].update(price, pct)

        # Timestamp
        now = datetime.now().strftime('%d %b %Y  %H:%M:%S IST')
        self.updated_label.text = f'Updated: {now}'

        # Top gainers / losers
        valid = [
            t for t in NIFTY50
            if t in results and results[t][1] is not None
        ]
        gainers = sorted(valid, key=lambda t: results[t][1], reverse=True)[:4]
        losers  = sorted(valid, key=lambda t: results[t][1])[:4]

        g_text = '\n'.join(
            f'{get_short_name(t)}  +{results[t][1]:.2f}%' if results[t][1] >= 0
            else f'{get_short_name(t)}  {results[t][1]:.2f}%'
            for t in gainers
        )
        l_text = '\n'.join(
            f'{get_short_name(t)}  {results[t][1]:.2f}%'
            for t in losers
        )
        self.gainers_label.text = g_text
        self.losers_label.text  = l_text

        loaded = sum(1 for t in NIFTY50 if t in results and results[t][0] is not None)
        self.status_label.text = f'({loaded}/50)'


if __name__ == '__main__':
    NiftyHeatmapApp().run()
