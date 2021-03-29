# Тема
class Word:

    # Конструктор
    def __init__(self):
        self.name = str()
        self.translate = str()
        self.example = str()

    # Заполнение
    def set(self, name: str, data: dict):
        self.name = name
        self.translate = data["Перевод"]
        self.example = data["Пример"]

    # Получение данных
    def get(self) -> tuple:
        data = {
            "Перевод": self.translate,
            "Пример": self.example
        }
        return self.name, data
