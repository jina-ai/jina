from typing import Iterable, Optional, Sequence

from prometheus_client import REGISTRY, CollectorRegistry
from prometheus_client.metrics import Summary, _build_full_name


class _SummaryDeprecated(Summary):
    """
    This is a small wrapper around prometheus Summary that allow to deprecate an old metrics by renaming it.
    """

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str] = (),
        namespace: str = '',
        subsystem: str = '',
        unit: str = '',
        registry: Optional[CollectorRegistry] = REGISTRY,
        _labelvalues: Optional[Sequence[str]] = None,
        old_name: str = None,
    ):
        """
        :param old_name: name of the metric you want to deprecat
        :param kwargs: the rest of argument for creating your Summary

        # noqa: DAR102
        # noqa: DAR101

        """
        super().__init__(
            name,
            documentation,
            labelnames,
            namespace,
            subsystem,
            unit,
            registry,
            _labelvalues,
        )

        self._old_name = (
            _build_full_name(self._type, old_name, namespace, subsystem, unit)
            if old_name
            else None
        )

    def collect(self):
        metric = self._get_metric()
        for suffix, labels, value, timestamp, exemplar in self._samples():
            metric.add_sample(self._name + suffix, labels, value, timestamp, exemplar)
            if self._old_name:  # here this is the hack to inject the old metrics names
                metric.add_sample(
                    self._old_name + suffix, labels, value, timestamp, exemplar
                )

        return [metric]
