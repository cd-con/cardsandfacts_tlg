import configparser
import logging
import os
import random
import sqlite3
import datetime

import telebot

import menu
import settings
import io, urllib

# Настройки логгера

mainLogger = logging.getLogger(name='Runtime')
mainLogger.setLevel(logging.INFO)
logFileHandler = logging.FileHandler("test.log", mode='w')
logFileHandler.setFormatter(logging.Formatter('%(asctime)s in %(name)s [%(levelname)s] >> %(message)s'))
mainLogger.addHandler(logFileHandler)
# Настройки логгера

mainLogger.info(f"Logger successfully inited")
mainLogger.info(f"Loading configuration file")
isDebug = False

# Проверка наличия файла конфигурации / загрузка конфигурации
if not os.path.exists(settings.configPath):
    mainLogger.warning(f"Couldn't find file {settings.configPath}. Creating another one for you")
    mainLogger.warning(f"Don't forget to fill this file with your data")
    config = configparser.ConfigParser()
    config.add_section("botInfo")
    config.set("botInfo", "version", "0.1")
    config.set("botInfo", "UUID", "000-000000-CAF2021")
    config.add_section("debug")
    config.set("debug", "isDebug", "True")
    config.add_section("telebot")
    config.set("telebot", "token", "[YOUR TOKEN HERE]")
    config.add_section("database")
    config.set("database", "userdb_address", "userbase.db")
    config.set("database", "collectiondb_address", "cardbase.db")
    try:
        with open(settings.configPath, "w") as config_file:
            config.write(config_file)
        mainLogger.info(f"File successfully created!")
    except Exception as e:
        mainLogger.critical(f"Some error occurred. Detailed info >> {e}")
    finally:
        mainLogger.warning(f"App will be stopped immediately")
        exit()
else:
    try:
        config = configparser.ConfigParser()
        config.read(settings.configPath)
        bot = telebot.TeleBot(config.get("telebot", "token"))  # получение токена из конфигурационного файла

        mainLogger.info(
            f"Launching CardsAndFacts Telegram bot, a bot for upgrading your brain!"
            f" Version {config.get('botInfo', 'version')}")
        mainLogger.info(
            f'Your UUID is "{config.get("botInfo", "UUID")}". '
            f'Use it when contacting with staff to get personalized help')

        if config.get("debug", "isDebug").upper() == 'TRUE':
            mainLogger.setLevel(logging.DEBUG)
            mainLogger.debug('Debug mode activated! Log will be filled with [DEBUG] spam :)')
    except Exception as e:
        mainLogger.critical(f"Some error occurred. Detailed info >> {e}")
        mainLogger.warning(f"App will be stopped immediately")
        exit()


def say_to_db(string, type='cards'):
    if type == 'user':
        connection = sqlite3.connect(config.get("database", "userdb_address"))
    else:
        connection = sqlite3.connect(config.get("database", "collectiondb_address"))
    cursor = connection.cursor()
    result = cursor.execute(string).fetchall()
    connection.commit()
    return result


def loadmenu(collectionname):
    try:
        row = say_to_db(f"SELECT * FROM '{collectionname}'")
        result_menu = telebot.types.InlineKeyboardMarkup(row_width=2)
        result_menu.add(telebot.types.InlineKeyboardButton(text='🕹️ Тест', callback_data='playtest'),
                        telebot.types.InlineKeyboardButton(text='❤', callback_data=f'like_{collectionname}'))
        for i in row:
            result_menu.add(telebot.types.InlineKeyboardButton(text=f'{i[0]}', callback_data=f'{i[0]}'))
        result_menu.add(telebot.types.InlineKeyboardButton(text='🔙 Назад', callback_data='play'))
        return result_menu
    except Exception as dberror:
        mainLogger.error(f'DB operation error: {dberror}')
        err_menu = telebot.types.InlineKeyboardMarkup(row_width=1)
        err_menu.add(telebot.types.InlineKeyboardButton(text='Здесь ничего нет :)', callback_data='play'))
        err_menu.add(telebot.types.InlineKeyboardButton(text='🔙 Назад', callback_data='play'))
        return err_menu


def getcard(collectionname, cardname):
    try:
            rawcard = say_to_db(f"SELECT * FROM '{collectionname}' WHERE front = '{cardname}'")
            if not [x[0] for x in rawcard] == []:
                front = [x[0] for x in rawcard]
                back = [x[1] for x in rawcard]
                picture = [x[2] for x in rawcard]
                return (front,
                        back,
                        picture)
            return 'Nani?'
    except Exception as dbcarderror:
        mainLogger.error(f"DB can't get card {cardname} from {collectionname}: {dbcarderror}")


def findcardincollection(chatid):
    try:
        result = getcollections('n', [x[0] for x in say_to_db(
            f"SELECT selectedcollection FROM users WHERE userid='{chatid}'", type="user")][0])
        if result == []:
            return [f'{random.randint(111111,999999)}']
        else:
            return result
    except Exception as error:
        mainLogger.error(f"DB can't find: {error}")


def getcollections(getinfo, search):
    try:
        row = say_to_db('SELECT * FROM collections')
        mainLogger.debug(f'DB response for getcollections({getinfo},{search}): {row}')
        sections = []
        if getinfo == 'n':
            if search != 'pass':
                sections = [x[0] for x in row if search in x]
            else:
                sections = [x[0] for x in row]
        if getinfo == 'a':
            if search != 'pass':
                sections = [x[1] for x in row if search in x]
            else:
                sections = [x[1] for x in row]
        if getinfo == 'w':
            if search != 'pass':
                sections = [x[2] for x in row if search in x]
            else:
                sections = [x[2] for x in row]
        return sections
    except Exception as dberr:
        mainLogger.error(f"DB operation error: {dberr}")
        return 'Ошибка!'


# обработка сообщений
@bot.message_handler(commands=['start'])
def start_message(message):
    mainLogger.debug(f"User @{message.from_user.username} triggered command {message.text}")
    try:
        if [x[0] for x in say_to_db(f"SELECT userid FROM users WHERE userid = '{message.chat.id}' LIMIT 1;", type="user")] == []:
            print('PASSED')
            say_to_db(
                f"INSERT OR REPLACE INTO users(userid,username,selectedcollection, level) VALUES "
                f"('{message.chat.id}','{message.from_user.first_name}','Empty', 0)", type="user")
            say_to_db(f"CREATE TABLE IF NOT EXISTS '{message.chat.id}_{message.from_user.first_name}'"
                      f" (favcoll TEXT, added DATE);",type="user")
            say_to_db(f"INSERT OR REPLACE INTO '{message.chat.id}_{message.from_user.first_name}'"
                      f"(favcoll, added) VALUES ('Cards&Facts news',{datetime.datetime.today()});",type="user")
    except Exception as error:
        mainLogger.error(f'DB error in "main.py/start_message()" at 152 line >> {error}')
    bot.send_message(message.chat.id,
                     'Добро пожаловать {}, ID диалога - {}'.format(message.from_user.first_name,
                                                                   message.chat.id),
                     reply_markup=menu.main_menu)


@bot.callback_query_handler(func=lambda call: True)
def handler_call(call):
    mainLogger.debug(f'CALL.DATA (168 line in main.py/handler_call()): {call.data}')
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    # Main menu
    if call.data == 'menu':
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text='Главное меню',
            reply_markup=menu.main_menu)
    if call.data == 'profile':
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text='Ваш профиль:',
            reply_markup=menu.main_profile_menu
        )
    if call.data == 'about':
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text='Cards&Facts\n'
                 'Создан RustyTheCodeguy\n'
                 'Вдохновлён Quizlet\n',
            reply_markup=menu.main_profile_menu
        )
    if call.data == 'play':
        row = say_to_db("SELECT * FROM collections ORDER BY RANDOM() LIMIT 10")
        result_menu = telebot.types.InlineKeyboardMarkup(row_width=1)
        result_menu.add(
            telebot.types.InlineKeyboardButton(text='🔄 Обновить', callback_data='play'),
            # telebot.types.InlineKeyboardButton(text='🔎 Найти', callback_data='search'),
        )
        for i in row:
            result_menu.add(telebot.types.InlineKeyboardButton(text=f'{i[0]}', callback_data=f'{i[0]}'))
        result_menu.add(telebot.types.InlineKeyboardButton(text='🔙 Назад', callback_data='menu'))
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Доступные карточки (показаны случайные 10)\n"
                 "Для обновления списка нажмите 🔄\n"
                 f"UUID запроса: {str(random.randint(1111, 9999))}",
            reply_markup=result_menu)
    if call.data in getcollections('n', 'pass'):
        author = getcollections('a', call.data)
        name = getcollections('n', call.data)
        views = getcollections('w', call.data)
        say_to_db(f"UPDATE users SET selectedcollection='{name[0]}' WHERE userid ='{chat_id}';", type='user')
        say_to_db(f"UPDATE collections SET views = views+1 WHERE name = '{name[0]}';")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f'"{name[0]}" от @{author[0]}\n'
                 f'Просмотров: {views[0]}',
            reply_markup=loadmenu(name[0]))
    print(findcardincollection(chat_id))
    print(getcard(''.join(findcardincollection(chat_id)), call.data))
    cardobj = getcard(''.join(findcardincollection(chat_id)), call.data)
    if not cardobj == None:
        if call.data in cardobj[0]:
            print('BYPASSED!!!')
            back_to_collection = telebot.types.InlineKeyboardMarkup(row_width=5)
            request = f"SELECT selectedcollection FROM users WHERE userid='{chat_id}'"
            back_to_collection.add(
            telebot.types.InlineKeyboardButton(text='🔙 Назад', callback_data=f'{[x[0] for x in say_to_db(request, type="user")][0]}'))
            #bot.send_photo(chat_id=chat_id, photo=io.BytesIO(urllib.request.urlopen(''.join(cardobj[2])).read()), caption=f"Открыта карточка {cardobj[0]}", reply_to_message_id=message_id, reply_markup=back_to_collection)
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{'Вопрос: '+''.join(cardobj[0])}"
                 f"\n{'Ответ: '+''.join(cardobj[1])}",
                reply_markup=back_to_collection)

    if call.data == 'my_collections':
        pass

# запуск телебота
#try:
bot.polling()
#except Exception as e:
    #mainLogger.error(f"Some error occurred in bot.polling(). Detailed info >> {e}")
