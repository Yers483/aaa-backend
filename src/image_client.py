import requests
import io


class ImageServiceClient:
    """Клиент для соединения с сервером, где лежат картинки ."""

    def __init__(self, base_url):
        self.base_url = base_url

    def download_image(self, img_id):
        try:
            response = requests.get(f'{self.base_url}/{img_id}', timeout=30)
            if response.status_code != 200:
                return None, f'Ошибка при скачивании изображения {img_id}. ' \
                             f'Статус: {response.status_code}'
            return io.BytesIO(response.content), None
        except requests.RequestException as e:
            return None, f'Ошибка при скачивании изображения {img_id}: ' \
                         f'{str(e)}'
