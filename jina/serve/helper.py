def _telemetry_run_in_thread(event: str) -> None:
    """Sends in a thread a request with telemetry for a given event"""

    import base64
    import json
    import urllib
    import threading

    def _telemetry():
        url = 'https://telemetry.jina.ai/'
        try:
            from jina.helper import get_full_version
            metas, envs = get_full_version()
            data = base64.urlsafe_b64encode(
                json.dumps({**metas, **envs, 'event': event}).encode('utf-8')
            )
            req = urllib.request.Request(
                url, data=data, headers={'User-Agent': 'Mozilla/5.0'}
            )
            urllib.request.urlopen(req)

        except:
            pass

    threading.Thread(target=_telemetry, daemon=True).start()