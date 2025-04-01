import logging
import io
import requests
from flask import Flask, request, jsonify
from models.plate_reader import PlateReader, InvalidImage

app = Flask(__name__)
plate_reader = PlateReader.load_from_file(
    './model_weights/plate_reader_model.pth'
)

IMAGE_SERVICE_URL = 'http://89.169.157.72:8080/images'
AVAILABLE_IMAGE_IDS = [10022, 9965]


def download_image(img_id):
    """Функция для скачивания изображений."""
    try:
        response = requests.get(f"{IMAGE_SERVICE_URL}/{img_id}")
        if response.status_code != 200:
            return None, f'Ошибка при скачивании изображения {img_id}. ' \
                         f'Статус: {response.status_code}'
        return io.BytesIO(response.content), None
    except requests.RequestException as e:
        return None, f'Ошибка при скачивании изображения {img_id}: {str(e)}'


def process_image(image_data):
    """Функция для обработки изображения и распознавания номерных знаков."""
    try:
        if image_data is None:
            return None, 'Файл с изображением пуст'

        plate_number = plate_reader.read_text(image_data)
        return plate_number, None
    except InvalidImage:
        return None, 'Неверный формат изображения'
    except Exception as e:
        return None, f'Ошибка при обработки изображения: {str(e)}'


@app.route('/')
def hello():
    return '<h1 style="color:blue;"><center>' \
            'Сервис для распознавания номерных знаков</center></h1>'


@app.route('/api/recognize', methods=['GET'])
def recognize_by_id():
    """Хэндлер для распознавания единичных изображений"""
    img_id = request.args.get('id')

    if not img_id:
        return jsonify({'Ошибка': 'Нужен ID изображения'}), 400

    try:
        img_id = int(img_id)
    except ValueError:
        return (
            jsonify({'Ошибка': 'ID изображения должно быть целым числом'}),
            400
        )

    image_data, error = download_image(img_id)
    if error:
        return jsonify({'Ошибка': error}), 404

    plate_number, error = process_image(image_data)
    if error:
        return jsonify({'Ошибка': error}), 400

    return jsonify({'id': img_id, 'plate_number': plate_number})


@app.route('/api/recognize_batch', methods=['POST'])
def recognize_batch():
    """Хэндлер для распознавания нескольких изображений"""

    request_data = request.get_json()

    if not request_data or 'ids' not in request_data:
        return (
            jsonify({'Ошибка':
                     'Запрос должен содержать поле ids с id изображений'}),
            400
        )

    image_ids = request_data['ids']

    if not isinstance(image_ids, list):
        return (
            jsonify({'Ошибка':
                     'Необходимо передать список из целых чисел в качестве ID картинок'}),
            400
        )

    results = []

    for img_id in image_ids:
        try:
            img_id = int(img_id)
        except (ValueError, TypeError):
            results.append(
                {'id': img_id, 'Ошибка':
                 'ID изображения должно быть целым числом'}
            )
            continue

        image_data, error = download_image(img_id)
        if error:
            results.append({'id': img_id, 'error': error})
            continue

        plate_number, error = process_image(image_data)
        if error:
            results.append({'id': img_id, 'error': error})
            continue

        results.append({'id': img_id, 'plate_number': plate_number})

    return jsonify({'results': results})


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )

    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080, debug=True)
