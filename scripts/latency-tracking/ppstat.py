import json
import sys

from prettytable import MARKDOWN, PrettyTable

try:
    stats_file = sys.argv[1]
except IndexError:
    stats_file = 'output/stats.json'

with open(stats_file) as fp:
    d = json.load(fp)

num_last_release = len(d) - 1

x = PrettyTable()
x.field_names = [
    'Version',
    'Index QPS',
    'Query QPS',
    'Avg Flow Time (s)',
    'Import Time (s)',
]

index_qps = int(d[-1]['index_qps'])
query_qps = int(d[-1]['query_qps'])
avg_flow_time = round(d[-1]['avg_flow_time'], 4)
import_time = round(d[-1]['import_time'], 4)
x.add_row([f'current', index_qps, query_qps, avg_flow_time, import_time])
for dd in d[:-1][::-1]:
    x.add_row(
        [
            f'[`{dd["version"]}`](https://github.com/jina-ai/jina/tree/v{dd["version"]})',
            int(dd['index_qps']),
            int(dd['query_qps']),
            round(dd['avg_flow_time'], 4),
            round(dd['import_time'], 4),
        ]
    )

avg_index_qps = sum(dd['index_qps'] for dd in d[:-1]) / len(d[:-1])
avg_query_qps = sum(dd['query_qps'] for dd in d[:-1]) / len(d[:-1])
_avg_flow_time = sum(dd['avg_flow_time'] for dd in d[:-1]) / len(d[:-1])
avg_import_time = sum(dd['import_time'] for dd in d[:-1]) / len(d[:-1])

delta_index = int((index_qps / avg_index_qps - 1) * 100)
delta_query = int((query_qps / avg_query_qps - 1) * 100)
delta_flow_time = int((avg_flow_time / _avg_flow_time - 1) * 100)
delta_import_time = int((import_time / avg_import_time - 1) * 100)

if delta_index > 10:
    emoji_index = '🐎🐎🐎🐎'
elif delta_index > 5:
    emoji_index = '🐎🐎'
elif delta_index < -5:
    emoji_index = '🐢🐢'
elif delta_index < -10:
    emoji_index = '🐢🐢🐢🐢'
else:
    emoji_index = '😶'

if delta_query > 10:
    emoji_query = '🐎🐎🐎🐎'
elif delta_query > 5:
    emoji_query = '🐎🐎'
elif delta_query < -5:
    emoji_query = '🐢🐢'
elif delta_query < -10:
    emoji_query = '🐢🐢🐢🐢'
else:
    emoji_query = '😶'

if delta_flow_time > 10:
    emoji_flow_time = '🐎🐎🐎🐎'
elif delta_flow_time > 5:
    emoji_flow_time = '🐎🐎'
elif delta_flow_time < -5:
    emoji_flow_time = '🐢🐢'
elif delta_flow_time < -10:
    emoji_flow_time = '🐢🐢🐢🐢'
else:
    emoji_flow_time = '😶'

if delta_import_time > 10:
    emoji_import_time = '🐎🐎🐎🐎'
elif delta_import_time > 5:
    emoji_import_time = '🐎🐎'
elif delta_import_time < -5:
    emoji_import_time = '🐢🐢'
elif delta_import_time < -10:
    emoji_import_time = '🐢🐢🐢🐢'
else:
    emoji_import_time = '😶'

summary = (
    f'## Latency summary\n '
    f'Current PR yields:\n'
    f'  - {emoji_index} **index QPS** at `{index_qps}`, delta to last {num_last_release} avg.: `{delta_index:+d}%`\n'
    f'  - {emoji_query} **query QPS** at `{query_qps}`, delta to last {num_last_release} avg.: `{delta_query:+d}%`\n'
    f'  - {emoji_flow_time} **avg flow time** within `{avg_flow_time}` seconds, delta to last {num_last_release} avg.: `{delta_flow_time:+d}%`\n'
    f'  - {emoji_import_time} `import jina` within **{import_time}** seconds, delta to last {num_last_release} avg.: `{delta_import_time:+d}%`\n\n'
    f'## Breakdown'
)

print(summary)
x.set_style(MARKDOWN)
print(x)
print(
    '\n\nBacked by [latency-tracking](https://github.com/jina-ai/latency-tracking).'
    ' Further commits will update this comment.'
)
