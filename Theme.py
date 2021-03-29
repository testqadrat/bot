from Word import Word


# Тема
class Theme:

    # Конструктор
    def __init__(self):
        self.name = None
        self.words_list = list()

    # Заполнение
    def set(self, name, words: dict):
        self.name = name
        for word, data in words.items():
            new_word = Word()
            new_word.set(word, data)
            self.words_list.append(new_word)

    # Получение данных
    def get(self) -> tuple:
        data = dict()
        for word in self.words_list:
            name, word_data = word.get()
            data[name] = word_data
        return self.name, data
