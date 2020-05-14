import re

from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import requests
from flask import Blueprint, request, send_file

from lib.common import message_response, get_cache_path

view = Blueprint('discord_meme', __name__)

MAX_LENGTH = 100
IMAGE_SIZE = 512
BASE_URL = 'https://cdn.discordapp.com/'
FONT_URL = 'https://github.com/sophilabs/macgifer/raw/master/static/font/impact.ttf'

_font_ins = None
_font_smaller_ins = None

pat_avatar_url = re.compile(
    r'^(embed/avatars/[0-4]\.png|avatars/[0-9]{18}/(a_)?[0-9a-f]{32}\.(gif|jpg|png|webp))\??')


def get_fonts():
    global _font_ins, _font_smaller_ins
    font_path = get_cache_path('impact.ttf', FONT_URL)

    if _font_ins is None:
        _font_ins = ImageFont.truetype(font_path, size=int(IMAGE_SIZE / 8))
    if _font_smaller_ins is None:
        _font_smaller_ins = ImageFont.truetype(font_path, size=int(IMAGE_SIZE / 14))

    return _font_ins, _font_smaller_ins


def text_splitter(draw, text, max_width, font):
    lines = []
    words = [f.strip() for f in text.split(' ')]

    line = []
    for word in words:
        w, h = draw.multiline_textsize(' '.join(line) + word, font)
        if w > max_width and len(line) > 0:
            lines.append(' '.join(line))
            line = [word]
        else:
            line.append(word)

    if len(line) > 0:
        lines.append(' '.join(line))

    return lines


def meme_draw(im, text, upper=True):
    draw = ImageDraw.Draw(im)
    ins_font, ins_smaller_font = get_fonts()
    sep = int(IMAGE_SIZE / 23)
    selfont = ins_font

    # Determine font size
    if len(text_splitter(draw, text, IMAGE_SIZE - sep, ins_font)) > 2:
        selfont = ins_smaller_font

    # Determine text position
    text = '\n'.join(text_splitter(draw, text, IMAGE_SIZE - sep, selfont))
    w, h = draw.multiline_textsize(text, selfont)
    xy = (int(IMAGE_SIZE/2)) - int(w/2), (15 if upper else IMAGE_SIZE - sep - h)

    # Draw shadow
    i = 2
    x, y = xy
    draw.multiline_text((x+i, y+i), text, font=selfont, align='center', fill='black')
    draw.multiline_text((x+i, y-i), text, font=selfont, align='center', fill='black')
    draw.multiline_text((x-i, y-i), text, font=selfont, align='center', fill='black')
    draw.multiline_text((x-i, y+i), text, font=selfont, align='center', fill='black')
    # Draw the text itself
    draw.multiline_text(xy, text, font=selfont, align='center')


@view.route('/discord_meme')
def show():
    avatar_url = request.args.get('avatar_url', '')
    top = request.args.get('top', '').strip()
    bottom = request.args.get('bottom', '').strip()

    if not pat_avatar_url.match(avatar_url):
        return message_response('Invalid avatar URL', 400)

    if not top and not bottom:
        return message_response('At least one of top and bottom texts must be sent', 400)

    if len(top) > MAX_LENGTH:
        return message_response('Top text is too long (max 100 characters)')

    if len(bottom) > MAX_LENGTH:
        return message_response('Bottom text is too long (max 100 characters)')

    avatar_url = avatar_url[:avatar_url.rfind('.')] + '.png?size=1024'
    avatar_data = requests.get(BASE_URL + avatar_url)
    avatar_data = Image.open(BytesIO(avatar_data.content)).resize((IMAGE_SIZE, IMAGE_SIZE), Image.ANTIALIAS)
    im = Image.new('RGBA', (IMAGE_SIZE, IMAGE_SIZE))
    im.paste(avatar_data, (0, 0))

    meme_draw(im, bottom, upper=False)
    if top:
        meme_draw(im, top)

    temp = BytesIO()
    im.save(temp, format='PNG')
    temp = BytesIO(temp.getvalue())  # eliminar bytes nulos

    return send_file(temp, attachment_filename='meme.png', mimetype='image/png')
