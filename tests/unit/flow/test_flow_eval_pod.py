from jina.flow import Flow


def test_flow1():
    f = Flow().add()

    with f:
        pass


def test_flow2():
    f = Flow().add().eval().plot()

    with f:
        pass


def test_flow3():
    f = Flow().add(name='p1', parallel=3).eval().add(name='p2', needs='gateway').needs(['p1', 'p2']).eval()

    with f:
        pass


def test_flow4():
    f = Flow().add(name='p1').add(name='p2', needs='gateway').needs(['p1', 'p2']).eval()

    with f:
        pass


def test_flow5():
    f = Flow().add().eval().add().eval().add().eval().plot(build=True)

    with f:
        pass
