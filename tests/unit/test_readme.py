import re
import subprocess
import time
from pathlib import Path

from jina.helper import random_port


def test_readme_snippet(tmpdir):
    rp_s = r'<!-- README-SERVER-START -->\n*```python\n(.*)\n```\n*<!-- README-SERVER-END -->'
    rp_c = r'<!-- README-CLIENT-START -->\n*```python\n(.*)\n```\n*<!-- README-CLIENT-END -->'

    with open(Path(__file__).parent.parent.parent / 'README.md') as fp:
        f = fp.read()
        s = re.findall(rp_s, f, re.DOTALL)[0]  # type: str
        c = re.findall(rp_c, f, re.DOTALL)[0]  # type: str

    # replace 12345 to a new port
    new_port = random_port()
    s = s.replace('12345', str(new_port))
    c = c.replace('12345', str(new_port))

    with open(tmpdir / 'server.py', 'w') as fp:
        fp.write(s)

    with open(tmpdir / 'client.py', 'w') as fp:
        fp.write(c)

    p_s = subprocess.Popen(['python', f'{tmpdir}/server.py'])
    time.sleep(10)
    p_c = subprocess.check_output(['python', f'{tmpdir}/client.py'])
    all_lines = p_c.decode().strip().split('\n')
    assert len(all_lines) == 3
    assert "@requests(on='/index')" in all_lines[0]
    assert "@requests(on='/search')" in all_lines[1]
