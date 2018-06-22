ogredump is a bot that dumps your crypto assets to btc on TradeOfre with defined strategies:

installation:

download the zip ball and extract to folder

run:

pip -r requirements.txt

copy settings-sample.json to settings.json

edit settings json with your

apikey
apisecret

and the strategies per symbol pair, there are 3 strategies defined yet:

1) sellmake: the asset will be sold with the lowest price in the available selloders
2) sellmakelow: the asset will be sold with lowest price -1 satoshi
3) selltake: the asset will be sold with the highest buy orders available

if there is no any strategy defined for the symbol pair in the settings.json, and you still have available amounts of asset the account, bot automatically sells them with "selltake" strategy.

This is a WIP and will be improved by time.