# FAQ

- **Is everything free?**

  Yes! We just need your feedback - use `jc survey` to help us understand your needs.

- **How powerful is JCloud?**

  JCloud scales according to your need. You can demand all the resources (GPU / RAM / CPU / Storage / instance-capacity) your Flows & Executors need. If there's anything particular you'd be looking for, you can contact us [on Slack](https://slack.jina.ai) or let us know via `jc survey`.

- **What restrictions are there on JCloud?**

  - Deployments are only supported in `us-east` region.
  - Each Executor is allowed a maximum of 4 GPUs, 16G RAM, 16 CPU cores & 10GB of block storage.

- **How long do you persist my service?**

  Flows are terminated if they are not serving requests for the last 24hrs. But this is configurable by passing {ref}`retention-days <retention-days>` argument.
