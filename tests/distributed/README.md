# Distributed Tests

During CICD, we run distributed tests with JinaD on AWS ec2 instances. To run these tests from local, we need to setup these instances using Terraform.

### Setup

1. (First time user) Install [aws-cli](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html#cliv2-linux-install) & [configure AWS credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-config) using `aws configure` command.

1. (First time user) Install [terraform cli](https://learn.hashicorp.com/tutorials/terraform/install-cli#install-terraform).

(Make sure you're under `jina` directory for the below commands)

1. Initalize terraform module

    ```bash
    terraform -chdir="tests/distributed" init
    ```

1. Create remote instances

    ```bash
    terraform -chdir="tests/distributed" apply -var="scriptpath=${PWD}/scripts/setup-jinad.sh" -var="branch=<your-branch-name>"
    ```

    File `${PWD}/scripts/setup-jinad.sh` lists all the commands to be executed on remote. Please change that if you need to customize that.

1. Get JinaD IPs (Following command will set the required environment variables in your current shell)

    ```bash
    source scripts/validate-setup-jinad.sh --dir tests/distributed --instances 2
    ```

1. Run tests

    ```bash
    pytest -s tests/distributed
    ```

1. Destroy remote instances

    ```bash
    terraform -chdir="tests/distributed" destroy -var="scriptpath=${PWD}/scripts/setup-jinad.sh" -var="branch=<your-branch-name>"
    ```
