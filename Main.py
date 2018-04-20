import os
import pandas as pd
from datetime import datetime
import sqlite3
import requests
import json
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import Secret

def LoadOrCreateCacheFile(FileName):
    try:
        CacheFile = open(FileName, "r")
        Contents = CacheFile.read()
        CacheFile.close()
        return json.loads(Contents)
    except:
        return {}

def RequestDataUsingCache(URL, FileName):

    if URL in LocalCache:
        # print("Getting cached data for \n", URL)
        return LocalCache[URL]
    else:
        # print("Getting Pricing Data from Exhcange \n", URL)
        Response = requests.get(URL)
        LocalCache[URL] = json.loads(Response.text)
        dumped_json_cache = json.dumps(LocalCache)
        fw = open(FileName, "w")
        fw.write(dumped_json_cache)
        fw.close()
        return LocalCache[URL]

def GetBitcoinPricingData(BitcoinExhcanges, CacheFileName):
    BaseURL = "http://www.quandl.com/api/v3/datasets/BCHARTS/"
    Currency = "USD"

    for Exchange in BitcoinExhcanges:
        RequestURL = BaseURL + Exchange + Currency + "?api_key=" + Secret.QuandlAPiKey
        try:
            PricingData = RequestDataUsingCache(RequestURL, CacheFileName)
            CreateTableForBitcoinDataInsertion(Exchange)
            InsertBticoinDataIntoDatabase(PricingData, Exchange)
        except:
            print("Error Getting Data From Quandl For", Exchange)

def InsertBticoinDataIntoDatabase(PricingData, Exchange):
    for DailyData in PricingData["dataset"]["data"]:
        Cursor.execute("Insert Into {Exchange} Values(?,?,?,?,?,?,?,?)".format(Exchange=Exchange), DailyData)
    Connection.commit()

def CreateAndConnectToDatabase():
    try:
        Connection = sqlite3.connect("CryptoCurrency.db")
        Cursor = Connection.cursor()
        return Connection, Cursor
    except Exception as Error:
        print(Error)

def CreateTableForBitcoinDataInsertion(Exchange):
    Connection.executescript("Drop Table If Exists " + Exchange)

    Query = """ Create Table {Exchange} (
                    "Date" Text,
                    "Open" Real,
                    "High" Real,
                    "Low" Real,
                    "Close" Real,
                    "VolumeBTC" Real ,
                    "VolumeCurrency" Real,
                    "WeightedAverage" Real )""".format(Exchange=Exchange)

    Connection.executescript(Query)

def GetAltCoinPricingData(Altcoins, CacheFileName):
    BaseURL = "https://poloniex.com/public?command=returnChartData&currencyPair={}&start={}&end={}&period={}"
    StartDate = datetime.strptime("2015-01-01", "%Y-%m-%d")
    EndDate = datetime.now()
    Period = 86400

    for Altcoin in Altcoins:
        CoinPair = "BTC_{}".format(Altcoin)
        RequestURL = BaseURL.format(CoinPair, StartDate.timestamp(), 1524119317, Period)
        try:
            PricingData = RequestDataUsingCache(RequestURL, CacheFileName)
            CreateTableForAltcoinDataInsertion(Altcoin)
            InsertAltcoinDataIntoDatabase(PricingData, Altcoin)
        except:
            print("Error Getting Data From Polenix For", Altcoin)


def CreateTableForAltcoinDataInsertion(Altcoin):
    Connection.executescript("Drop Table If Exists " + Altcoin)

    Query = """ Create Table {Altcoin} (
                    "Date" Text,
                    "High" Real,
                    "Low" Real,
                    "Open" Real,
                    "Close" Real,
                    "Volume" Real ,
                    "QuoteVolume" Real,
                    "WeightedAverage" Real )""".format(Altcoin=Altcoin)

    Connection.executescript(Query)

def InsertAltcoinDataIntoDatabase(PricingData, Altcoin):
    for DailyData in PricingData:
        Cursor.execute("Insert Into {Altcoin} Values(?,?,?,?,?,?,?,?)".format(Altcoin=Altcoin), [str(datetime.fromtimestamp(int(DailyData["date"])).strftime("%Y-%m-%d")), DailyData["high"], DailyData["low"], DailyData["open"], DailyData["close"], DailyData["volume"], DailyData["quoteVolume"], DailyData["weightedAverage"]])
    Connection.commit()


def DeleteZeroEntries(Altcoins, Exchange):
    CompleteDatabase = Altcoins + Exchange
    for Coin in CompleteDatabase:
        Cursor.execute("Delete From {Coin} Where Open = 0.0 Or Close = 0.0 or High = 0.0 or Low = 0.0".format(Coin=Coin))
    Connection.commit()

def GetPriceOfAltcoinsinUSD(Altcoins):
    for Altcoin in Altcoins:
        Connection.executescript("ALTER Table " + Altcoin + " ADD PriceUSD Real")
        Connection.executescript("""Update {Altcoin} Set PriceUSD = (Select B.WeightedAverage*{Altcoin}.WeightedAverage From Kraken as B Where B.Date = {Altcoin}.Date)
                                    Where Date in (Select Date From {Altcoin})""".format(Altcoin=Altcoin))
        Connection.executescript("""Update {Altcoin} Set Open = (Select B.WeightedAverage*{Altcoin}.Open From Kraken as B Where B.Date = {Altcoin}.Date)
                                    Where Date in (Select Date From {Altcoin})""".format(Altcoin=Altcoin))
        Connection.executescript("""Update {Altcoin} Set Close = (Select B.WeightedAverage*{Altcoin}.Close From Kraken as B Where B.Date = {Altcoin}.Date)
                                    Where Date in (Select Date From {Altcoin})""".format(Altcoin=Altcoin))
        Connection.executescript("""Update {Altcoin} Set High = (Select B.WeightedAverage*{Altcoin}.High From Kraken as B Where B.Date = {Altcoin}.Date)
                                    Where Date in (Select Date From {Altcoin})""".format(Altcoin=Altcoin))
        Connection.executescript("""Update {Altcoin} Set Low = (Select B.WeightedAverage*{Altcoin}.Low From Kraken as B Where B.Date = {Altcoin}.Date)
                                    Where Date in (Select Date From {Altcoin})""".format(Altcoin=Altcoin))

def DeleteNullEntries(Altcoins):
    for Coin in Altcoins:
        Cursor.execute("Delete From {Coin} Where Open Is Null Or Close Is Null or High Is Null or Low Is Null".format(Coin=Coin))
    Connection.commit()

class Crypto:

    def __init__(self, Name, Abbreviation, Website):
        self.Name = Name
        self.Abbreviation = Abbreviation
        self.Website = Website
        self.Date = []
        self.Open = []
        self.Close = []
        self.High = []
        self.Low = []
        self.WeightedAverage = []
        self.PriceUSD = -1
        self.TopStories = []

def LoadBitcoinDataIntoClass():
    BitCoin = Crypto("Bitcoin", "BTC", "https://bitcoin.org")

    Cursor.execute(""" Select * From Kraken Order By Date ASC """)
    Data = Cursor.fetchall()

    BitCoin.Date = [datetime.strptime(D[0],"%Y-%m-%d") for D in Data]
    BitCoin.Open = [D[1] for D in Data]
    BitCoin.Close = [D[4] for D in Data]
    BitCoin.High = [D[2] for D in Data]
    BitCoin.Low = [D[3] for D in Data]
    BitCoin.WeightedAverage = [D[7] for D in Data]
    BitCoin.PriceUSD = [D[7] for D in Data]
    return BitCoin

def LoadALtcoinDataIntoClass():
    Coins = []
    for Index, Altcoin in enumerate(Altcoins):
        TempCoin = Crypto(AltcoinFullNames[Index], Altcoin, Websites[Index])

        Cursor.execute(""" Select * From {Altcoin} Order By Date ASC """.format(Altcoin=Altcoin))
        Data = Cursor.fetchall()

        TempCoin.Date = [datetime.strptime(D[0],"%Y-%m-%d") for D in Data[10:]]
        TempCoin.Open = [D[3] for D in Data[10:]]
        TempCoin.Close = [D[4] for D in Data[10:]]
        TempCoin.High = [D[1] for D in Data[10:]]
        TempCoin.Low = [D[2] for D in Data[10:]]
        TempCoin.WeightedAverage = [D[7] for D in Data[10:]]
        TempCoin.PriceUSD = [D[8] for D in Data[10:]]
        Coins.append(TempCoin)

    return Coins

def WebApplication():

    app = dash.Dash()
    app.config.suppress_callback_exceptions = True

    app.layout = html.Div([
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content")
    ])

    RootPage = html.Div([
        html.H1("CryptoCurrency Markets", style={"color": "Black", "fontSize": 72, "textAlign": "center",}),
        html.Br(),
        html.Div([ html.Div([dcc.Link(Coin.Name, href="/"+Coin.Abbreviation, style={"color": "Blue", "fontSize": 24})],className="two columns") for Coin in Coins], className="row"),
        html.Br(),
        html.Label("Graph Scale"),
        dcc.RadioItems(
            id = "Scale",
            options=[
                {"label": "Linear Scale", "value": "linear"},
                {"label": "Logarithmic Scale", "value": "log"},
                ],
                value="log"),

        dcc.Graph(id="MainPageGraph",
            style={"height": 600})
    ])

    @app.callback(dash.dependencies.Output("page-content", "children"),
                  [dash.dependencies.Input("url", "pathname")])
    def display_page(pathname):
        if pathname[1:].upper() in Altcoins or pathname[1:].upper() == "BTC":
            for Coin in Coins:
                if Coin.Abbreviation == pathname[1:]:
                    TempCoin = Coin
                    break
            return RenderCoinPage(TempCoin)
        else:
            return RootPage

    @app.callback(dash.dependencies.Output("MainPageGraph", "figure"),
    [dash.dependencies.Input("Scale", "value")])
    def UpdateGraph(Scale):
        return {
            "layout": go.Layout(
                title="CryptoCurrency Prices (USD)",
                legend=dict(orientation="h"),
                xaxis=dict(type="date", range=[datetime.strptime("2017-01-01","%Y-%m-%d"), datetime.now()]),
                yaxis=dict(
                    title="CryptoCurrency Prices (USD)",
                    showticklabels = True,
                    type=Scale)),
            "data": [go.Scatter(
                    x=Coin.Date,
                    y=Coin.PriceUSD,
                    name=Coin.Name,
                    visible="visible") for Coin in Coins]}

    app.css.append_css({
        "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
    })

    app.run_server(debug=True)

def RenderCoinPage(CurrentCoin):
    RootPage = html.Div([
        html.A(html.H1(CurrentCoin.Name, style={"color": "Black", "fontSize": 72, "textAlign": "center"}), href=CurrentCoin.Website, target="_blank"),
        dcc.Link("Home Page", href="/", style={"color": "Red", "fontSize": 28}),
        html.Br(),
        html.Div([ html.Div([dcc.Link(Coin.Name, href="/"+Coin.Abbreviation, style={"color": "Blue", "fontSize": 24})],className="two columns") for Coin in [item for item in Coins if CurrentCoin != item]], className="row"),
        dcc.Graph(
            figure={
                "layout": go.Layout(
                    title=CurrentCoin.Name + " Market",
                    legend=dict(orientation="h"),
                    xaxis=dict(type="date"),
                    yaxis=dict(
                        title=CurrentCoin.Name + " Prices (USD)",
                        showticklabels = True)),
                "data": [go.Ohlc(x=CurrentCoin.Date,
                        open=CurrentCoin.Open,
                        high=CurrentCoin.High,
                        low=CurrentCoin.Low,
                        close=CurrentCoin.Close)]}, id=CurrentCoin.Name + "Graph",
                            style={"height": 1000}),
        html.Ul([html.Li(html.A(Article[0], href=Article[1], style={"color": "Blue", "fontSize": 24}, target="_blank")) for Article in CurrentCoin.TopStories], style={"padding-left": 70})])
    return RootPage

def MakeRequestGoogleCache(URL):

    if URL in LocalCache:
        return LocalCache[URL]
    else:
        resp = requests.get(URL)
        LocalCache[URL] = resp.text
        dumped_json_cache = json.dumps(LocalCache)
        fw = open(CacheFileName, "w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return LocalCache[URL]

def GetRecentNews():
    BaseURL = "https://news.google.com/news/search/section/q/"
    for Coin in Coins:
        try:
            CurrentPageSoup = BeautifulSoup(MakeRequestGoogleCache(BaseURL + Coin.Name), "html.parser")
            NewsArticles = CurrentPageSoup.find_all("c-wiz", {"class": "PaqQNc"})
            for _, Member in zip(range(5), NewsArticles):
                Coin.TopStories.append([Member.find("a", {"class": "nuEeue hzdq5d ME7ew"}).text, Member.find("a", {"class": "nuEeue hzdq5d ME7ew"})["href"]])
        except:
            print("Error Getting Top Stories For", Coin.Name)


Altcoins = ["ETH", "LTC", "XRP", "ZEC", "XMR"]
AltcoinFullNames = ["Ethereum", "Litecoin", "Ripple", "ZCash", "Monero"]
Websites = ["https://www.ethereum.org/", "https://litecoin.org/", "https://ripple.com/", "https://z.cash/", "https://getmonero.org/"]

CacheFileName = "Cache.json"
BitcoinExhcanges = ["Coinbase", "Kraken"]
Altcoins = ["ETH", "LTC", "XRP", "ZEC", "XMR"]

LocalCache = LoadOrCreateCacheFile(CacheFileName)
Connection, Cursor = CreateAndConnectToDatabase()

GetBitcoinPricingData(BitcoinExhcanges, CacheFileName)
GetAltCoinPricingData(Altcoins, CacheFileName)
DeleteZeroEntries(Altcoins, BitcoinExhcanges)
GetPriceOfAltcoinsinUSD(Altcoins)
DeleteNullEntries(Altcoins)

BitCoin = LoadBitcoinDataIntoClass()
Coins = LoadALtcoinDataIntoClass()
Coins.append(BitCoin)
GetRecentNews()

if __name__ == "__main__":
    WebApplication()
