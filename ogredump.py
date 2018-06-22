from pyogre import api
import json
import urllib2
from xml.dom import minidom
import texttable


class ogrebot(object):
    def __init__(self, sfile="settings.json"):
        try:
            with open("settings.json") as f:
                self.settings = json.load(f)
        except:
            raise Exception("Settings file is not a proper json file")

        self.api = api(self.settings.get("apikey"), self.settings.get("apisecret"))
        self.minsize = 0.0001
        self.exchanges()
        
    def exchanges(self):
        self.usd = {}
        exchanges = minidom.parse(urllib2.urlopen("http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"))
        for symbol in exchanges.getElementsByTagName("Cube"):
            currency = symbol.attributes.get("currency")
            if currency:
                if currency.value == "USD":
                    self.usd["EUR"] = 1 / float(symbol.attributes["rate"].value)
                else:
                    self.usd[currency.value] = float(symbol.attributes["rate"].value) * self.usd["EUR"]
                
    
    @staticmethod
    def btcusd():
        bcinfo = json.loads(urllib2.urlopen("https://blockchain.info/ticker").read())
        return bcinfo["USD"]["15m"]
        
    def iterbalances(self, skipzero=True):
        # yields: symbolname, available balance, junk balance, ordered balance, ask price
        for symbol, balance in self.api.balances()["balances"].iteritems():
            if symbol == "BTC":
                yield "BTC", balance, 0, 0, 1.0
            else:
                if skipzero and not balance:
                    continue
                ask = self.getask(symbol)
                if balance:
                    abalance = self.api.balance(symbol)["available"]
                    size = abalance * ask
                    if size < self.minsize:
                        jbalance = abalance
                        abalance = 0
                    else:
                        jbalance = 0
                else:
                    abalance = 0
                    jbalance = 0
                obalance = balance - abalance - jbalance
                yield symbol, abalance, jbalance, obalance, ask
                
    def iterbtcbalances(self):
        for symbol, abalance, jbalance, obalance, ask in self.iterbalances():
            if symbol == "BTC":
                obtc = obalance
            else:
                orders = self.api.myorders("BTC-%s" % symbol)
                obtc = 0
                for order in orders:
                    if order["type"] == "sell":
                        obtc += order["price"] * order["quantity"]
            yield symbol, abalance * ask, jbalance * ask, obtc
            
    def iterfiatbalances(self, fiat=None):
        usdbtc = self.btcusd()
        if fiat and self.usd.get(fiat.upper()):
            frate = self.usd[fiat.upper()] * usdbtc
        else:
            frate = usdbtc    
        for symbol, abalance, jbalance, obalance in self.iterbtcbalances():
            yield symbol, abalance * frate, jbalance * frate, obalance * frate

    def printbalances(self, symbol=None):
        if not symbol:
            callback = self.iterbalances
            args = ()
        elif symbol.lower() == "btc":
            callback = self.iterbtcbalances
            args = ()
        else:
            callback = self.iterfiatbalances
            args = (symbol,)
        table = texttable.Texttable()
        table.set_precision(8)
        table.add_row(["SYMBOL/%s" % symbol, "TOTAL", "AVAILABLE", "JUNK", "ORDERED"])
        sum0 = sum1 = sum2 = sum3 = 0
        for ret in callback(*args):
            total = ret[1] + ret[2] + ret[3]
            table.add_row([ret[0], total, ret[1], ret[2], ret[3]])
            sum0 += total
            sum1 += ret[1]
            sum2 += ret[2]
            sum3 += ret[3]
        if symbol:
            table.add_row(["TOTAL", sum0, sum1, sum2, sum3])
        print table.draw()

    def getask(self, symbol):
        market = "BTC-%s" % symbol
        strategy = self.settings.get("strategies", {}).get(market, "selltake")
        orders = self.api.orders(market)
        if strategy == "selltake":
            ask = max(orders["buy"].keys())
        elif strategy == "sellmake":
            ask = min(orders["sell"].keys())
        elif strategy == "sellmakelow":
            asklow = min(orders["sell"].keys()) - 1e-8
            buymax = max(orders["buy"].keys())
            if asklow > buymax:
                ask = asklow
            else:
                ask = buymax
            # check your volume on over all volume
        return ask
    
    def dump(self):
        for symbol, abalance, jbalance, obalance, ask in self.iterbalances():
            if symbol == "BTC":
                continue
            if abalance:
                size = abalance * ask
                market = "BTC-%s" % symbol
                print "EXECUTING ORDER: AMOUNT: %s%s, PRICE %.8fBTC: SIZE:%.8fBTC" % (abalance,
                                                                                      symbol,
                                                                                      ask,
                                                                                      size)
                order = self.api.sellorder(market, abalance, ask)
                if order["success"]:
                    uuid = order["uuid"]
                    if uuid:
                        print "ORDER PLACED SUCCESSFULLY: UUID: %s" % order["uuid"]
                    else:
                        print "ORDER SOLD SUCCESSFULLY: AMOUNT: %sBTC" % size
                else:
                    print "ORDER FAILED: %s" % order.get("error")
                            
                            
bot = ogrebot()
"""
bot.printbalances()
bot.printbalances("btc")
bot.printbalances("usd")
bot.printbalances("try")
"""
bot.dump()
bot.printbalances("usd")