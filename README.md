# Cryptocurrency-Markets-

## Data Sources:

1. **Bitcoin Prices:** [Quandl API](https://www.quandl.com/collections/markets/bitcoin-data), *API Key Required* 
2. **Altcoin Prices:** [Polenix API](https://poloniex.com/support/api/), *No API Key Required*
3. **Top Stories Relating To Cryptocurrencies**: Google News

API Key Should be Stored in *Secrets.py*: `QuandlAPiKey = "Your API Key"`

## Table Relation In Database
* Bitcoin Prices are retreived in USD where as the Altcoins prices are retrieved in term of Bitcoin price at that time
* To convert the Altcoin prices in USD the program extracts the Bitcoin price for each day from the Bitcoin Kraken table and multiplies it by the ALtcoin value to the convert the Altcoin prices in terms of USD

## Code Organization:

1. `GetBitcoinPricingData()` and `GetAltCoinPricingData()` get the data from the sources and store them in the database.
2. `LoadBitcoinDataIntoClass()` Create a Crypto class of each crypto and stores relevant information such as Name, Abbreviation, Website and Pricing Data from Database
3. `GetRecentNews()` get the top stories for the cryptocurrencies
4. `WebApplication()` uses the Dash framework to display the graphs on the local website along with the top stories

## Run: `python Main.py` to begin
