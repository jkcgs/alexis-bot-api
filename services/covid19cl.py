import json
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify, request

from lib.common import find_str
from lib.database import Database

view = Blueprint('covid19cl', __name__)
db = Database.get_instance().db.get_collection('covid19cl')

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

mes = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
       'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def clear_data(data, raw=False):
    if data is None:
        return data

    if raw != '1':
        if 'raw' in data:
            del data['raw']
        if 'datamap' in data:
            del data['datamap']
    if '_id' in data:
        del data['_id']
    return data


@view.route('/covid')
def show():
    raw = request.args.get('raw', '')
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    date_today = '{} de {}'.format(now.day, mes[now.month])
    date_ytday = '{} de {}'.format(yesterday.day, mes[yesterday.month])

    # Fetch data from database first
    today_data = db.find_one({'fecha': date_today, 'listo': True}, projection={'_id': 0})
    ytday_data = db.find_one({'fecha': date_ytday, 'listo': True}, projection={'_id': 0})

    today_data = clear_data(today_data, raw)
    ytday_data = clear_data(ytday_data, raw)

    if today_data:
        today_data['ayer'] = ytday_data
        return jsonify(today_data)

    # Today's data not found in database, scrap it from the website
    infogram = requests.get(step1)

    # If data is not valid, return an error
    data = find_str(infogram.text, 'window.infographicData=', '</script>')
    if data is None:
        response = jsonify(message='Could not fetch today\'s data')
        response.status_code = 500
        return response

    data_raw = json.loads(data.strip()[:-1])
    data = data_raw.copy()
    data = data['elements']['content']['content']['entities']
    data = [v for k, v in data.items() if v['type'] in ['TEXT', 'SHAPE']]
    data = [v['props']['content']['blocks'][0]['text'] for v in data
            if 'content' in v['props'] and len(v['props']['content']['blocks']) > 0]

    # Initialize data with some metadata
    data_result = {'raw': data, 'datamap': datamap, 'listo': True, 'ts_capturado': now}

    # Parse numeric data to its data type
    for k, v in datamap.items():
        data_result[k] = data[v]
        if k not in ['fecha', 'ts_capturado', 'raw', 'datamap', 'listo']:
            try:
                # noinspection PyTypeChecker
                data_result[k] = int(data_result[k].replace('.', ''))
            except ValueError:
                # If we found empty or unparsable data, declare them null and
                # disable the ready flag
                data_result[k] = None
                data_result['listo'] = False

    # Insert data as today's data's not on the DB
    db.insert_one(data_result)

    # Clear data and append yesterday's data
    data_result = clear_data(data_result, raw)
    data_result['ayer'] = ytday_data
    return jsonify(data_result)
