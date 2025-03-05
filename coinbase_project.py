import pprint
import statistics
import urllib
import requests
import time
import os

from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get('coinbase_apikey')


def getEndpoint(endpoint, parameters):
    baseUrl = "https://api.exchange.coinbase.com/"
    resource = baseUrl + endpoint

    headers = {
        "api_key": api_key
    }

    print("Getting Endpoint: " + resource + "?" + urllib.parse.urlencode(parameters))
    response = requests.get(resource, headers=headers, params=parameters)
    response_data = response.json()
    # pprint.pprint(response_data)
    return response_data

service = "products"
endpoint = f"{service}"
parameters = {
}

productResponse = getEndpoint(endpoint, parameters)
for productIndex, productDictionary in enumerate(productResponse):
    if productDictionary['display_name'].endswith('-USD'): # possible products to watch?
        print(productDictionary['display_name'])

products = []
print("Enter the ticker for a Crypto. Type DONE when finished")
while True:
    user_option = input(">").upper()
    if user_option != "DONE":
        user_option = user_option + "-USD"  
        products.append(user_option)
    else:
        break

# products = ['BTC-USD']
for product in products:
    service = "products"
    resource = "candles"
    granularity = 86400 # seconds...so one day granularity
    endpoint = f"{service}/{product}/{resource}"
    parameters = {
        "granularity": granularity
    }

    candleResponse = getEndpoint(endpoint, parameters)
    xTimeValues = []
    yPriceValues = []
    closeList = []
    for candleIndex, candleList in enumerate(candleResponse): # candles are a list of values: time, low, high, open, close, volume
        print(candleList[0])
        xTimeValues.append(int(candleList[0])/granularity) # dividing by granularity to get regression on same time scale as candles
        yPriceValues.append(statistics.mean(candleList[1:5])) # calculating mean for candle
        closeList.append(candleList[4])  # adds close price per day to list

    # SMA50 Indicator
    sma50List = []
    for close in range(50):  # range for 50
        sma50List.append(closeList[close])  # adds 50 closes to list
    fiftyMovingAverage = statistics.mean(sma50List)  # average of 50 day close prices

    # SMA200 Indicator
    sma200List = []
    for close in range(200):  # range for 200
        sma50List.append(closeList[close])  # adds 200 closes to list
    twoHundredMovingAverage = statistics.mean(sma50List)  # average of 200 day close prices

    # Regression Analysis
    daysAgo = 0
    ypred = statistics.linear_regression(xTimeValues, yPriceValues)
    slope = ypred.slope
    int = ypred.intercept
    predTime = candleResponse[daysAgo][0]/granularity
    yval = (slope * predTime) + int
    # print(yval, predTime)
    
    # Support/Resistance
    similarPercent = []
    percentOff = 0.1  # Degree of relevance. Any more is too broad, and any less is too constrictive

    for i in range(len(closeList)):
        for j in range(i + 1, len(closeList)):
            price_i = closeList[i]
            price_j = closeList[j]
            upperBound = price_i * (1 + percentOff)  # adds the upper level of the degree
            lowerBound = price_i * (1 - percentOff)  # lower level of the degree of relevance
            if lowerBound <= price_j <= upperBound:  # checks if the price level falls within 10% in either direction
                if price_j not in similarPercent:
                    similarPercent.append(price_j)
    # print(similarPercent)
    for i in range(len(similarPercent)):
        for j in range(i + 1, len(similarPercent)):  # same process as before, but looped
            price_i = closeList[i]
            price_j = closeList[j]
            upperBound = price_i * (1 + percentOff)
            lowerBound = price_i * (1 - percentOff)
            if lowerBound <= price_j <= upperBound:
                similarPercent.pop(i)  # removes duplicate levels of support and resistance within 10% of each other
    # print('Key Support/Resistance Levels')
    # print(similarPercent)

    # Recommendation
    print('----------------')
    print(f"\033[1m{product}\033[0m")
    sentiment = 0  # range 1-3 by end of indicators, then calls a list
    currentPrice = closeList[0]
    print('Current Price: $' + str(currentPrice))
    time.sleep(.5)  # time.sleep functions allow for better interface
    print('50 Day SMA: $' + str(fiftyMovingAverage))
    time.sleep(.5)
    print('200 Day SMA: $' + str(twoHundredMovingAverage))
    time.sleep(.5)

    upperBoundFifty = fiftyMovingAverage * (1 + percentOff)
    lowerBoundFifty = fiftyMovingAverage * (1 - percentOff)
    if lowerBoundFifty <= twoHundredMovingAverage <= upperBoundFifty and fiftyMovingAverage < twoHundredMovingAverage:  # checks if the SMA50 and SMA200 is close enough for eligible crossover
        print("SMA50 < SMA200 : \033[1mSELL\033[0m")
        sentiment -= 1  # Sell signals lower sentiment
    elif lowerBoundFifty <= twoHundredMovingAverage <= upperBoundFifty and fiftyMovingAverage > twoHundredMovingAverage:
        print("SMA50 > SMA200 : \033[1mBUY\033[0m")
        sentiment += 1  # buy signals raise sentiment
    else:
        print("SMA50 NOT CLOSE ENOUGH TO SMA200 : \033[1mHOLD\033[0m")

    time.sleep(.5)

    print("Support/Resistance Levels @", similarPercent)
    time.sleep(.5)
    upperBoundPrice = currentPrice * (1 + percentOff)
    lowerBoundPrice = currentPrice * (1 - percentOff)
    x = 0
    for level in similarPercent:
        if lowerBoundPrice <= level <= upperBoundPrice:  # checks if current price is within 10% of a critical price level
            print("\033[1m$" + str(level), "is within", str(percentOff*100) + "% of $" + str(currentPrice), "\033[0m")
            sentiment += 1
            x += 1
    if x == 0:
        print("No Support/Resistance are within", str(percentOff*100) + "% of $" + str(currentPrice), ": \033[1mHOLD\033[0m")  # not within range of price

    time.sleep(.5)
    yval = round(yval, 2)
    print("$" + str(yval), "predicted price with Regression Analysis")
    marginOfError = ((currentPrice/yval) - 1) * 100  # checks the predicted regession price to the current price
    time.sleep(.5)
    print("Price is", str(round(marginOfError, 2)) + "% away from current price of $" + str(currentPrice))
    time.sleep(.5)
    if marginOfError > 0:  # if the price is above predicted, it is over valued
        print("Price is above predicted : OVERVALUED : \033[1mSELL\033[0m")
        sentiment -= 1
    elif marginOfError < 0:  # if price is below predicted, undervalued
        print("Price is below predicted : UNDERVALUED : \033[1mBUY\033[0m")
        sentiment += 1
    else:
        print("Price is at predicted : VALUE : \033[1mHOLD\033[0m")

    time.sleep(.5)

    buyList = ['WEAK BUY', 'BUY', 'STRONG BUY']  # sentiment serves as index call for these lists
    sellList = ['WEAK SELL', 'SELL', 'STRONG SELL']
    if sentiment < 0:
        sentiment = sentiment * -1
        verdict = sellList[sentiment - 1]
    elif sentiment > 0:
        verdict = buyList[sentiment - 1]
    else:
        verdict = "HOLD"
    print('RECOMMENDATION :', f"\033[1m{verdict}\033[0m")



