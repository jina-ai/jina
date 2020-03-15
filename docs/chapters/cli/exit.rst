Gracefully Exit Jina
====================

In a Local Console
------------------
If you running Jina locally (e.g. :command:`jina flow`), you can :kbd:`Control-c` or :kbd:`Command-c` to terminate it at any time. All :class:`BasePod` will receive this signal and shutdown accordingly.