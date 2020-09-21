import os

import pytest
import pymongo
import mongomock

from jina.docker.hubio import HubIO
from jina.helper import yaml
from jina.main.parser import set_hub_build_parser, set_hub_list_parser, set_hub_pushpull_parser


cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.timeout(360)
def test_hub_build_pull():
    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--pull', '--push', '--test-uses'])
    HubIO(args).build()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder'])
    HubIO(args).pull()

    args = set_hub_pushpull_parser().parse_args(['jinahub/pod.dummy_mwu_encoder:0.0.6'])
    HubIO(args).pull()


@pytest.mark.timeout(360)
def test_hub_build_uses():
    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--pull', '--test-uses'])
    HubIO(args).build()
    # build again it shall not fail
    HubIO(args).build()

    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--pull', '--test-uses', '--daemon'])
    HubIO(args).build()
    # build again it shall not fail
    HubIO(args).build()


def test_hub_build_push():
    args = set_hub_build_parser().parse_args([os.path.join(cur_dir, 'hub-mwu'), '--push', '--host-info'])
    summary = HubIO(args).build()

    with open(os.path.join(cur_dir, 'hub-mwu', 'manifest.yml')) as fp:
        manifest = yaml.load(fp)

    assert summary['is_build_success']
    assert manifest['version'] == summary['version']
    assert manifest['description'] == summary['manifest_info']['description']
    assert manifest['author'] == summary['manifest_info']['author']
    assert manifest['kind'] == summary['manifest_info']['kind']
    assert manifest['type'] == summary['manifest_info']['type']
    assert manifest['vendor'] == summary['manifest_info']['vendor']
    assert manifest['keywords'] == summary['manifest_info']['keywords']


def test_hub_build_failures():
    for j in ['bad-dockerfile', 'bad-pythonfile', 'missing-dockerfile', 'missing-manifest']:
        args = set_hub_build_parser().parse_args(
            [os.path.join(cur_dir, 'hub-mwu-bad', j), '--pull', '--push'])
        assert not HubIO(args).build()['is_build_success']


def test_hub_build_no_pymodules():
    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu-bad', 'fail-to-start'), '--pull', '--push'])
    assert HubIO(args).build()['is_build_success']

    args = set_hub_build_parser().parse_args(
        [os.path.join(cur_dir, 'hub-mwu-bad', 'fail-to-start'), '--pull', '--push', '--test-uses'])
    assert not HubIO(args).build()['is_build_success']

def test_aggregate(monkeypatch):

        args = set_hub_list_parser().parse_args(['--type', 'pod', '--kind', 'encoder', '--keywords', '[sklearn]'])
        
        monkeypatch.setattr(pymongo.collection, "Collection", mongomock.collection.Collection)
        monkeypatch.setattr(pymongo, "MongoClient", mongomock.MongoClient)
        setattr(mongomock.database.Database, "address", ("localhost", 27017))

        # monkeypatch.setenv('JINA_DB_HOSTNAME', "TestingHost")
        # monkeypatch.setenv('JINA_DB_USERNAME', "TestingUser")
        # monkeypatch.setenv('JINA_DB_PASSWORD', "TestingPassword")
        # monkeypatch.setenv('JINA_DB_NAME', "TestingName")
        # monkeypatch.setenv('JINA_DB_COLLECTION', "TestingCollection")

        collection = mongomock.MongoClient().db.collection
        objs = [
            {
                "_id": {
                    "id": "5f60529aeb8374c52d5e9fca"
                },
                "name": "jinahub/pod.encoder.randomsparseencoder",
                "version": "0.0.2",
                "path": "jina/hub/encoders/numeric/RandomSparseEncoder",
                "manifest_info": {
                    "description": "RandomSparseEncoder encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`",
                    "kind": "encoder",
                    "type": "pod",
                    "keywords": [
                    "numeric",
                    "sklearn"
                    ],
                    "author": "Jina AI Dev-Team (dev-team@jina.ai)",
                    "license": "apache-2.0",
                    "url": "https://jina.ai",
                    "vendor": "Jina AI Limited",
                    "documentation": "https://github.com/jina-ai/jina-hub"
                }
            },
            {
                "_id": {
                    "id": "6f60529aeb8374c52d5e9fca"
                },
                "name": "jinahub/pod.encoder.dummyencoder",
                "version": "0.0.2",
                "path": "jina/hub/encoders/numeric/DummyEncoder",
                "manifest_info": {
                    "description": "DummyEncoder encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`",
                    "kind": "encoder",
                    "type": "pod",
                    "keywords": [
                    "numeric",
                    "sklearn"
                    ],
                    "author": "Jina AI Dev-Team (dev-team@jina.ai)",
                    "license": "apache-2.0",
                    "url": "https://jina.ai",
                    "vendor": "Jina AI Limited",
                    "documentation": "https://github.com/jina-ai/jina-hub"
                }
            },
            {
                "_id": {
                    "id": "7f60529aeb8374c52d5e9fca"
                },
                "name": "jinahub/pod.crafter.deepsegmenter:0.0.2",
                "version": "0.0.2",
                "path": "jina/hub/crafters/nlp/DeepSegmenter",
                "manifest_info": {
                    "description": "DeepSegmenter encodes data from an ndarray in size `B x T` into an ndarray in size `B x D`",
                    "kind": "encoder",
                    "type": "pod",
                    "keywords": [
                    "numeric",
                    "sklearn"
                    ],
                    "author": "Jina AI Dev-Team (dev-team@jina.ai)",
                    "license": "apache-2.0",
                    "url": "https://jina.ai",
                    "vendor": "Jina AI Limited",
                    "documentation": "https://github.com/jina-ai/jina-hub"
                }
            }
        ]

        collection.insert(objs)

        HubIO(args).list()
        print('### PRINTING RESULTS ###')
        # print(results)
        # assert len(list(results)) == 3
