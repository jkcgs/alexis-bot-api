import os
import traceback

import requests
from flask import jsonify
from os import path

CACHE_PATH = path.abspath(path.join(path.dirname(path.realpath(__file__)), '..', 'cache', 'private'))


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


def message_response(message, status=200):
    resp = jsonify({'message': message})
    resp.status_code = status
    return resp


def download_cache(filename, url, filesize=None):
    if not path.exists(CACHE_PATH):
        try:
            os.mkdir(CACHE_PATH)
        except Exception as e:
            print('Could not create cache directory')
            traceback.print_tb(e)
            return None

    filepath = path.join(CACHE_PATH, filename)
    if path.exists(filepath):
        if filesize is None:
            return filepath

        fs = os.stat(filepath)
        if fs.st_size == filesize:
            return filepath

    try:
        print('Downloading %s from %s' % (filename, url))
        r = requests.get(url)
        data = r.content
        try:
            with open(filepath, 'wb') as f:
                f.write(data)
                print('File %s stored to %s' % (filename, filepath))
                return filepath
        except OSError as e:
            print('Could not store %s file' % filename)
            traceback.print_tb(e)
            return None
    except Exception as e:
        print('Could not download the %s file' % filename)
        traceback.print_tb(e)
        return None


def get_cache_path(filename, url=None):
    filepath = path.join(CACHE_PATH, filename)
    if not path.exists(filepath):
        if url:
            download_cache(filename, url)
            if not path.exists(filepath):
                return None
        else:
            return None

    return filepath


def get_cache(filename, url=None):
    filepath = get_cache_path(filename, url)
    if filepath is None:
        return None

    return open(filepath, 'r')
