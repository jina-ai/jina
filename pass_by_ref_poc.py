from typing import Dict

def parse_params(parameters: Dict, executor_name: str):
    parsed_params = parameters
    specific_parameters = parameters.get(executor_name, None)
    if specific_parameters:
        parsed_params.update(**specific_parameters)

    return parsed_params

a = {'a': 1, 'b': {'a': 2}}
c = parse_params(a , 'b')

print(a)
print(c)