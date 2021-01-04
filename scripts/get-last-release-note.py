## under jina root dir
# python scripts/get-last-release-note.py
## result in root/tmp.md

with open('CHANGELOG.md') as fp:
    n = []
    for v in fp:
        if v.startswith('## Release Note'):
            n.clear()
        n.append(v)

with open('tmp.md', 'w') as fp:
    fp.writelines(n)
