from pyogre import api
import json
import time
import six
import logging

logger = logging.getLogger("ogredump")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class ogrebot(object):
    def __init__(self, sfile="settings.json"):
        try:
            with open(sfile) as f:
                self.settings = json.load(f)
        except Exception:
            raise Exception("Settings file is not a proper json file")

        self.api = api(self.settings.get("apikey"), self.settings.get("apisecret"))
        logger.info("Ogrebot started")
        self.minsize = 0.0001

    def iterbalances(self, skipzero=True):
        # yields: symbolname, available balance, junk balance, ordered balance, ask price
        for symbol, balance in six.iteritems(self.api.balances()["balances"]):
            if symbol == "BTC":
                yield "BTC", balance, 0, 0, 1.0, "hodl"
            else:
                if skipzero and not balance:
                    continue
                ask, strategy = self.get_askstrategy(symbol)
                if not ask:
                    continue
                if balance and ask:
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
                yield symbol, abalance, jbalance, obalance, ask, strategy

    def iterbtcbalances(self):
        for symbol, abalance, jbalance, obalance, ask, _ in self.iterbalances():
            if symbol == "BTC":
                obtc = obalance
            else:
                orders = self.api.myorders("BTC-%s" % symbol)
                obtc = 0
                for order in orders:
                    if order["type"] == "sell":
                        obtc += order["price"] * order["quantity"]
            yield symbol, abalance * ask, jbalance * ask, obtc

    def get_askstrategy(self, symbol):
        market = "BTC-%s" % symbol
        strategy = self.settings.get("strategies", {}).get(market, "hodl").lower()
        orders = self.api.orders(market)
        if len(orders["buy"]):
            maxbuy = max(orders["buy"])
        else:
            maxbuy = None
        if len(orders["sell"]):
            minsell = min(orders["sell"].keys())
        else:
            minsell = None

        if strategy == "selltake":
            ask = maxbuy
        elif strategy == "sellmake":
            ask = minsell
        elif strategy == "sellmakelow":
            if (minsell - 1e-8) > maxbuy:
                ask = minsell - 1e-8
            else:
                ask = maxbuy
        elif strategy == "hodl":
            ask = maxbuy
            # check your volume on over all volume
        return ask, strategy

    def dump(self):
        for symbol, abalance, _jbalance, _obalance, ask, strategy in self.iterbalances():
            if symbol == "BTC" or strategy == "hodl":
                continue
            if abalance:
                size = abalance * ask
                market = "BTC-%s" % symbol
                logger.info("EXECUTING ORDER: AMOUNT: %s%s, PRICE %.8fBTC: SIZE:%.8fBTC" % (
                    abalance, symbol, ask, size))
                order = self.api.sellorder(market, abalance, ask)
                if order["success"]:
                    uuid = order["uuid"]
                    if uuid:
                        logger.info("ORDER PLACED SUCCESSFULLY: UUID: %s" % order["uuid"])
                    else:
                        logger.info("ORDER SOLD SUCCESSFULLY: AMOUNT: %sBTC" % size)
                else:
                    logger.warning("ORDER FAILED: %s" % order.get("error"))


if __name__ == "__main__":
    bot = ogrebot()
    while True:
        bot.dump()
        time.sleep(30)
