from .optimize import main


def test_optimizer():
    """This will run complete optimisation.
    Todo: fix number of index and query doc so that test doesnt run long
    Todo: assert to check eval key and value for values generated in config/best_config.yml
    Todo: after optimisation is complete, assert to check trial pods and flows do not have any evironment variable.
          This can be checked by some of our current yaml related functions in flow runner
          and changing its functionality to assert values are not starting with $.
    """
    pass