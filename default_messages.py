start_message = 'Hi, stranger!\nThis bot can keep track of your crypto portfolio and send you updates with certain intervals\n\
Inspired by CoinMarketCap, created by @lanyadorkin\n\
Source code: https://github.com/lanya-dorkin/LanyaFolioBot'
add_remove_tutorial = 'Add assets with "/add asset amount" command and remove it with "/remove asset amount" (it is simple, right)\n\
For example, to add 0.01 of BTC you should send\n\
    /add BTC 0.01\n\
to remove 0.01 of BTC send\n\
    /remove BTC 0.01\n\
or simply\n\
    /remove BTC all\n\
You can edit the amount with "/edit asset amount" command\n\
To state that your portfolio has 0.05 of ETH you should send\n\
    /edit ETH 0.05\n\
Also you can add, remove or edit assets in batches separating them by a comma like this\n\
    /add BTC 0.01, ETH 0.5\n\n\
To view your portfolio simply use "/portfolio" command\n\
To delete the whole portfolio use "/remove_portfolio"\n\n\
To set the interval you would like to receive updates on your portfolio use "/interval minutes" command specifying the interval in minutes\n\
Avaliable intervals: 15 (15 minutes), 30 (30 minutes), 60 (1 hour), 240 (4 hours), 360 (6 hours), 480 (8 hours), 720 (12 hours), 1440 (1 day), 4320 (3 days)\n\
For example, to receive updates every hour you should send\n\
    /interval 60\n\
To stop receiving updates simply set the interval to 0 or -1'
binance_key_message = 'To import your portfolio send me Binance api key and secret key in two separate messages. Api key first, secret key second. \
Then click Import potfolio once again\n\
It is safer if your api key is in read only mode'