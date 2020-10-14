import pytest
import requests

from jina.clients import py_client
from jina.clients.python import PyClient
from jina.clients.python.io import input_files
from jina.enums import ClientMode
from jina.flow import Flow
from jina.parser import set_gateway_parser
from jina.peapods.gateway import RESTGatewayPea
from jina.proto.jina_pb2 import Document


def test_client():
    f = Flow().add(uses="_pass")
    with f:
        print(
            py_client(port_expose=f.port_expose).call_unary(
                b"a1234", mode=ClientMode.INDEX
            )
        )


def test_check_input():
    input_fn = iter([b"1234", b"45467"])
    PyClient.check_input(input_fn)
    input_fn = iter([Document(), Document()])
    PyClient.check_input(input_fn)
    bad_input_fn_1 = iter([b"1234", "45467", [12, 2, 3]])
    with pytest.raises(TypeError):
        PyClient.check_input(bad_input_fn_1)
    bad_input_fn_2 = iter([Document(), None])
    with pytest.raises(TypeError):
        PyClient.check_input(bad_input_fn_2)


def test_gateway_ready():
    p = set_gateway_parser().parse_args([])
    with RESTGatewayPea(p):
        a = requests.get(f"http://0.0.0.0:{p.port_expose}/ready")
        assert a.status_code == 200

    with RESTGatewayPea(p):
        a = requests.post(f"http://0.0.0.0:{p.port_expose}/api/ass")
        assert a.status_code == 405


def test_gateway_index():
    f = Flow(rest_api=True).add(uses="_pass")
    with f:
        a = requests.post(
            f"http://0.0.0.0:{f.port_expose}/api/index",
            json={
                "data": [
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC",
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC",
                ]
            },
        )

        j = a.json()
        assert "index" in j
        assert len(j["index"]["docs"]) == 2
        assert (
            j["index"]["docs"][0]["uri"]
            == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC"
        )
        assert a.status_code == 200


def test_gateway_index_with_args():
    f = Flow(rest_api=True).add(uses="_pass")
    with f:
        a = requests.post(
            f"http://0.0.0.0:{f.port_expose}/api/index",
            json={
                "data": [
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC",
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AvdGjTZeOlQq07xSYPgJjlWRwfWEBx2+CgAVrPrP+O5ghhOa+a0cocoWnaMJFAsBuCQCgiJOKDBcIQTiLieOrPD/cp/6iZ/Iu4HqAh5dGzggIQVJI3WqTxwVTDjs5XJOy38AlgHoaKgY+xJEXeFTyR7FOfF7JNWjs3b8evQE6B2dTDvQZx3n3Rz6rgOtVlaZRLvR9geCAxuY3G+0mepEAhrTISES3bwPWYYi48OUrQOc//IaJeij9xZGGmDIG9kc73fNI7eA8VMBAAD//0SxXMMT90UdAAAAAElFTkSuQmCC",
                ],
            },
        )
        j = a.json()
        assert "index" in j
        assert len(j["index"]["docs"]) == 2
        assert (
            j["index"]["docs"][0]["uri"]
            == "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAA2ElEQVR4nADIADf/AxWcWRUeCEeBO68T3u1qLWarHqMaxDnxhAEaLh0Ssu6ZGfnKcjP4CeDLoJok3o4aOPYAJocsjktZfo4Z7Q/WR1UTgppAAdguAhR+AUm9AnqRH2jgdBZ0R+kKxAFoAME32BL7fwQbcLzhw+dXMmY9BS9K8EarXyWLH8VYK1MACkxlLTY4Eh69XfjpROqjE7P0AeBx6DGmA8/lRRlTCmPkL196pC0aWBkVs2wyjqb/LABVYL8Xgeomjl3VtEMxAeaUrGvnIawVh/oBAAD///GwU6v3yCoVAAAAAElFTkSuQmCC"
        )
        assert a.status_code == 200


def test_mime_type():

    f = Flow().add(uses="- !URI2Buffer {}")

    def validate_mime_type(req):
        for d in req.index.docs:
            assert d.mime_type == "text/x-python"

    with f:
        f.index(input_files("*.py"), validate_mime_type)
