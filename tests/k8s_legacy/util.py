import asyncio
import os

async def create_all_flow_deployments_and_wait_ready(
        flow_dump_path,
        namespace,
        api_client,
        app_client,
        core_client,
        deployment_replicas_expected,
        logger,
):
    from kubernetes import utils

    namespace = namespace.lower()
    namespace_object = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {'name': f'{namespace}'},
    }
    try:
        logger.info(f'create Namespace {namespace}')
        utils.create_from_dict(api_client, namespace_object)
    except:
        pass

    while True:
        ns_items = core_client.list_namespace().items
        if any(item.metadata.name == namespace for item in ns_items):
            logger.info(f'created Namespace {namespace}')
            break
        logger.info(f'waiting for Namespace {namespace}')
        await asyncio.sleep(1.0)

    deployment_set = set(os.listdir(flow_dump_path))
    for deployment_name in deployment_set:
        file_set = set(os.listdir(os.path.join(flow_dump_path, deployment_name)))
        for file in file_set:
            try:
                utils.create_from_yaml(
                    api_client,
                    yaml_file=os.path.join(flow_dump_path, deployment_name, file),
                    namespace=namespace,
                )
            except Exception as e:
                # some objects are not successfully created since they exist from previous files
                logger.info(
                    f'Did not create resource from {file} for pod {deployment_name} due to {e} '
                )
                pass

    # wait for all the pods to be up
    expected_deployments = sum(deployment_replicas_expected.values())
    while True:
        namespaced_pods = core_client.list_namespaced_pod(namespace)
        if (
                namespaced_pods.items is not None
                and len(namespaced_pods.items) == expected_deployments
        ):
            break
        logger.info(
            f'Waiting for all {expected_deployments} Deployments to be created, only got {len(namespaced_pods.items) if namespaced_pods.items is not None else None}'
        )
        await asyncio.sleep(1.0)

    # wait for all the pods to be up
    resp = app_client.list_namespaced_deployment(namespace=namespace)
    resp2 = app_client.list_namespaced_stateful_set(namespace=namespace)
    deployment_names = set([item.metadata.name for item in resp.items])
    sset_names = set([item.metadata.name for item in resp2.items])
    all_execs_names = deployment_names.union(sset_names)
    assert all_execs_names == set(deployment_replicas_expected.keys())
    while len(all_execs_names) > 0:
        deployments_ready = []
        for deployment_name in all_execs_names:
            if deployment_name in deployment_names:
                api_response = app_client.read_namespaced_deployment(
                    name=deployment_name, namespace=namespace
                )
            elif deployment_name in sset_names:
                api_response = app_client.read_namespaced_stateful_set(
                    name=deployment_name, namespace=namespace
                )
            expected_num_replicas = deployment_replicas_expected[deployment_name]
            if (
                    api_response.status.ready_replicas is not None
                    and api_response.status.ready_replicas == expected_num_replicas
            ):
                logger.info(f'Deployment {deployment_name} is now ready')
                deployments_ready.append(deployment_name)
            else:
                logger.info(
                    f'Deployment {deployment_name} is not ready yet: ready_replicas is {api_response.status.ready_replicas} not equal to {expected_num_replicas}'
                )

        for deployment_name in deployments_ready:
            all_execs_names.remove(deployment_name)
        logger.info(f'Waiting for {all_execs_names} to be ready')
        await asyncio.sleep(1.0)
