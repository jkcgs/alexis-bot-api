import json
import re
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify, request

from lib.common import find_str
from lib.database import Database

view = Blueprint('covid19cl', __name__)
db = Database.get_instance()
coll = db.db.get_collection('covid19cl')
pat_infogram_uuid = re.compile(r'^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$')

step1 = 'https://www.gob.cl/coronavirus/cifrasoficiales/'
step2 = 'https://e.infogram.com/'
datamap = {
    'activos': 3,
    'asintomaticos': 26,
    'conectados': 10,
    'confirmados': 19,
    'criticos': 12,
    'examenes': 14,
    'fallecidos': 23,
    'fecha': 22,
    'rs_habitaciones': 34,
    'rs_residencias': 33,
    'sintomaticos': 5,
    'total_examenes': 15,
    'ventiladores_disp': 32,
}
minimal_fields = ['confirmados', 'sintomaticos', 'asintomaticos', 'fallecidos', 'activos']
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


def get_infogram_id():
    gobresult = requests.get(step1, headers={'User-Agent': __name__ + '/1.0.0'})
    infogram_id = find_str(gobresult.text, 'class="infogram-embed" data-id="', '"')
    if not pat_infogram_uuid.match(infogram_id):
        error_fetch = jsonify(message='Could not fetch today\'s data (fetch upstream code)')
        error_fetch.status_code = 500
        return error_fetch, None
    return None, infogram_id


@view.route('/covid')
def show():
    raw = request.args.get('raw', '')
    use_cache = request.args.get('no_cache', '') != '1'

    now = datetime.now()
    yesterday = now - timedelta(days=1)
    date_ytday = '{} de {}'.format(yesterday.day, mes[yesterday.month])

    # Fetch data from database first
    ytday_data = coll.find_one({'fecha': date_ytday, 'listo': True}, projection={'_id': 0})
    ytday_data = clear_data(ytday_data, raw)

    if use_cache:
        date_today = '{} de {}'.format(now.day, mes[now.month])
        today_data = coll.find_one({'fecha': date_today, 'listo': True}, projection={'_id': 0})
        today_data = clear_data(today_data, raw)

        # Today's data not found in database, scrap it from the website
        if today_data:
            today_data['ayer'] = ytday_data
            return jsonify(today_data)

    # Get infogram ID from cache. If not available, fetch it from upstream.
    err, infogram_id = get_infogram_id()
    if err:
        return err

    # Load infogram data
    infogram = requests.get(step2 + infogram_id)
    if infogram.status_code != 200:
        error_fetch = jsonify(message='Could not fetch today\'s data (invalid upstream code)')
        error_fetch.status_code = 500
        return error_fetch

    # If data is not valid, return an error
    data = find_str(infogram.text, 'window.infographicData=', '</script>')
    if data is None:
        error_fetch = jsonify(message='Could not fetch today\'s data (invalid data)')
        error_fetch.status_code = 500
        return error_fetch

    data_raw = json.loads(data.strip()[:-1])

    content = data_raw['elements']['content']['content']
    entities = content['blocks'][content['blockOrder'][0]]['entities']
    data = [content['entities'][x]['props'] for x in entities]
    data = [y['content']['blocks'][0].get('text', '') for y in data if 'content' in y]

    # Initialize data with some metadata
    data_result = {'raw': data, 'datamap': datamap, 'listo': True, 'pre_listo': True, 'ts_capturado': now,
                   'total_nuevos': None, 'recuperados': None}

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
                if k in minimal_fields:
                    data_result['pre_listo'] = False

    # If current infogram date's yesterday, fetch pre-yesterday data and send yesterday data from DB
    if data_result['fecha'] == date_ytday:
        pre_ytday = yesterday - timedelta(days=1)
        date_preyt = '{} de {}'.format(pre_ytday.day, mes[pre_ytday.month])
        preyt_data = coll.find_one({'fecha': date_preyt, 'listo': True}, projection={'_id': 0})
        ytday_data['ayer'] = clear_data(preyt_data, raw)
        return jsonify(ytday_data)

    if data_result['pre_listo']:
        data_result['recuperados'] = data_result['confirmados'] - data_result['fallecidos'] - data_result['activos']
        data_result['total_nuevos'] = data_result['sintomaticos'] + data_result['asintomaticos']

    # Insert data as today's data on DB if it's ready
    if data_result['listo'] and use_cache:
        coll.insert_one(data_result)

    # Clear data and append yesterday's data
    data_result = clear_data(data_result, raw)
    data_result['ayer'] = ytday_data
    return jsonify(data_result)
