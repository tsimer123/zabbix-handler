import json

from requests import post

from data_class.data_request import ResultRequestModel


class BaseRequest:
    def __init__(self, host: str, api_token: str):
        self.host = host
        self.api_token = api_token
        self.url = f'http://{self.host}/api_jsonrpc.php'
        self.headers = self.create_heders_with_auth()

    def create_heders_with_auth(self, content_type: str = 'application/json-rpc') -> dict:
        headers = {
            'Content-Type': content_type,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Authorization': f'Bearer {self.api_token}',
        }
        return headers

    @staticmethod
    def set_default_result() -> ResultRequestModel:
        result = ResultRequestModel(status=False)
        return result

    def post_request_with_token(self, data_in: dict) -> ResultRequestModel:
        result = self.set_default_result()
        data_request = json.dumps(data_in)
        try:
            resp = post(self.url, headers=self.headers, data=data_request)
            result.data = resp.text
            if resp.status_code < 400:
                result.status = True
        except Exception as ex:
            result.error = str(ex)
        return result
