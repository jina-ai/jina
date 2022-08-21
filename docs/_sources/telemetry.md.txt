# Telemetry

Telemetry is the process of collecting data about the usage of a system. This data can be used to improve the system by understanding how it is being used and what areas need improvement.

Jina uses telemetry to collect data about how the software is being used. This data is then used to improve the software. For example, if Jina sees that a lot of users are having trouble with a certain feature, they can improve that feature to make it easier to use.

Telemetry is important for Jina because it allows the team to understand how the software is being used and what areas need improvement. Without telemetry, Jina would not be able to improve as quickly or as effectively.

The data collected include:

- Jina and its dependencies versions;
- A hashed unique user identifier;
- A hashed unique session identifier;
- Boolean events: start of a Flow, Gateway and Runtime.

To opt out of usage statistics, add the `--optout-telemetry` argument to the different Flows and Executors or set the `JINA_OPTOUT_TELEMETRY=1` as an environment variable.