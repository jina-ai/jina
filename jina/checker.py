from .logging.predefined import default_logger
import argparse


class NetworkChecker:
    """Check if a BasePod is running or not."""

    def __init__(self, args: 'argparse.Namespace'):
        """
        Create a new :class:`NetworkChecker`.

        :param args: args provided by the CLI.
        """
        from .peapods.zmq import send_ctrl_message
        from .logging.profile import TimeContext
        from google.protobuf.json_format import MessageToJson
        import time

        ctrl_addr = f'tcp://{args.host}:{args.port}'
        try:
            total_time = 0
            total_success = 0
            for j in range(args.retries):
                with TimeContext(
                    f'ping {ctrl_addr} at {j} round', default_logger
                ) as tc:
                    r = send_ctrl_message(ctrl_addr, 'STATUS', timeout=args.timeout)
                    if not r:
                        default_logger.warning(
                            'not responding, retry (%d/%d) in 1s'
                            % (j + 1, args.retries)
                        )
                    else:
                        total_success += 1
                        if args.print_response:
                            default_logger.info(f'returns {MessageToJson(r.proto)}')
                total_time += tc.duration
                time.sleep(1)
            if total_success < args.retries:
                default_logger.warning(
                    'message lost %.0f%% (%d/%d) '
                    % (
                        (1 - total_success / args.retries) * 100,
                        args.retries - total_success,
                        args.retries,
                    )
                )
            if total_success > 0:
                default_logger.success(
                    'avg. latency: %.0f ms' % (total_time / total_success * 1000)
                )
                exit(0)
        except KeyboardInterrupt:
            pass

        # returns 1 (anomaly) when it comes to here
        exit(1)
