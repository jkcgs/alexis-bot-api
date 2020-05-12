import requests


def find_str(cont, ini, end):
    """
    Busca una cadena de texto según una cadena inicial y otra final. Extrae el texto que está
    inmediatamente después de la cadena inicial, para buscar la cadena final desde la inicial,
    y devuelve el texto que está entre ellos, sin incluir las cadenas de búsqueda.

    Ejemplo:

    Si cont = `Hola, ¿cómo están todos?, ¿qué tal el día?`, ini = `¿`, end = `?`, el resultado
    será `cómo están todos`.

    :param cont: El contenido donde se buscará.
    :param ini: La cadena de texto inicial.
    :param end: La cadena de texto final.
    :return: El resultado, o None si no se encontró.
    """
    try:
        idx_ini = cont.index(ini) + len(ini)
        idx_end = cont[idx_ini:].index(end) + idx_ini
        return cont[idx_ini:idx_end]
    except ValueError:
        return None


def get_session():
    s = requests.Session()
    s.headers.update({'User-Agent': 'alexis-bot-api/1.0.0 (https://alexisbot.mak.wtf)'})
    return s
