import os

import numpy as np

from .. import BaseTextEncoder
from ..helper import reduce_mean, reduce_max, reduce_min


class ErnieTextEncoder(BaseTextEncoder):
    """
    :class:`ErnieTextEncoder` encodes data from an array of string in size `B` into a ndarray in size `B x D`.
    Internally, :class:`ErnieTextEncoder` wraps the Ernie module from paddlehub.
    https://github.com/PaddlePaddle/PaddleHub
    """

    def __init__(self,
                 model_name: str = 'ernie_tiny',
                 pooling_strategy: str = 'cls',
                 max_length: int = 128,
                 *args,
                 **kwargs):
        """

        :param model_name: the name of the model. Supported models include ``ernie``, ``ernie_tiny``,
            ``ernie_v2_eng_base``, and ``ernie_v2_eng_large``. Fo models' details refer to
            https://aistudio.baidu.com/aistudio/projectdetail/186443
        :param pooling_strategy: the strategy to merge the word embeddings into the chunk embedding. Supported
            strategies include ``mean``, ``cls``, ``max``, and ``min``.
        :param max_length: the max length to truncate the tokenized sequences to.
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pooling_strategy = pooling_strategy
        self.max_seq_length = max_length
        self.vocab_filename = ''
        self.tokenizer = None

    def post_init(self):
        import paddlehub as hub
        import paddle.fluid as fluid
        from bert.tokenization import bert_tokenization
        module = hub.Module(name=self.model_name)
        self.inputs, self.outputs, self.model = module.context(
            trainable=False, max_seq_len=self.max_seq_length)
        # convert the ernie vocab file into the bert vocab format
        self.vocab_filename = os.path.join(self.current_workspace, 'ernie.vocab.txt')
        num_cols = 1
        if self.model_name == 'ernie':
            num_cols = 2
        self._convert_vocab(module.get_vocab_path(), self.vocab_filename, num_cols)
        self.logger.info('vocab file saved path: {}'.format(self.vocab_filename))
        self.tokenizer = bert_tokenization.FullTokenizer(
            vocab_file=self.vocab_filename, do_lower_case=True)
        place = None
        if not self.on_gpu:
            place = fluid.CPUPlace()
        else:
            place = fluid.CUDAPlace(int(os.getenv('FLAGS_selected_gpus', '0')))
        self.exe = fluid.Executor(place)
        self.convert_to_unicode = bert_tokenization.convert_to_unicode

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        padded_token_ids, padded_text_type_ids, padded_position_ids, padded_task_ids, input_mask = \
            self._data2inputs(data)
        cls_emb, unpad_top_layer_emb = self.exe.run(
            program=self.model,
            fetch_list=[
                self.outputs['pooled_output'].name,
                self.outputs['sequence_output'].name
            ],
            feed={
                self.inputs['input_ids'].name: padded_token_ids,
                self.inputs['segment_ids'].name: padded_text_type_ids,
                self.inputs['position_ids'].name: padded_position_ids,
                self.inputs['input_mask'].name: input_mask
            },
            return_numpy=False
        )
        if self.pooling_strategy == 'cls':
            output = np.array(cls_emb)
        elif self.pooling_strategy == 'mean':
            output = reduce_mean(np.array(unpad_top_layer_emb), input_mask.squeeze())
        elif self.pooling_strategy == 'max':
            output = reduce_max(np.array(unpad_top_layer_emb), input_mask.squeeze())
        elif self.pooling_strategy == 'min':
            output = reduce_min(np.array(unpad_top_layer_emb), input_mask.squeeze())
        else:
            self.logger.error('pooling strategy not found: {}'.format(self.pooling_strategy))
            raise NotImplementedError
        return output

    def close(self):
        self.exe.close()

    def _data2inputs(self, data):
        batch_token_ids = []
        batch_text_type_ids = []
        batch_position_ids = []
        for r in data:
            text = self.convert_to_unicode(r)
            tokens = ['[CLS]'] + self.tokenizer.tokenize(text)[:self.max_seq_length] + ['[SEP]']
            token_ids = self.tokenizer.convert_tokens_to_ids(tokens)
            text_type_ids = [0] * len(token_ids)
            position_ids = list(range(len(token_ids)))
            batch_token_ids.append(token_ids)
            batch_text_type_ids.append(text_type_ids)
            batch_position_ids.append(position_ids)
        padded_token_ids, input_mask = self._pad_batch_data(
            batch_token_ids,
            pad_idx=self.tokenizer.vocab['[PAD]'],
            return_input_mask=True)
        padded_text_type_ids = self._pad_batch_data(
            batch_text_type_ids, pad_idx=self.tokenizer.vocab['[PAD]'])
        padded_position_ids = self._pad_batch_data(
            batch_position_ids, pad_idx=self.tokenizer.vocab['[PAD]'])
        padded_task_ids = np.ones_like(
            padded_token_ids, dtype='int64') * self.tokenizer.vocab['[PAD]']
        return padded_token_ids, padded_text_type_ids, padded_position_ids, padded_task_ids, input_mask

    @staticmethod
    def _convert_vocab(input_fn, output_fn, num_cols=1):
        vocab = []
        with open(input_fn, 'r') as in_fh:
            for l in in_fh:
                tmp = l.split('\t')
                if len(tmp) == num_cols:
                    vocab.append(tmp[0].strip("\n"))
        with open(output_fn, 'w') as out_fh:
            out_fh.write('\n'.join(vocab))
            out_fh.write('\n')

    @staticmethod
    def _pad_batch_data(inputs, pad_idx=0, return_input_mask=False):
        result = []
        max_len = max(len(t) for t in inputs)
        inst_data = np.array([t + list([pad_idx] * (max_len - len(t))) for t in inputs])
        result += [inst_data.astype('int64').reshape([-1, max_len, 1])]
        if return_input_mask:
            input_mask_data = np.array([[1] * len(t) + [0] * (max_len - len(t)) for t in inputs])
            input_mask_data = np.expand_dims(input_mask_data, axis=-1)
            result += [input_mask_data.astype('float32')]
        return result if len(result) > 1 else result[0]
