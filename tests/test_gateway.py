from threading import Thread

import requests

from jina.flow import Flow
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    def test_rest_gateway_concurrency(self):
        def _request(status_codes, index):
            a = requests.post(
                f'http://0.0.0.0:{f.port_grpc}/api/index',
                json={
                    'data': [
                        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC',
                        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC']})

            status_codes[index] = a.status_code

        f = Flow(rest_api=True).add(yaml_path='_forward')
        with f:
            concurrency = 50
            threads = []
            status_codes = [None] * concurrency
            for i in range(concurrency):
                t = Thread(target=_request, args=(status_codes, i))
                t.daemon = True
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            success = status_codes.count(200)
            failed = len(status_codes) - success

            self.assertTrue(success >= 1)

            # In some slow environments, a certain degree of failed
            # requests will occur. Here we limit the degree of failed
            # requests.
            rate = failed / success
            self.assertTrue(rate < 0.1)
