# Пользователь
class User:

    # Конструктор
    def __init__(self):
        # Данные
        self.id = int()
        self.username = str()
        self.first_name = str()
        self.last_name = str()

        # Статистика
        self.last_test_date = None
        self.learned_words_dict = dict()

        # Настройки
        self.theme = str()
        self.question_number = int()
        self.right_answers_number = int()

    # Получение данных пользователя в виде ID и словаря
    def get(self) -> tuple:
        data = {
            "Имя": self.first_name,
            "Фамилия": self.last_name,
            "Username": self.username,
            "Дата последнего теста": self.last_test_date,
            "Выученные слова": self.learned_words_dict,
            "Тема": self.theme,
            "Количество вопросов в тесте": self.question_number,
            "Количество правильных ответов для заучивания слова": self.right_answers_number
        }
        return str(self.id), data

    # Заполнение данных из запроса
    def set_from_request(self, req: dict):
        self.id = req["message"]["from"]["id"]
        if "username" in req["message"]["from"]:
            self.username = req["message"]["from"]["username"]
        if "first_name" in req["message"]["from"]:
            self.first_name = req["message"]["from"]["first_name"]
        if "last_name" in req["message"]["from"]:
            self.last_name = req["message"]["from"]["last_name"]
        self.last_test_date = None
        self.learned_words_dict = dict()
        self.theme = "birds"
        self.question_number = 5
        self.right_answers_number = 5
        print(f"Created user {self.id}")

    # Заполнение данных
    def set(self, id: int, data: dict):
        self.id = id
        self.first_name = data["Имя"]
        self.last_name = data["Фамилия"]
        self.username = data["Username"]
        self.last_test_date = data["Дата последнего теста"]
        self.learned_words_dict = data["Выученные слова"]
        self.theme = data["Тема"]
        self.question_number = data["Количество вопросов в тесте"]
        self.right_answers_number = data["Количество правильных ответов для заучивания слова"]

    # Получение статистики
    def get_statistics(self) -> str:
        learned_words_number = 0
        for theme, learned_words in self.learned_words_dict.items():
            for number in learned_words.values():
                if number >= self.right_answers_number:
                    learned_words_number += 1
        stat_str = f"Количество выученых слов: {learned_words_number}\n"
        if not self.last_test_date:
            stat_str += "Дата последнего теста: Пусто"
        else:
            stat_str += f"Дата последнего теста: {self.last_test_date}"
        return stat_str

    # Получение текущих настроек
    def get_settings(self) -> str:
        settings_str = f"Тема: {self.theme}\n"
        settings_str += f"Количество вопросов в тесте: {self.question_number}\n"
        settings_str += f"Количество правильных ответов для заучивания слова: {self.right_answers_number}"
        return settings_str

    # Получение полностью выученных слов текущей темы
    def get_fully_learned_words_cur_theme(self):
        if self.theme not in self.learned_words_dict:
            return []
        else:
            fully_learned_words_list = list()
            cur_theme_words_dict = self.learned_words_dict[self.theme]
            if not cur_theme_words_dict:
                return []
            for word, number in cur_theme_words_dict.items():
                if number >= self.right_answers_number:
                    fully_learned_words_list.append(word)
            return fully_learned_words_list
