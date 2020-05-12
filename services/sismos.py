import requests
import bs4
from flask import Blueprint, jsonify

BASE_URL = 'http://sismologia.cl'
view = Blueprint('sismos', __name__)


def row_parse(row):
    cols = row.find_all('td')
    link = BASE_URL + cols[0].find('a')['href']
    magnitud = cols[5].text.split(',')[0].split(' ')
    imagen = link.replace('events', 'mapas').replace('html', 'jpeg').replace('erb_', '')

    return {
        'id': link.split('/')[-1][:-5],
        'enlace': link,
        'mapa': imagen,
        'latitud': float(cols[2].text),
        'longitud': float(cols[3].text),
        'fecha': cols[0].text,
        'fecha_utc': cols[1].text,
        'profundidad': float(cols[4].text),
        'referencia': cols[7].text,
        'magnitud': float(magnitud[0]),
        'escala': magnitud[1],
        'preliminar': 'erb_' in link
    }


@view.route('/sismos')
def show():
    cont = requests.get(BASE_URL + '/links/ultimos_sismos.html')
    cont.encoding = 'utf-8'
    dom = bs4.BeautifulSoup(cont.text, 'html.parser')
    rows = dom.find_all('tr')
    del rows[0]

    return jsonify(sismos=[row_parse(x) for x in rows])
