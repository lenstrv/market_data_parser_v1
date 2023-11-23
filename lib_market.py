import emoji

def clean_text (in_str: str) -> str:
    """
    Возвращает очищенную от мусора текстовую строку. Переносы строк заменяет пробелами

    Аргументы:
        in_str: str     - Строка, требующая очистки

    """
    try:
        text = emoji.replace_emoji(in_str, replace=' ').replace('*', '').replace('#', ''). \
            replace('№', '').replace('-', '').replace('+', '').replace('=', '').replace('^', ''). \
            replace('>', '').replace('&', '').replace('\t', '').replace('\n', ' ').replace('\v', ''). \
            replace('\'', '').replace('\"', '').replace('\\', ' ').replace('  ', ' ').strip()
        return text
    except:
        print('Ошибка при выполнении очистки текста - текст объявления не найден')
    return None