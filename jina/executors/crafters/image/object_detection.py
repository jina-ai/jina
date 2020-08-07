__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List

import numpy as np

from jina.executors.crafters import BaseSegmenter
from jina.executors.devices import TorchDevice
from .helper import _crop_image, _move_channel_axis, _load_image


class TorchObjectDetectionSegmenter(TorchDevice, BaseSegmenter):
    """
    :class:`TorchObjectDetectionSegmenter` detects objects from an image using `torchvision detection models` and crops
    the images according tothe detected bounding boxes of the objects with a confidence higher than a threshold.
        TODO: Allow changing the backbone
    """
    COCO_INSTANCE_CATEGORY_NAMES = [
        '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
        'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
        'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
        'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
        'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
        'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
        'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
        'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table',
        'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
        'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
        'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]

    def __init__(self, model_name: str = None,
                 channel_axis: int = 0,
                 confidence_threshold: int = 0.0,
                 label_name_map: Dict[int, str] = None,
                 *args, **kwargs):
        """
        :param model_name: the name of the model. Supported models include
        ``fasterrcnn_resnet50_fpn``,
        ``maskrcnn_resnet50_fpn`
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param confidence_threshold: confidence value from which it
        considers a positive detection and therefore the object detected will be cropped and returned
        :param label_name_map: A Dict mapping from label index to label name, by default will be
        COCO_INSTANCE_CATEGORY_NAMES
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        if self.model_name is None:
            self.model_name = 'fasterrcnn_resnet50_fpn'
        self.channel_axis = channel_axis
        self._default_channel_axis = 0
        self.confidence_threshold = confidence_threshold
        self.label_name_map = label_name_map
        if self.label_name_map is None:
            self.label_name_map = TorchObjectDetectionSegmenter.COCO_INSTANCE_CATEGORY_NAMES

    def post_init(self):
        super().post_init()
        self._device = None
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
        _predictions = self.model([_input])[0]
        boxes = _predictions['boxes'].detach()
        scores = _predictions['scores'].detach()
        labels = _predictions['labels']
        if self.on_gpu:
            boxes = boxes.cpu()
            scores = scores.cpu()
            labels = labels.cpu()
        return boxes, scores, labels

    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> List[Dict]:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :return: a list of chunk dicts with the cropped images
        """
        raw_img = np.copy(blob)
        raw_img = _move_channel_axis(raw_img, self.channel_axis, self._default_channel_axis)
        bboxes, scores, labels = self._predict(raw_img)
        img = _load_image(raw_img * 255, self._default_channel_axis)
        result = []
        for bbox, score, label in zip(bboxes.numpy(), scores.numpy(), labels.numpy()):
            if score >= self.confidence_threshold:
                x0, y0, x1, y1 = bbox
                # note that tensors are [H, W] while PIL Images are [W, H]
                top, left = int(y0), int(x0)
                # target size must be (h, w)
                target_size = (int(y1) - int(y0), int(x1) - int(x0))
                # at this point, raw_img has the channel axis at the default tensor one
                _img, top, left = _crop_image(img, target_size=target_size, top=top, left=left, how='precise')
                _img = _move_channel_axis(np.asarray(_img).astype('float32'), -1, self.channel_axis)
                label_name = self.label_name_map[label]
                self.logger.debug(f'detected {label_name} with confidence {score} at position {(top, left)} and size {target_size}')
                result.append(
                    dict(offset=0, weight=1., blob=_img,
                         location=(top, left), meta_info=label_name.encode()))
        return result
