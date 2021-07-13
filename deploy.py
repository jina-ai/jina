from jina import Flow

f = Flow(name='f1')\
    .add(uses='jinahub+docker://CLIPTextEncoder', replicas=2)\
    .add(uses='jinahub+docker://CLIPImageEncoder', replicas=2)
f.deploy('k8s')
print('done')
