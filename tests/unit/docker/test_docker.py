from jina.docker.checker import is_error_message


def test_checker_is_error_message():
    err_msg_list = [
        'HubIO@11[C]:ERROR: Command errored out with exit status 1: ...',
        'HubIO@11[C]:  ERROR: Failed building wheel for ...',
        'HubIO@11[C]:  gcc: error trying to exec : execvp: No such file or directory'
        'HubIO@11[W]:======================== 1 failed, 6 warnings in 1.05s ========================= '
    ]
    non_err_msg_list = [
        'HubIO@11[C]:    warnings.warn(error_info)',
        'HubIO@11[C]:Get:18  liberror-perl'
    ]

    for _err in err_msg_list:
        assert is_error_message(_err)

    for _non_err in non_err_msg_list:
        assert not is_error_message(_non_err)
