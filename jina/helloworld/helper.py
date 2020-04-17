import base64
import gzip
import struct
import zlib

import numpy as np
from pkg_resources import resource_filename


def load_mnist(path):
    with gzip.open(path, 'rb') as fp:
        return np.frombuffer(fp.read(), dtype=np.uint8, offset=16).reshape([-1, 784])


def write_png(buf, width=28, height=28):
    pixels = []
    for p in buf[::-1]:
        pixels.extend([255 - int(p), 255 - int(p), 255 - int(p), 255])
    buf = bytearray(pixels)

    # reverse the vertical line order and add null bytes at the start
    width_byte_4 = width * 4
    raw_data = b''.join(
        b'\x00' + buf[span:span + width_byte_4]
        for span in range((height - 1) * width_byte_4, -1, - width_byte_4))

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (struct.pack("!I", len(data)) +
                chunk_head +
                struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

    png_bytes = b''.join([
        b'\x89PNG\r\n\x1a\n',
        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
        png_pack(b'IEND', b'')])
    return base64.b64encode(png_bytes)


def input_fn(fp, index=True, num_doc=None):
    img_data = load_mnist(fp)
    if not index:
        # shuffle for random query
        img_data = np.take(img_data, np.random.permutation(img_data.shape[0]), axis=0)
    d_id = 0
    for r in img_data:
        yield r.tobytes()
        d_id += 1
        if num_doc is not None and d_id > num_doc:
            break


result_html = []


def print_result(resp):
    for d in resp.search.docs:
        vi = 'data:image/png;base64,' + d.meta_info.decode()
        result_html.append(f'<tr><td><img src="{vi}"/></td><td>')
        for kk in d.topk_results:
            kmi = 'data:image/png;base64,' + kk.match_doc.meta_info.decode()
            result_html.append(f'<img src="{kmi}" style="opacity:{kk.score.value}"/>')
            # k['score']['explained'] = json.loads(kk.score.explained)
        result_html.append('</td></tr>\n')


def write_html(html_path):
    with open(resource_filename('jina', '/'.join(('resources', 'helloworld.html'))), 'r') as fp, \
            open(html_path, 'w') as fw:
        t = fp.read()
        t = t.replace('{% RESULT %}', '\n'.join(result_html))
        fw.write(t)
