import argparse

from jina.enums import GatewayProtocolType
from jina.helper import parse_host_scheme
from jina.logging.predefined import default_logger


class NetworkChecker:
    """Check if a BaseDeployment is running or not."""

    def __init__(self, args: 'argparse.Namespace'):
        """
        Create a new :class:`NetworkChecker`.

        :param args: args provided by the CLI.
        """

        import time

        from jina.clients import Client
        from jina.logging.profile import TimeContext
        from jina.serve.runtimes.gateway import GatewayRuntime
        from jina.serve.runtimes.worker import WorkerRuntime

        try:
            total_time = 0
            total_success = 0
            for j in range(args.attempts):
                with TimeContext(
                    f'ping {args.target} on {args.host} at {j} round', default_logger
                ) as tc:
                    if args.target == 'executor':
                        hostname, port, protocol, _ = parse_host_scheme(args.host)
                        r = WorkerRuntime.is_ready(ctrl_address=f'{hostname}:{port}')
                    elif args.target == 'gateway':
                        hostname, port, protocol, _ = parse_host_scheme(args.host)
                        r = GatewayRuntime.is_ready(
                            f'{hostname}:{port}',
                            protocol=GatewayProtocolType.from_string(protocol)
                        )
                    elif args.target == 'flow':
                        r = Client(host=args.host).is_flow_ready(timeout=args.timeout / 1000)
                    if not r:
                        default_logger.warning(
                            'not responding, attempt (%d/%d) in 1s'
                            % (j + 1, args.attempts)
                        )
                    else:
                        total_success += 1
                total_time += tc.duration
                if args.attempts > 0:
                    time.sleep(1)
            if total_success < args.attempts:
                default_logger.debug(
                    'message lost %.0f%% (%d/%d) '
                    % (
                        (1 - total_success / args.attempts) * 100,
                        args.attempts - total_success,
                        args.attempts,
                    )
                )
            if total_success > 0:
                default_logger.debug(
                    'avg. latency: %.0f ms' % (total_time / total_success * 1000)
                )

            if total_success >= args.min_successful_attempts:
                default_logger.debug(
                    f'readiness check succeeded {total_success} times!!!'
                )
                exit(0)
            else:
                default_logger.debug(
                    f'readiness check succeeded {total_success} times, less than {args.min_successful_attempts}'
                )
        except KeyboardInterrupt:
            pass

        # returns 1 (anomaly) when it comes to here
        exit(1)
