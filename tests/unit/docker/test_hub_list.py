import os
import pytest

from jina.docker.hubio import HubIO
from jina.parser import set_hub_list_parser


def test_hub_list_keywords():
    args = set_hub_list_parser().parse_args(['--keywords', 'numeric'])
    response = HubIO(args).list()
    numeric_count = len(response.json()['manifest'])
    
    assert response.status_code == 200
    assert numeric_count > 1 
    
    args = set_hub_list_parser().parse_args(['--keywords', 'numeric', 'randjojd'])
    response = HubIO(args).list()
    combined_count = len(response.json()['manifest'])

    assert response.status_code == 200
    assert combined_count > 1 

    # Making sure both arguments are --keywords are considered as `either or`
    assert combined_count >= numeric_count
    
    
def test_hub_list_nonexisting_kind():
    args = set_hub_list_parser().parse_args(['--kind', 'blah'])
    response = HubIO(args).list()
    
    assert response.status_code == 400
    assert response.text.lower() == 'no docs found'
