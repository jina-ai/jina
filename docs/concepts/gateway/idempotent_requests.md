# IDEMPOTENT REQUESTS

These are a standard of the REST POST and PUT api's wherein duplicate requests or re-tried requests for certain use cases have a single effect and outcome. For example, user account creation is unique and retries will return an error response. In a similar way asynchronous jobs that have the same identifier will only be scheduled to run once. 
