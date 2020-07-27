import unittest

from jina.proto.jina_pb2 import Document
from tests import JinaTestCase
from google.protobuf.json_format import MessageToJson, Parse


class ProtobufTestCase(JinaTestCase):

    def test_tags(self):
        d = Document()
        d.tags['int'] = 1  # will convert to float!!!
        d.tags['str'] = 'blah'
        d.tags['float'] = 0.1234
        d.tags['bool'] = True
        d.tags['nested'] = {'bool': True}
        jd = MessageToJson(d)
        d2 = Parse(jd, Document())
        self.assertTrue(isinstance(d2.tags['int'], float))
        self.assertTrue(isinstance(d2.tags['str'], str))
        self.assertTrue(isinstance(d2.tags['float'], float))
        self.assertTrue(isinstance(d2.tags['bool'], bool))
        self.assertTrue(isinstance(d2.tags['nested']['bool'], bool))
        # can be used as a dict
        for k, v in d2.tags['nested'].items():
            print(f'{k}:{v}')



if __name__ == '__main__':
    unittest.main()
