from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


default_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

delete_key_button = KeyboardButton('Delete api keys')
import_portfokio_button = KeyboardButton('Import portfolio')
show_portfolio_button = KeyboardButton('Show portfolio')
remove_portfolio_button = KeyboardButton('Remove portfolio')
interval_button = KeyboardButton('Set interval')
help_button = KeyboardButton('Help')

default_keyboard = default_keyboard.row(remove_portfolio_button, show_portfolio_button).row(delete_key_button, import_portfokio_button).add(help_button, interval_button)

yes_button = KeyboardButton('Yes, delete my whole portfolio')
no_button = KeyboardButton('Nope, forget it')

confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(no_button, yes_button)

interval_button1 = InlineKeyboardButton('15 minutes', callback_data='setting interval 15')
interval_button2 = InlineKeyboardButton('30 minutes', callback_data='setting interval 30')
interval_button3 = InlineKeyboardButton('1 hour', callback_data='setting interval 60')
interval_button4 = InlineKeyboardButton('4 hours', callback_data='setting interval 240')
interval_button5 = InlineKeyboardButton('6 hours', callback_data='setting interval 360')
interval_button6 = InlineKeyboardButton('8 hours', callback_data='setting interval 480')
interval_button7 = InlineKeyboardButton('12 hours', callback_data='setting interval 720')
interval_button8 = InlineKeyboardButton('1 day', callback_data='setting interval 1440')
interval_button9 = InlineKeyboardButton('3 days', callback_data='setting interval 4320')
interval_button10 = InlineKeyboardButton('Never', callback_data='setting interval 0')

interval_keybord = InlineKeyboardMarkup().add(interval_button1, interval_button2, interval_button3, interval_button4, interval_button5, 
                                              interval_button6, interval_button7, interval_button8, interval_button9, interval_button10)

binance_button = InlineKeyboardButton('Binance', callback_data='binance')
import_select_keyboard = InlineKeyboardMarkup().add(binance_button)