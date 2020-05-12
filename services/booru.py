from flask import Blueprint, request, jsonify
from xml.etree.ElementTree import fromstring as parsexml

from lib.common import get_session

search_types = {
    'e621': {
        'url': 'https://e621.net/posts.json?limit=30&tags={}',
    },
    'gelbooru': {
        'url': 'https://gelbooru.com/index.php?page=dapi&s=post&q=index&tags={}',
    },
    'rule34': {
        'url': 'https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    },
    'danbooru': {
        'url': 'https://danbooru.donmai.us/posts.json?limit=30&tags={}',
    },
    'konachan': {
        'url': 'https://konachan.net/post.json?limit=30&tags={}',
    },
    'konachan18': {
        'url': 'https://konachan.com/post.json?limit=30&tags={}',
    },
    'hypnohub': {
        'url': 'https://hypnohub.net/post/index.json?limit=30&tags={}',
        'image_format': 'https:{}'
    },
    'xbooru': {
        'url': 'https://xbooru.com/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    },
    'realbooru': {
        'url': 'https://realbooru.com/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    },
    'furrybooru': {
        'url': 'https://furry.booru.org/index.php?page=dapi&s=post&q=index&tags={}',
        'format': 'xml'
    }
}

view = Blueprint(__name__, __name__)


@view.route('/booru')
def show():
    search_text = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'rule34').strip()

    if search_text == '':
        return jsonify({'message': 'Missing search query ("q" query param)'}, status=400)

    if search_type not in search_types:
        return jsonify({'message': 'Invalid search type.'}, status=400)

    search_url = search_types[search_type]['url'].format(search_text)
    s = get_session()
    response = s.get(search_url)

    if search_types[search_type].get('format', 'json') == 'xml':
        posts = [x.attrib for x in parsexml(response.text).findall('post')]
    else:
        posts = response.json()['posts']

    return jsonify(posts)
