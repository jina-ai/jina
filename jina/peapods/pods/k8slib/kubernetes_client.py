class K8sClients:
    """
    The Kubernetes api is wrapped into a class to have a lazy reading of the cluster configuration.

    """

    def __init__(self):
        import kubernetes

        try:
            # try loading kube config from disk first
            kubernetes.config.load_kube_config()
        except kubernetes.config.config_exception.ConfigException:
            # if the config could not be read from disk, try loading in cluster config
            # this works if we are running inside k8s
            kubernetes.config.load_incluster_config()

        self._k8s_client = kubernetes.client.ApiClient()
        self._core_v1 = None
        self._apps_v1 = None
        self._beta = None
        self._networking_v1_beta1_api = None

    @property
    def k8s_client(self):
        """Client for making requests to Kubernetes

        :return: k8s client
        """
        return self._k8s_client

    @property
    def core_v1(self):
        """V1 client for core

        :return: v1 client
        """
        if not self._core_v1:
            from kubernetes import client

            self._core_v1 = client.CoreV1Api(api_client=self._k8s_client)
        return self._core_v1

    @property
    def apps_v1(self):
        """V1 client for core

        :return: v1 client
        """
        if not self._apps_v1:
            from kubernetes import client

            self._apps_v1 = client.AppsV1Api(api_client=self._k8s_client)
        return self._apps_v1

    @property
    def beta(self):
        """Beta client for using beta features

        :return: beta client
        """
        if not self._beta:
            from kubernetes import client

            self._beta = client.ExtensionsV1beta1Api(api_client=self._k8s_client)
        return self._beta

    @property
    def networking_v1_beta1_api(self):
        """Networking client used for creating the ingress

        :return: networking client
        """
        if not self._networking_v1_beta1_api:
            from kubernetes import client

            self._networking_v1_beta1_api = client.NetworkingV1beta1Api(
                api_client=self._k8s_client
            )
        return self._networking_v1_beta1_api
