from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher.filters import Command
import asyncio
import aioschedule
import requests
import json
import sqlite3
import pandas as pd
from time import time
from datetime import datetime
from binance import AsyncClient

from config import bot_token
from default_messages import *
from keyboards import *


bot = Bot(token=bot_token)
dp = Dispatcher(bot)

async def update_binance_data():
    req = requests.get('https://api.binance.com/api/v3/ticker/24hr')
    if req.status_code == 200:
        res = json.loads(req.text)
        with sqlite3.connect('database.db') as connect:
            cursor = connect.cursor()
            cursor.execute("DELETE FROM binance_data")
            cursor.execute("INSERT INTO binance_data VALUES (:symbol, :price_change, :last_price);", {'symbol': 'USDT', 'price_change': 0, 'last_price': 1})
            for r in res:
                if r['symbol'].endswith('USDT'):
                    symbol = r['symbol'].replace('USDT', '')
                    price_change = float(r['priceChangePercent'])
                    last_price = float(r['lastPrice'])
                    cursor.execute("INSERT INTO binance_data VALUES (:symbol, :price_change, :last_price);", {'symbol': symbol, 'price_change': price_change, 'last_price': last_price})
            connect.commit()
        print(f'{datetime.utcfromtimestamp(int(time())).strftime("%Y-%m-%d %H:%M:%S")}: updated Binance data')

async def send_update_to_id(id, connect, b_data):
    cursor = connect.cursor()
    cursor.execute("SELECT * FROM quotes WHERE id=:id", {'id': id})
    data = cursor.fetchall()
    if data != []:
        to_return_list = []
        for asset_row in data:
            asset = asset_row[1]
            amount = asset_row[2]
            asset_value = asset_row[2] * b_data["last_price"][asset]
            p_change = b_data["24h_change"][asset]/100
            abs_change = asset_value - 1 / (1 + p_change) * asset_value
            to_return_list.append({'asset': asset, 'amount': amount, 'asset_value': asset_value, 'p_change': p_change, 'abs_change': abs_change})
        to_return_list = sorted(to_return_list, key=lambda d: abs(d['abs_change']), reverse=True)
        to_return = ''
        sum_asset_value = 0
        sum_abs_change = 0
        for row in to_return_list:
            sum_asset_value += row["asset_value"]
            sum_abs_change += row["abs_change"]
            to_return += f'{row["amount"]} {row["asset"]} ~ {round(row["asset_value"], 2)} USDT | {round(row["abs_change"], 2)} USDT ({round(row["p_change"]*100, 2)}%)\n'
        prev_sum_asset_value = sum_asset_value - sum_abs_change
        sum_asset_value_p_change = (sum_asset_value - prev_sum_asset_value) / prev_sum_asset_value
        to_return += f'\nPortfolio value ~ {round(sum_asset_value, 2)} USDT | {round(sum_abs_change, 2)} USDT ({round(sum_asset_value_p_change*100, 2)}%)'
        await bot.send_message(id, to_return)
        print(f'{datetime.utcfromtimestamp(int(time())).strftime("%Y-%m-%d %H:%M:%S")}: sent update to {id}')
    else:
        return 'Your portfolio is empty'

async def send_updates(interval):
    
    with sqlite3.connect('database.db') as connect:
        b_data = pd.read_sql('SELECT * FROM binance_data', connect, index_col='asset')
        cursor = connect.cursor()
        cursor.execute("SELECT id FROM users WHERE interval=:interval", {'interval': interval})
        data = cursor.fetchall()
        ids = list(map(lambda d: d[0], data))
        tasks = []
        for id in ids:
            tasks.append(send_update_to_id(id, connect, b_data))
        await asyncio.gather(*tasks)

async def scheduler():
    aioschedule.every(15).minutes.do(update_binance_data)
    aioschedule.every(15).minutes.do(send_updates, 15)
    aioschedule.every(30).minutes.do(send_updates, 30)
    aioschedule.every(60).minutes.do(send_updates, 60)
    aioschedule.every(240).minutes.do(send_updates, 240)
    aioschedule.every(360).minutes.do(send_updates, 360)
    aioschedule.every(480).minutes.do(send_updates, 480)
    aioschedule.every(720).minutes.do(send_updates, 720)
    aioschedule.every(1440).minutes.do(send_updates, 1440)
    aioschedule.every(4320).minutes.do(send_updates, 4320)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    await update_binance_data()
    asyncio.create_task(scheduler())

@dp.message_handler(Command('start'))
@dp.message_handler(Command('help'))
@dp.message_handler(lambda message: message.text and 'help' in message.text.lower())
async def start(message):
    
    id = message['from']['id']
    date = message['date']
    username = message['from']['username']
    
    with sqlite3.connect('database.db') as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM users WHERE id=:id", {'id': id})
        data = cursor.fetchone()
        
        if data is None:
            cursor.execute("INSERT INTO users VALUES (:id, :date, :username, :interval, :api_key, :secret_key)", 
                           {'id': id, 'date': date, 'username': username, 'interval': 0, "api_key": 'null', "secret_key": 'null'})
        connect.commit()
    
    if 'help' not in message['text'].lower():
        await message.answer(start_message)
    await message.answer(add_remove_tutorial, reply_markup=default_keyboard)

@dp.message_handler(Command('add'))
async def add_asset(message):
    
    id = message['from']['id']
    text = message.text.replace('/add', '')
    asset_amount_pairs = text.split(',')
    
    for pair in asset_amount_pairs:
        pair = pair.strip()
        asset = pair.split(' ')[0].upper().strip()
        add_amount = float(pair.split(' ')[1].strip())
        if add_amount <= 0:
            await message.answer(f'{asset}: the amount should be positive')
            continue
        with sqlite3.connect('database.db') as connect:
            cursor = connect.cursor()
            cursor.execute("SELECT asset FROM binance_data")
            assets = cursor.fetchall()
            assets_list = list(map(lambda d: d[0], assets))
        if not asset in assets_list:
            await message.answer(f'{asset}: there is no such asset on Binance')
            continue
        
        with sqlite3.connect('database.db') as connect:
            cursor = connect.cursor()
            
            cursor.execute("SELECT amount FROM quotes WHERE id=:id AND asset=:asset", {'id': id, 'asset': asset})
            data = cursor.fetchone()

            if not data is None:
                cursor.execute("UPDATE quotes SET amount=:new_amount WHERE id=:id AND asset=:asset;", {'id': id, 'asset': asset, 'new_amount': data[0] + add_amount})
                await message.answer(f'{asset}: added {add_amount} -> {data[0] + add_amount} in your portfolio')
            else:
                cursor.execute("INSERT INTO quotes VALUES (:id, :asset, :amount);", {'id': id, 'asset': asset, 'amount': add_amount})
                await message.answer(f'{asset}: added {add_amount} -> {add_amount} in your portfolio')
            connect.commit()

@dp.message_handler(Command('remove'))
async def remove_asset(message):
    id = message['from']['id']
    text = message.text.replace('/remove', '')
    asset_amount_pairs = text.split(',')

    for pair in asset_amount_pairs:
        pair = pair.strip()
        asset = pair.split(' ')[0].upper().strip()
        remove_amount = pair.split(' ')[1].strip()
        
        if remove_amount != 'all':
            remove_amount = float(remove_amount)

            if remove_amount <= 0:
                await message.answer(f'{asset}: the amount should be positive')
                continue
        
        with sqlite3.connect('database.db') as connect:
            cursor = connect.cursor()
            
            cursor.execute("SELECT amount FROM quotes WHERE id=:id AND asset=:asset", {'id': id, 'asset': asset})
            data = cursor.fetchone()

            if not data is None:
                if (remove_amount == 'all') or (data[0] - remove_amount <= 0):
                    cursor.execute("DELETE FROM quotes WHERE id=:id AND asset=:asset", {'id': id, 'asset': asset})
                    await message.answer(f'{asset}: removed all -> 0 in your portfolio')
                else:
                    cursor.execute("UPDATE quotes SET amount=:new_amount WHERE id=:id AND asset=:asset", {'id': id, 'asset': asset, 'new_amount': data[0] - remove_amount})
                    await message.answer(f'{asset}: removed {remove_amount} -> {data[0] - remove_amount} in your portfolio')
                connect.commit()
            else:
                await message.answer(f'{asset}: there is none in your portfolio')

@dp.message_handler(Command('edit'))
async def edit_asset(message):
    id = message['from']['id']
    text = message.text.replace('/edit', '')
    asset_amount_pairs = text.split(',')
    
    for pair in asset_amount_pairs:
        pair = pair.strip()
        asset = pair.split(' ')[0].upper().strip()
        edit_amount = float(pair.split(' ')[1].strip())

        if edit_amount <= 0:
            await message.answer(f'{asset}: the amount should be positive')
            continue

        with sqlite3.connect('database.db') as connect:
            cursor = connect.cursor()
            
            cursor.execute("SELECT amount FROM quotes WHERE id=:id AND asset=:asset", {'id': id, 'asset': asset})
            data = cursor.fetchone()

            if not data is None:
                cursor.execute("UPDATE quotes SET amount=:new_amount WHERE id=:id AND asset=:asset", {'id': id, 'asset': asset, 'new_amount': edit_amount})
                await message.answer(f'{asset}: edited {edit_amount} -> {edit_amount} in your portfolio')
            else:
                await message.answer(f'{asset}: there is none in your portfolio')

@dp.message_handler(Command('portfolio'))
@dp.message_handler(lambda message: 'show portfolio' in message.text.lower())
async def show_portfolio(message):
    id = message['from']['id']
    with sqlite3.connect('database.db') as connect:
        b_data = pd.read_sql('SELECT * FROM binance_data', connect, index_col='asset')
        
        res = await send_update_to_id(id, connect, b_data)
        if not res is None:
            await message.answer(res)

@dp.message_handler(lambda message: 'import portfolio' in message.text.lower())
async def import_portfolio(message):
    with sqlite3.connect('database.db') as connect:
        id = message['from']['id']
        cursor = connect.cursor()
        cursor.execute("SELECT api_key, secret_key FROM users where id=:id", {'id': id})
        data = cursor.fetchall()
        if data == [('null', 'null')]:
            await message.answer('Which source to  use?', reply_markup=import_select_keyboard)
        else:
            api_key = data[0][0]
            secret_key = data[0][1]
            client = await AsyncClient.create(api_key, secret_key)
            info = await client.get_account()
            info = list(map(lambda x: {"asset": x['asset'].replace('LD', ''), "total": float(x['free']) + float(x['locked'])}, info['balances']))
            await client.close_connection()
            non_zero = [d for d in info if (d['total'] != 0) and (not d['asset'].startswith('LD'))]
            cursor.execute("DELETE FROM quotes WHERE id=:id", {'id': id})
            for row in non_zero:
                cursor.execute("INSERT INTO quotes VALUES (:id, :asset, :amount);", {'id': id, 'asset': row['asset'], 'amount': row['total']})
                await message.answer(f'{row["asset"]}: added {row["total"]} -> {row["total"]} in your portfolio')

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('binance'))
async def process_callback(callback_query):
    id = callback_query['from']['id']
    await bot.send_message(id, binance_key_message)

@dp.message_handler(lambda message: len(message.text) == 64)
async def read_api_key(message):
    with sqlite3.connect('database.db') as connect:
        id = message['from']['id']
        cursor = connect.cursor()
        cursor.execute("SELECT api_key, secret_key FROM users where id=:id", {'id': id})
        data = cursor.fetchall()
        if data[0][0] == 'null':
            cursor.execute("UPDATE users SET api_key=:api_key WHERE id=:id", {'id': id, 'api_key': message['text']})
            connect.commit()
            await message.answer('Send me your secret key now')
        elif data[0][1] == 'null':
            cursor.execute("UPDATE users SET secret_key=:api_key WHERE id=:id", {'id': id, 'api_key': message['text']})
            connect.commit()
            await message.answer('Got  it. Now you can click Import portfolio once again')

@dp.message_handler(lambda message: 'delete api keys' in message.text.lower())
async def delete_api_keys(message):
    id = message['from']['id']
    with sqlite3.connect('database.db') as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT api_key, secret_key FROM users WHERE id=:id", {'id': id})
        data = cursor.fetchall()    
        if data == [('null', 'null')]:
            await message.answer('They are already empty')
        else:
            cursor.execute("UPDATE users SET api_key=:api_key, secret_key=:secret_key WHERE id=:id", {'id': id, 'api_key': 'null', 'secret_key': 'null'})
            connect.commit()
            await message.answer('Done')

@dp.message_handler(lambda message: 'remove portfolio' in message.text.lower())
async def remove_confirm(message):
    await message.answer('Are you sure?', reply_markup=confirm_keyboard)

@dp.message_handler(lambda message: 'nope, forget it' in message.text.lower())
async def return_to_default_keyboard(message):
    await message.answer('Nevermind', reply_markup=default_keyboard)

@dp.message_handler(Command('remove_portfolio'))
@dp.message_handler(lambda message: 'yes, delete my whole portfolio' in message.text.lower())
async def remove_portfolio(message):
    id = message['from']['id']
    with sqlite3.connect('database.db') as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM quotes WHERE id=:id", {'id': id})
        data = cursor.fetchall()
        
        if data != []:
            cursor.execute("DELETE FROM quotes WHERE id=:id", {'id': id})
            connect.commit()
            await message.answer('Done, your portfolio is empty', reply_markup=default_keyboard)
        else:
            await message.answer('Your portfolio is already empty', reply_markup=default_keyboard)

@dp.message_handler(Command('interval'))
async def change_interval(message):
    id = message['from']['id']
    interval = int(message.text.replace('/interval', '').strip())
    with sqlite3.connect('database.db') as connect:
        cursor = connect.cursor()
        cursor.execute("UPDATE users SET interval=:new_interval WHERE id=:id", {'id': id, 'new_interval': interval})
        connect.commit()
        await message.answer(f'Your interval is {interval} minutes now')

@dp.message_handler(lambda message: 'set interval' in message.text.lower())
async def choose_interval(message):
    await message.answer('Okay, with what interval would you like to receive updates?', reply_markup=interval_keybord)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('setting interval'))
async def process_callback(callback_query):
    id = callback_query['from']['id']
    interval = int(callback_query.data.split(' ')[-1])
    with sqlite3.connect('database.db') as connect:
        cursor = connect.cursor()
        cursor.execute("UPDATE users SET interval=:new_interval WHERE id=:id", {'id': id, 'new_interval': interval})
        connect.commit()
    await bot.send_message(id, 'Got it')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
