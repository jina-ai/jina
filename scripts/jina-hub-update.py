""" Script to change versioning of files (eg. manifest.yml) for executors
[encoders, crafters, indexers, rankers, evaluators, classifiers etc.].
It also adds the required jina version.
Commits the change in the branch and raises a PR for the executor.
"""
import glob
import os

import git
import semver
from github import Github
from ruamel.yaml import YAML

# this one has PR push access
g = Github(os.environ["DEV_BOT_TOKEN"])

yaml = YAML()


def main():
    hub_repo = git.Repo('jina-hub')
    hub_origin = hub_repo.remote(name='origin')
    hub_origin_url = list(hub_origin.urls)[0]
    assert 'jina-hub' in hub_origin_url, f'hub repo was not initialized correctly'
    gh_hub_repo = g.get_repo('jina-ai/jina-hub')

    jina_core_repo = git.Repo('.')
    core_origin_url = list(jina_core_repo.remote(name='origin').urls)[0]
    assert 'jina.git' in core_origin_url, f'core repo was not initialized correctly'

    jina_core_version = jina_core_repo.tags[-1].tag.tag[1:]  # remove leading 'v'

    print(f'cur. dir. is "{os.getcwd()}"')
    print(f'got jina core v: "{jina_core_version}"')

    modules = glob.glob(f'jina-hub/**/manifest.yml', recursive=True)
    print(f'got {len(modules)} modules to update')
    # traverse list of modules in jina-hub
    for fpath in modules:
        dname = fpath.split('/')[-2]
        print(f'handling {dname}...')
        with open(fpath) as fp:
            info = yaml.load(fp)
            # make sure the (possibly) existing version is older
            if 'jina-version' in info.keys():
                existing_jina_version = info['jina-version']
                if semver.VersionInfo.parse(existing_jina_version) >= semver.VersionInfo.parse(jina_core_version):
                    print(f'existing jina-core version for {dname} was greater or equal than version to update '
                          f'({existing_jina_version} >= '
                          f'{jina_core_version}). Skipping...')
                    continue

            old_ver = info['version']
            new_ver = '.'.join(old_ver.split('.')[:-1] + [str(int(old_ver.split('.')[-1]) + 1)])
            info['version'] = new_ver
            print(f'bumped to {new_ver}')
            info['jina-version'] = jina_core_version
        with open(fpath, 'w') as fp:
            yaml.dump(info, fp)

        br_name = ''
        try:
            print('preparing the branch ...')
            br_name = f'chore-{dname.lower()}-{new_ver.replace(".", "-")}-core-{jina_core_version.replace(".", "-")}'
            new_branch = hub_repo.create_head(br_name)
            new_branch.checkout()

            print(f'bumping version to {new_ver} and committing to {new_branch}...')
            hub_repo.git.add(update=True)
            hub_repo.index.commit(f'chore: bump {dname} version to {new_ver}')
            hub_repo.git.push('--set-upstream', hub_origin, hub_repo.head.ref)

            print('making a PR ...')
            title_string = f'bumping version for {dname} to {new_ver}'
            body_string = f'bumping version from {old_ver} to {new_ver}'

            gh_hub_repo.create_pull(
                title=title_string,
                body=body_string,
                head=br_name,
                base='master'
            )
        except git.GitCommandError as e:
            print(f'Caught exception: {repr(e)}')
            if 'tip of your current branch is behind' in str(e) \
                    or 'the remote contains work that you do' in str(e):
                print(f'warning: Branch "{br_name}" already existed. . Skipping...')
        except Exception:
            raise
        finally:
            hub_repo.git.checkout('master')
            if br_name:
                hub_repo.delete_head(br_name, force=True)


if __name__ == '__main__':
    main()
