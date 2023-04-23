import re
import sys

meetup_svg = '.github/images/meetup.svg'
readme_md = 'README.md'
conf_py = 'docs/conf.py'


def rm_announce():
    # remove all announcement
    with open(readme_md, encoding='utf-8') as fp:
        _old = fp.read()
        _new = re.sub(
            r'(<!--startmsg-->\s*?\n).*(\n\s*?<!--endmsg-->)',
            rf'\g<1>\g<2>',
            _old,
            flags=re.DOTALL,
        )

    with open(readme_md, 'w', encoding='utf-8') as fp:
        fp.write(_new)

    with open(conf_py, encoding='utf-8') as fp:
        _old = fp.read()
        _new = re.sub(
            r'(# start-announce\s*?\n).*(\n\s*?# end-announce)',
            rf'\g<1>\g<2>',
            _old,
            flags=re.DOTALL,
        )
    with open(conf_py, 'w', encoding='utf-8') as fp:
        fp.write(_new)


if len(sys.argv) < 3:
    rm_announce()
else:
    text = sys.argv[1]
    url = sys.argv[2]

    if not text or not url:
        rm_announce()
    else:
        announce_url = f'''
    "announcement": \'\'\'
    <a href="{url}">{text}</a>
    \'\'\',
        '''
        meetup_svg_url = f'<a href="{url}"><img src="https://github.com/jina-ai/jina/blob/master/{meetup_svg}?raw=true"></a>'

        # update meetup_svg
        with open(meetup_svg, encoding='utf-8') as fp:
            _old = fp.read()
            _new = re.sub(r'(<a href=").*(")', rf'\g<1>{url}\g<2>', _old)
            _new = re.sub(
                r'(<!--startmsg-->\s*?\n).*(\n\s*?<!--endmsg-->)',
                rf'\g<1>{text}\g<2>',
                _new,
                flags=re.DOTALL,
            )

        with open(meetup_svg, 'w', encoding='utf-8') as fp:
            fp.write(_new)

        # update readme_md
        with open(readme_md, encoding='utf-8') as fp:
            _old = fp.read()
            _new = re.sub(
                r'(<!--startmsg-->\s*?\n).*(\n\s*?<!--endmsg-->)',
                rf'\g<1>{meetup_svg_url}\g<2>',
                _old,
                flags=re.DOTALL,
            )

        with open(readme_md, 'w', encoding='utf-8') as fp:
            fp.write(_new)

        # update conf
        with open(conf_py, encoding='utf-8') as fp:
            _old = fp.read()
            _new = re.sub(
                r'(# start-announce\s*?\n).*(\n\s*?# end-announce)',
                rf'\g<1>{announce_url}\g<2>',
                _old,
                flags=re.DOTALL,
            )

        with open(conf_py, 'w', encoding='utf-8') as fp:
            fp.write(_new)
