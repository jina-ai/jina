
def get_run_parameters(target_dimension):
    return {
        'JINA_PARALLEL': '1',
        'JINA_SHARDS': '1',
        'JINA_WORKSPACE': f'workspace_eval_{target_dimension}',
        'JINA_TARGET_DIMENSION': f'{target_dimension}'
    }
