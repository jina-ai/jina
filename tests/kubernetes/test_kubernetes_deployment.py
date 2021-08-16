

# pytest-kind
# def test_kubernetes_version(kind_cluster):
#     import tests.kubernetes.k8s_deploy_index
#     assert kind_cluster.api.version == ('1', '20')

# kubetest
def test_kubernetes_version(kube):
    print(kube)