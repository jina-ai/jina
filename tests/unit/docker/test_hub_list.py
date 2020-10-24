from jina.docker.hubio import HubIO
from jina.parser import set_hub_list_parser


def test_hub_list_local_with_submodule():
    args = set_hub_list_parser().parse_args(['--local-only'])
    response = HubIO(args).list()
    assert len(response) > 1


def test_hub_list_keywords():
    args = set_hub_list_parser().parse_args(['--keywords', 'numeric'])
    response = HubIO(args).list()
    numeric_count = len(response)

    assert numeric_count > 1

    args = set_hub_list_parser().parse_args(['--keywords', 'numeric', 'randjojd'])
    response = HubIO(args).list()
    combined_count = len(response)

    assert combined_count > 1

    # Making sure both arguments are --keywords are considered as `either or`
    assert combined_count >= numeric_count


def test_hub_list_nonexisting_kind():
    args = set_hub_list_parser().parse_args(['--kind', 'blah'])
    response = HubIO(args).list()

    assert not response
