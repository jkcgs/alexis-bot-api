import json

import requests
from flask import Blueprint, jsonify, request

from lib.common import find_str

view = Blueprint('covid19cl', __name__)

step1 = 'https://e.infogram.com/d9e30e4b-e63c-4e02-a72a-eca4653f3283'
datamap = {
    'asintomaticos': 21,
    'conectados': 17,
    'activos': 28,
    'confirmados': 10,
    'sintomaticos': 27,
    'total_examenes': 1,
    'recuperados': 4,
    'criticos': 7,
    'examenes': 32,
    'fallecidos': 6,
    'fecha': 9
}


@view.route('/covid')
def show():
    infogram = requests.get(step1)
    data = find_str(infogram.text, 'window.infographicData=', '</script>')
    if data is None:
        return 'no'

    data_raw = json.loads(data.strip()[:-1])
    data = data_raw.copy()
    data = data['elements']['content']['content']['entities']
    data = [v for k, v in data.items() if v['type'] in ['TEXT', 'SHAPE']]
    data = [v['props']['content']['blocks'][0]['text'] for v in data
            if 'content' in v['props'] and len(v['props']['content']['blocks']) > 0]

    data_result = {}
    for k, v in datamap.items():
        data_result[k] = data[v]
        if k != 'fecha':
            try:
                data_result[k] = int(data_result[k].replace('.', ''))
            except ValueError:
                data_result[k] = None

    if request.args.get('raw', '') == '1':
        data_result['raw'] = data

    return jsonify(data_result)
