__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List

import numpy as np

from ..frameworks import BaseTorchSegmenter
from .helper import _crop_image, _restore_channel_axis, _load_image, _check_channel_axis


class TorchObjectDetectionSegmenter(BaseTorchSegmenter):
    """
    :class:`FasterRCNNSegmenter` detects objects from an image using `FasterRCNN` and crops the images according to
    the detected bounding boxes of the objects with a confidence higher than a threshold.
    """
    def __init__(self, channel_axis: int = 1,
                 confidence_threshold: int = 0.0,
                 label_name_map: Dict[int, str] = None, *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include
            ``fasterrcnn_resnet50_fpn``,
            ``maskrcnn_resnet50_fpn``
            TODO: Allow changing the backbone
        """
        super().__init__(*args, **kwargs)
        if self.model_name is None:
            self.model_name = 'fasterrcnn_resnet50_fpn'
        self.channel_axis = channel_axis
        self._default_channel_axis = 1
        self.confidence_threshold = confidence_threshold
        self.label_name_map = label_name_map

    def post_init(self):
        super().post_init()
        import torchvision.models.detection as detection_models
        model = getattr(detection_models, self.model_name)(pretrained=True, pretrained_backbone=True)
        self.model = model.eval()
        self.to_device(self.model)

    def _predict(self, img: 'np.ndarray') -> 'np.ndarray':
        """
        Run the model for prediction

        :param img: the image from which to run a prediction
        :return:
        """
        import torch
        _input = torch.from_numpy(img.astype('float32'))
        if self.on_gpu:
            _input = _input.cuda()
        _predictions = self.model(_input).detach()
        if self.on_gpu:
            _predictions = _predictions.cpu()
        _predictions = _predictions.numpy()
        return _predictions['boxes'].detach(), _predictions['scores'].detach(), _predictions['labels']

    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> List[Dict]:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :return: a list of chunk dicts with the cropped images
        """
        raw_img = _load_image(blob, self.channel_axis)
        img = _check_channel_axis(raw_img, self.channel_axis, self._default_channel_axis)
        bboxes, scores, labels = self._predict(img)
        if self.on_gpu:
            bboxes = bboxes.cpu()
            scores = scores.cpu()
            labels = labels.cpu()
        result = []
        for bbox, score, label in zip(bboxes.numpy(), scores.numpy(), labels.numpy()):
            if score >= self.confidence_threshold:
                x0, y0, x1, y1 = bbox
                top, left = x0, y0
                target_size = (x1 - x0, y1 - y0)
                _img, top, left = _crop_image(raw_img, target_size=target_size, top=top, left=left, how='precise')
                img = _restore_channel_axis(np.asarray(_img), self.channel_axis, self._default_channel_axis)
                label_name = str(label)
                if self.label_name_map:
                    label_name = self.label_name_map[label]
                #TODO: put label in tags and not meta_info
                result.append(
                    dict(offset=0, weight=1., blob=np.asarray(img).astype('float32'),
                         location=(top, left), meta_info=label_name.encode()))
        return result
