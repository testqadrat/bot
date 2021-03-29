from flask import Flask, request, jsonify
import requests
import json
import random
import datetime
from User import User
from Theme import Theme
import os

token = os.environ.get("TOKEN")
url = f"https://api.telegram.org/bot{token}/"

themes_file = "themes.json"

app = Flask(__name__)


# Получение ID чата из запроса
def get_chat_id(req: dict):
    if "message" in req:
        chat_id = req["message"]["chat"]["id"]
    elif "callback_query" in req:
        chat_id = req["callback_query"]["message"]["chat"]["id"]
    else:
        chat_id = None
    return chat_id


# Проверка, является ли запрос текстовым сообщением
def is_text_message(req: dict):
    if "text" in req["message"]:
        return True
    else:
        return False


# Получение текста из принятого сообщения
def get_message(req: dict):
    message = req["message"]["text"]
    return message


# Получение данных из callback запроса
def get_data(req: dict):
    data = req["callback_query"]["data"]
    return data


# Загрузка данных из json-файла
def load_json_data(file: str) -> dict:
    try:
        with open(file, "rt", encoding="utf-8") as in_file:
            json_data = json.load(in_file)
        return json_data
    except FileNotFoundError:
        print(f"Отсутствует файл {file}\n")
        exit()


# Бот
class Bot:

    # Конструктор
    def __init__(self, token: str, url: str):
        self.token = token
        self.url = url

        self.users_list = list()

        self.themes_list = list()
        themes_dict = load_json_data(themes_file)
        for name, data in themes_dict.items():
            new_theme = Theme()
            new_theme.set(name, data)
            self.themes_list.append(new_theme)

        self.edit_theme_users = list()
        self.edit_question_number_users = dict()
        self.edit_right_answers_number_users = list()
        self.users_test_dict = dict()

    # Проверка наличия пользователя в списке пользователей
    def check_user(self, user_id: int):
        for user in self.users_list:
            if user.id == user_id:
                return True
        return False

    # Добавление пользователя в список пользователей
    def add_user(self, req: dict):
        new_user = User()
        new_user.set_from_request(req)
        self.users_list.append(new_user)

    # Получение пользователя по ID
    def get_user(self, id: int):
        for user in self.users_list:
            if user.id == id:
                return user
        return None

    # Получение темы по названию
    def get_theme(self, name: str):
        for theme in self.themes_list:
            if theme.name == name:
                return theme
        return None

    # Получение списка с названиями тем
    def get_themes_names(self):
        themes_names_list = list()
        for theme in self.themes_list:
            themes_names_list.append(theme.name)
        return themes_names_list

    # Отправка сообщения
    def send_message(self, chat_id: int, text):
        data = {"chat_id": chat_id, "text": text, "allow_sending_without_reply": True}
        requests.post(url + "sendMessage", data=data)

    # Отправка клавиатуры
    def send_keyboard(self, chat_id: int, text: str, keyboard):
        data = {"chat_id": chat_id, "text": text, "allow_sending_without_reply": True, "reply_markup": keyboard}
        requests.post(url + "sendMessage", data=data)

    # Отправка статистики
    def send_statistics(self, chat_id: int, user_id: int):
        user = self.get_user(user_id)
        stat_str = user.get_statistics()
        self.send_keyboard(chat_id, stat_str, json.dumps(main_menu_keyboard))

    # Отправка статистики
    def send_settings(self, chat_id: int, user_id: str):
        user = self.get_user(chat_id)
        settings_str = user.get_settings()
        self.send_keyboard(chat_id, settings_str, json.dumps(settings_keyboard))

    # Генерация теста
    def generate_test(self, user_id: int):
        user = self.get_user(user_id)
        theme = self.get_theme(user.theme)
        _, words_dict = theme.get()
        fully_learned_words_list = user.get_fully_learned_words_cur_theme()
        words_list = words_dict.keys()
        words_list = [item for item in words_list if item not in fully_learned_words_list]
        if not words_list:
            return False
        if user.theme not in user.learned_words_dict:
            user.learned_words_dict[user.theme] = {}
        words_list = random.sample(words_list, k=user.question_number)
        question_list = list()
        for word in words_list:
            right_word = words_dict[word]
            right_answer = right_word["Перевод"]
            example = right_word["Пример"]
            answers_list = list()
            for elem in words_dict.values():
                answers_list.append(elem["Перевод"])
            answers_list.remove(right_answer)
            answers_list = random.sample(answers_list, k=3)
            answers_list.append(right_answer)
            answers_list = random.sample(answers_list, k=len(answers_list))
            keyboard_elem = list()
            for elem in answers_list:
                keyboard_elem.append([{"text": elem,
                                       "callback_data": elem}])
            keyboard = {"inline_keyboard": keyboard_elem}
            question_list.append({"message": word,
                                  "keyboard": keyboard,
                                  "right answer": right_answer,
                                  "example": example})
        self.users_test_dict[user_id] = question_list
        return True

    # Пересчет количества правильных ответов
    def recalculate_questions_number(self, user_id: int):
        user = self.get_user(user_id)
        theme = self.get_theme(user.theme)
        max_question_number = len(theme.words_list)
        if user.theme not in user.learned_words_dict:
            if user.question_number == 0:
                user.question_number = max_question_number
            return None
        learned_words_list = user.get_fully_learned_words_cur_theme()
        learned_words_number = len(learned_words_list)
        max_question_number -= learned_words_number
        if max_question_number < user.question_number or user.question_number == 0:
            user.question_number = max_question_number

    def end_test(self, user_id: int):
        del self.users_test_dict[user_id]
        cur_date = datetime.datetime.utcnow()
        cur_date = cur_date.replace(tzinfo=utc_moscow)
        cur_date = cur_date + cur_date.utcoffset()
        user = self.get_user(user_id)
        user.last_test_date = cur_date.strftime("%Y-%m-%d %H:%M:%S")
        self.recalculate_questions_number(user_id)


main_menu_keyboard = {
    "keyboard": [
        [
            {"text": "Начать тест"}
        ],
        [
            {"text": "Статистика"},
            {"text": "Настройки"}
        ]
    ],
    "resize_keyboard": True
}

settings_keyboard = {
    "keyboard": [
        [
            {"text": "Тема"},
            {"text": "Назад"}
        ],
        [
            {"text": "Количество вопросов в тесте"}
        ],
        [
            {"text": "Количество правильных ответов для заучивания слова"}
        ]
    ],
    "resize_keyboard": True
}

test_keyboard = {
    "keyboard": [
        [
            {"text": "Посмотреть пример"}
        ],
        [
            {"text": "Закончить"}
        ]
    ],
    "resize_keyboard": True
}

utc_moscow = datetime.timezone(datetime.timedelta(hours=3))

bot = Bot(token, url)

request_count = 0


@app.route("/", methods=["GET", "POST"])
def get_request():
    global request_count
    request_count += 1

    # Принят POST-запрос
    if request.method == "POST":
        req = request.get_json()
        chat_id = get_chat_id(req)
        is_reg_user = bool
        print(req)

        # Принятый POST-запрос - сообщение
        if "message" in req and is_text_message(req):
            message = get_message(req)
            user_id = req["message"]["from"]["id"]
            is_reg_user = bot.check_user(user_id)

            # Начало работы с ботом
            if message == "/start":
                if "username" in req["message"]["from"]:
                    user = req["message"]["from"]["username"]
                elif "first_name" in req["message"]["from"]:
                    user = req["message"]["from"]["first_name"]
                else:
                    user = ""
                bot.send_message(chat_id, f"Hello, {user}.\nЯ могу помочь тебе с изучением новых английских слов.")
                if not is_reg_user:
                    bot.add_user(req)
                    is_reg_user = True
                bot.send_keyboard(chat_id, "Выберите пункт меню", json.dumps(main_menu_keyboard))

            # Нажата кнопка "Закончить"
            if message == "Закончить" and is_reg_user:
                if user_id in bot.users_test_dict:
                    bot.end_test(user_id)
                    bot.send_keyboard(chat_id, "Выберите пункт меню", json.dumps(main_menu_keyboard))

            # Нажата кнопка "Посмотреть пример"
            if message == "Посмотреть пример" and is_reg_user:
                example = bot.users_test_dict[user_id][0]["example"]
                bot.send_message(chat_id, example)

            # Нажата кнопка "Начать тест"
            if message == "Начать тест" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    res = bot.generate_test(user_id)
                    if not res:
                        bot.send_message(chat_id, "Вы выучили все слова данной темы")
                    else:
                        question_word = bot.users_test_dict[user_id][0]["message"]
                        answers_keyboard = bot.users_test_dict[user_id][0]["keyboard"]
                        bot.send_keyboard(chat_id, "Стартую тест", json.dumps(test_keyboard))
                        bot.send_keyboard(chat_id, question_word, json.dumps(answers_keyboard))

            # Нажата кнопка "Статистика"
            if message == "Статистика" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    bot.send_statistics(chat_id, user_id)

            # Нажата кнопка "Настройки"
            if message == "Настройки" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    bot.send_settings(chat_id, user_id)

            # Настройки: Нажата кнопка "Тема"
            if message == "Тема" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    set_theme_str = "Выберите тему:"
                    keyboard_elem = []
                    for theme in bot.themes_list:
                        keyboard_elem.append([{"text": theme.name}])
                    keyboard = {"keyboard": keyboard_elem,
                                "resize_keyboard": True}
                    bot.send_keyboard(chat_id, set_theme_str, json.dumps(keyboard))
                    bot.edit_theme_users.append(user_id)

            # Настройки: Нажата кнопка "Количество вопросов"
            if message == "Количество вопросов в тесте" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    user = bot.get_user(user_id)
                    theme = bot.get_theme(user.theme)
                    _, words_dict = theme.get()
                    max_question_number = len(words_dict)
                    learned_words_list = user.get_fully_learned_words_cur_theme()
                    learned_words_number = len(learned_words_list)
                    max_question_number -= learned_words_number
                    if max_question_number == 0:
                        bot.send_message(chat_id, "Вы выучили все слова в данной теме")
                    else:
                        bot.edit_question_number_users[user_id] = max_question_number
                        bot.send_message(chat_id, f"Введите количество вопросов в тесте (от 1 до {max_question_number}):")

            # Настройки: Нажата кнопка "Количество правильных ответов для заучивания слова"
            if message == "Количество правильных ответов для заучивания слова" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    bot.send_message(chat_id, "Введите количество правильных ответов для заучивания слова:")
                    bot.edit_right_answers_number_users.append(user_id)

            # Настройки: Нажата кнопка "Назад"
            if message == "Назад" and is_reg_user:
                if user_id not in bot.users_test_dict:
                    bot.send_keyboard(chat_id, "Выберите пункт меню", json.dumps(main_menu_keyboard))

            # Принято сообщение с темой
            if (user_id in bot.edit_theme_users) and (message in bot.get_themes_names()) and is_reg_user:
                user = bot.get_user(user_id)
                user.theme = message
                bot.recalculate_questions_number(user_id)
                bot.send_settings(chat_id, user_id)
                bot.edit_theme_users.remove(user_id)

            # Принято сообщение с количеством вопросов в тесте
            if user_id in bot.edit_question_number_users and message.isdigit() and 1 <= int(message) <= bot.edit_question_number_users[user_id] and is_reg_user:
                user = bot.get_user(user_id)
                user.question_number = int(message)
                bot.send_settings(chat_id, user_id)
                del bot.edit_question_number_users[user_id]

            # Принято сообщение с количеством правильных ответов для заучивания слова
            if (user_id in bot.edit_right_answers_number_users) and message.isdigit() and message != "0" and is_reg_user:
                user = bot.get_user(user_id)
                user.right_answers_number = int(message)
                bot.recalculate_questions_number(user_id)
                bot.send_settings(chat_id, user_id)
                bot.edit_right_answers_number_users.remove(user_id)

        # Принятый POST-запрос - callback-запрос
        if "callback_query" in req:
            data = req["callback_query"]["data"]
            user_id = req["callback_query"]["from"]["id"]
            is_reg_user = bot.check_user(user_id)

            # Пользователь проходит тест
            if user_id in bot.users_test_dict and is_reg_user:
                if data == bot.users_test_dict[user_id][0]["right answer"]:
                    bot.send_message(chat_id, "Правильный ответ")
                    user = bot.get_user(user_id)
                    word = bot.users_test_dict[user_id][0]["message"]
                    if word in user.learned_words_dict[user.theme]:
                        user.learned_words_dict[user.theme][word] += 1
                    else:
                        user.learned_words_dict[user.theme][word] = 1
                else:
                    bot.send_message(chat_id, "Неправильный ответ")
                del bot.users_test_dict[user_id][0]
                if bot.users_test_dict[user_id]:
                    question_word = bot.users_test_dict[user_id][0]["message"]
                    answers_keyboard = bot.users_test_dict[user_id][0]["keyboard"]
                    bot.send_keyboard(chat_id, question_word, json.dumps(answers_keyboard))
                else:
                    bot.end_test(user_id)
                    bot.send_keyboard(chat_id, "Выберите пункт меню", json.dumps(main_menu_keyboard))

        if not is_reg_user:
            bot.send_message(chat_id, "Вас нет в базе данных.\nДля начала работы с ботом введите /start")

        return jsonify(req)

    return f"<h1>Request count: {request_count}<h1>"


if __name__ == "__main__":
    app.run(debug=True)
