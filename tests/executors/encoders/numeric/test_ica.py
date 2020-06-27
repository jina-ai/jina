#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 20:35:11 2020

@author: James
"""

import unittest

import numpy as np
from jina.executors.encoders.numeric.ica import FastICAEncoder
from tests.executors.encoders.numeric import NumericTestCase


class MyTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 280
        self.target_output_dim = 6
        encoder = FastICAEncoder(
            output_dim=self.target_output_dim, whiten=True, num_features=self.input_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        return encoder


if __name__ == '__main__':
    unittest.main()