# FAQ

- **Is everything free?**

  Yes! We just need your feedback - use `jc survey` to help us understand your needs.

- **How powerful is JCloud?**

  JCloud scales according to your need. You can demand all the resources (RAM / disk / instance-capacity) your Flows & Executors need. If there's anything particular you'd be looking for, you can contact us [on Slack](https://slack.jina.ai) or let us know via `jc survey`.

- **What restrictions are there on JCloud?**

  - JCloud doesn't support GPUs yet.
  - Executors are currently allowed a maximum of 16G RAM & 10GB disk (using EBS).
  - Deployments are only supported in `us-east` region.

- **How long do you persist my service?**

  Flows are terminated if they are not serving requests for the last 24hrs. But this is configurable by passing {ref}`retention-days <retention-days>` argument.

- **My Flow deployment failed. How I do to fix it?**

  As a first step, please enable verbose logs while deploying the Flow. You can add `--loglevel DEBUG` _before_ each CLI subcommand, e.g.

  ```bash
  jc --loglevel DEBUG deploy flow.yml
  ```

  Alternatively, you can also configure it by using Environment Variable `JCLOUD_LOGLEVEL`, e.g.

  ```bash
  export JCLOUD_LOGLEVEL=DEBUG && jc deploy flow.yml
  ```

  If you don't see any obvious errors, please raise an issue in [JCloud](https://github.com/jina-ai/jcloud/issues/new/choose)
