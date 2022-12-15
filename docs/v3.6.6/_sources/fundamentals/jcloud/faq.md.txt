# FAQ

- **Why does it take a while on every operation of `jcloud`?**

  Because the event listener at Jina Cloud is serverless by design, which means it spawns an instance on-demand to process your requests from `jcloud`. Note that operations such as `deploy`, `remove` in `jcloud` are not high-frequency. Hence, having a serverless listener is much more cost-efficient than an always-on listener. The downside is slower operations, nevertheless this does not affect the deployed service. Your deployed service is **always on**.

- **How long do you persist my service?**

  Forever. Until you manually `remove` it, we will persist your service as long as possible.

- **Is everything free?**

  Yes! We just need your feedback - use `jc survey` to help us understand your needs.

- **How powerful is Jina Cloud?**

  Jina Cloud scales according to your need. You can demand for the resources your Flow requires. If there's anything particular you'd be looking for, you can contact us [on Slack](https://slack.jina.ai) or let us know via `jc survey`.

- **How can I enable verbose logs with `jcloud`?**

  To make the output more verbose, you can add `--loglevel DEBUG` _before_ each CLI subcommand, e.g.

  ```bash
  jc --loglevel DEBUG deploy toy.yml
  ```