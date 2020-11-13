"""
updates all modules from JinaHub with latest version of Jina
"""
import os
from glob import glob


def handle_module_update(module_dir):
    print(f'handing module {module_dir}')
    pass


def main():
    manifest_ymls = glob('jina/hub/**/manifest.yml', recursive=True)
    print(f'Got {len(manifest_ymls)} manifests/modules to handle')
    # TODO limited to 1 for dev/testing
    manifest_ymls = manifest_ymls[:1]
    for manifest_path in manifest_ymls:
        module_dir = os.path.sep.join(manifest_path.split(os.path.sep)[:-1])
        handle_module_update(module_dir)


if __name__ == '__main__':
    main()
