import unittest
from Main import *
import Main
from random import randint

class TestDatabaseStructure(unittest.TestCase):

    def testNumberofTable(self):
        Cursor.execute("SELECT count(*) FROM sqlite_master WHERE type = \"table\" AND name != \"sqlite_sequence\"")
        (Data,) = Cursor.fetchone()
        self.assertEqual(Data, len(Altcoins) + len(BitcoinExhcanges))

    def testNullEntries(self):
        CompleteDatabase = Altcoins + BitcoinExhcanges
        for Coin in CompleteDatabase:
            Cursor.execute("Select Count(*) From {Coin} Where Open Is Null Or Close Is Null or High Is Null Or Low Is Null Or Date Is Null".format(Coin=Coin))
            (Data,) = Cursor.fetchone()
            self.assertEqual(Data, 0)

    def testZeroEntries(self):
        CompleteDatabase = Altcoins + BitcoinExhcanges
        for Coin in CompleteDatabase:
            Cursor.execute("Select Count(*) From {Coin} Where Open = 0.0 Or Close = 0.0 or High = 0.0 Or Low = 0.0 Or Date = 0.0".format(Coin=Coin))
            (Data,) = Cursor.fetchone()
            self.assertEqual(Data, 0)

    def testColumnsBitcoinExchanges(self):
        for Exchange in BitcoinExhcanges:
            Cursor.execute("PRAGMA table_info({Exchange})".format(Exchange=Exchange))
            Data = Cursor.fetchall()
            self.assertEqual(len(Data), 8)

    def testColumnsAltcoins(self):
        for Exchange in Altcoins:
            Cursor.execute("PRAGMA table_info({Exchange})".format(Exchange=Exchange))
            Data = Cursor.fetchall()
            self.assertEqual(len(Data), 9)
            self.assertEqual(Data[-1][1], "PriceUSD")

    def testPricingDataRetreived(self):
        CompleteDatabase = Altcoins + BitcoinExhcanges
        for Coin in CompleteDatabase:
            Cursor.execute("Select Count(*) From {Coin}".format(Coin=Coin))
            (Data,) = Cursor.fetchone()
            self.assertGreater(Data, 100)

class TestCryptoClass(unittest.TestCase):

    def testAllVColumnsHaveSameLength(self):
        for Coin in Coins:
            TempList = [Coin.Open, Coin.Close, Coin.High, Coin.Low, Coin.Date, Coin.WeightedAverage, Coin.PriceUSD]
            L = len(TempList[0])
            self.assertEqual(all(len(x) == L for x in TempList), True)

    def testAllValuesLoadedFromDatabaseAltcoin(self):
        for Coin in Coins[:-1]:
            Cursor.execute("Select Count(*) From {Coin}".format(Coin=Coin.Abbreviation))
            (Data,) = Cursor.fetchone()
            self.assertEqual(Data, len(Coin.Open)+10)

    def testAllValuesLoadedFromDatabaseBitcoin(self):
        Cursor.execute("Select Count(*) From {Coin}".format(Coin="Kraken"))
        (Data,) = Cursor.fetchone()
        self.assertEqual(Data, len(Coins[-1].Open))

    def testBitcoinPriceUSD(self):
        self.assertEqual(set(Coins[-1].WeightedAverage) == set(Coins[-1].PriceUSD), True)

    def testDataCorrectness(self):
        for Coin in Coins[:-1]:
            for Try in range(0,3):
                Index = randint(0,len(Coin.Open)-1)
                Cursor.execute("Select Open, Close, High, Low, WeightedAverage From {Coin} Where Date = \"{Date}\"".format(Coin=Coin.Abbreviation, Date=Coin.Date[Index].strftime("%Y-%m-%d")))
                Data = Cursor.fetchone()
                TempList = (Coin.Open[Index], Coin.Close[Index], Coin.High[Index], Coin.Low[Index], Coin.WeightedAverage[Index])
                self.assertEqual(set(TempList) == set(Data), True)

class TestTopStories(unittest.TestCase):

    def testTopStoriesLength(self):
        for Coin in Coins:
            self.assertEqual(len(Coin.TopStories), 5)

    def testTopStoriesPopulated(self):
        for Coin in Coins:
            for S in Coin.TopStories:
                self.assertNotEqual(S[0], "")
                self.assertNotEqual(S[1], "")

unittest.main()
