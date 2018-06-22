ogredump is a bot that dumps your bots to btc on defined strategies:

installation:

download the zip bal and extract to folder

run:

pip -r requrements.txt

copy settings-sample.json to settings.json

edit settings json with your

apikey
apisecret

and the strategies per symbol pair:

there are 3 strategies defined yet:

1) sellmake: the asset will be sold in lowest price in the available selloders
2) sellmakelow: the asset will be sold in lowest price -1 satoshi
3) selltake: the asset will be sold in the highest buy orders available

if there is no any strategy defined for the symbol pair in the settings, and you still have available amounts of asset the account, bot automatically sells them with "selltake" strategy.

This is a WIP and will be improved by time.