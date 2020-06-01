import unittest

from jina.executors.crafters.nlp.split import Sentencizer, JiebaSegmenter
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_sentencier_en(self):
        sentencizer = Sentencizer()
        text = 'It is a sunny day!!!! When Andy comes back, we are going to the zoo.'
        crafted_chunk_list = sentencizer.craft(text, 0)
        self.assertEqual(len(crafted_chunk_list), 2)

    def test_sentencier_en_new_lines(self):
        """
        New lines are also considered as a separator.
        """
        sentencizer = Sentencizer()
        text = 'It is a sunny day!!!! When Andy comes back,\n' \
               'we are going to the zoo.'
        crafted_chunk_list = sentencizer.craft(text, 0)
        self.assertEqual(len(crafted_chunk_list), 3)

    def test_sentencier_en_float_numbers(self):
        """
        Separators in float numbers, URLs, emails, abbreviations (like 'Mr.')
        are not taking into account.
        """
        sentencizer = Sentencizer()
        text = 'With a 0.99 probability this sentence will be ' \
               'tokenized in 2 sentences.'
        crafted_chunk_list = sentencizer.craft(text, 0)
        self.assertEqual(len(crafted_chunk_list), 2)

    def test_sentencier_en_trim_spaces(self):
        """
        Trimming all spaces at the beginning an end of the chunks.
        Keeping extra spaces inside chunks.
        Ignoring chunks with only spaces.
        """
        sentencizer = Sentencizer()
        text = '  This ,  text is...  . Amazing !!'
        chunks = [i['text'] for i in sentencizer.craft(text, 0)]
        self.assertListEqual(chunks, ["This ,  text is", "Amazing"])

    def test_sentencier_cn(self):
        sentencizer = Sentencizer()
        text = '今天是个大晴天！安迪回来以后，我们准备去动物园。'
        crafted_chunk_list = sentencizer.craft(text, 0)
        self.assertEqual(len(crafted_chunk_list), 2)

    def test_jieba_crafter(self):
        jieba_crafter = JiebaSegmenter(mode='accurate')
        text = '今天是个大晴天！安迪回来以后，我们准备去动物园。'
        crafted_chunk_list = jieba_crafter.craft(text, 0)
        self.assertEqual(len(crafted_chunk_list), 14)


if __name__ == '__main__':
    unittest.main()
