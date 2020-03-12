import os
import numpy as np
from . import BaseTextEncoder
from .helper import reduce_mean, reduce_max


class ErnieTextEncoder(BaseTextEncoder):
    def __init__(self,
                 pooling_strategy: str = 'cls',
                 max_length: int = 128,
                 device: str = 'cpu',
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.tokenizer = None
        self.pooling_strategy = pooling_strategy
        self.max_seq_length = max_length
        self.device = device
        self.vocab_filename = ""

    def post_init(self):
        self.exe = None
        self.model = None
        self.inputs = None
        self.outputs = None
        import paddlehub as hub
        import paddle.fluid as fluid
        from bert.tokenization import bert_tokenization
        module = hub.Module(name='ernie')
        self.inputs, self.outputs, self.model = module.context(
            trainable=False, max_seq_len=self.max_seq_length)
        # convert the ernie vocab file into the bert vocab format
        self.vocab_filename = os.path.join(
            self.current_workspace, "ernie.vocab.txt")
        self.convert_vocab(module.get_vocab_path(), self.vocab_filename)
        self.logger.info("vocab file saved path: {}".format(self.vocab_filename))
        self.tokenizer = bert_tokenization.FullTokenizer(
            vocab_file=self.vocab_filename, do_lower_case=True)
        place = None
        if self.device == 'cpu':
            place = fluid.CPUPlace()
        else:
            self.logger.error("unknown device: {}".format(self.device))
            raise ValueError
        self.exe = fluid.Executor(place)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        padded_token_ids, padded_text_type_ids, padded_position_ids, padded_task_ids, input_mask = \
            self.ndarray2ids(data)
        cls_emb, unpad_top_layer_emb = self.exe.run(
            program=self.model,
            fetch_list=[
                self.outputs["pooled_output"].name,
                self.outputs["sequence_output"].name
            ],
            feed={
                self.inputs["input_ids"].name: padded_token_ids,
                self.inputs["segment_ids"].name: padded_text_type_ids,
                self.inputs["position_ids"].name: padded_position_ids,
                self.inputs["input_mask"].name: input_mask
            },
            return_numpy=False
        )
        if self.pooling_strategy == 'cls':
            output = np.array(cls_emb)
        elif self.pooling_strategy == 'mean':
            output = reduce_mean(np.array(unpad_top_layer_emb), input_mask.squeeze())
        elif self.pooling_strategy == 'max':
            output = reduce_max(np.array(unpad_top_layer_emb), input_mask.squeeze())
        else:
            self.logger.error("pooling strategy not found: {}".format(self.pooling_strategy))
            raise NotImplementedError
        return output

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exe.close()
        super().__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def convert_vocab(input_fn, output_fn):
        vocab = []
        with open(input_fn, "r") as in_fh:
            for l in in_fh:
                tmp = l.split("\t")
                if len(tmp) == 2:
                    vocab.append(tmp[0])
        with open(output_fn, "w") as out_fh:
            out_fh.write("\n".join(vocab))
            out_fh.write("\n")

    def ndarray2ids(self, data):
        from bert.tokenization import bert_tokenization
        batch_token_ids = []
        batch_text_type_ids = []
        batch_position_ids = []
        for r in data:
            text_a = bert_tokenization.convert_to_unicode(r)
            tokens_a = self.tokenizer.tokenize(text_a)
            if len(tokens_a) > self.max_seq_length - 2:
                tokens_a = tokens_a[0:(self.max_seq_length - 2)]
            tokens = []
            text_type_ids = []
            tokens.append("[CLS]")
            text_type_ids.append(0)
            for token in tokens_a:
                tokens.append(token)
                text_type_ids.append(0)
            tokens.append("[SEP]")
            token_ids = self.tokenizer.convert_tokens_to_ids(tokens)
            text_type_ids.append(0)
            position_ids = list(range(len(token_ids)))
            batch_token_ids.append(token_ids)
            batch_text_type_ids.append(text_type_ids)
            batch_position_ids.append(position_ids)
        padded_token_ids, input_mask = self.pad_batch_data(
            batch_token_ids,
            pad_idx=self.tokenizer.vocab['[PAD]'],
            return_input_mask=True)
        padded_text_type_ids = self.pad_batch_data(
            batch_text_type_ids, pad_idx=self.tokenizer.vocab['[PAD]'])
        padded_position_ids = self.pad_batch_data(
            batch_position_ids, pad_idx=self.tokenizer.vocab['[PAD]'])
        padded_task_ids = np.ones_like(
            padded_token_ids, dtype="int64") * self.tokenizer.vocab['[PAD]']
        return padded_token_ids, padded_text_type_ids, padded_position_ids, padded_task_ids, input_mask

    @staticmethod
    def pad_batch_data(insts,
                       pad_idx=0,
                       return_input_mask=False):
        return_list = []
        max_len = max(len(inst) for inst in insts)
        inst_data = np.array(
            [inst + list([pad_idx] * (max_len - len(inst))) for inst in insts])
        return_list += [inst_data.astype("int64").reshape([-1, max_len, 1])]
        if return_input_mask:
            input_mask_data = np.array([[1] * len(inst) + [0] *
                                        (max_len - len(inst)) for inst in insts])
            input_mask_data = np.expand_dims(input_mask_data, axis=-1)
            return_list += [input_mask_data.astype("float32")]
        return return_list if len(return_list) > 1 else return_list[0]
