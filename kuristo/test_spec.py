import yaml


class TestSpec:
    """
    Test specification
    """

    def __init__(self, name, **kwargs) -> None:
        self._name = name
        self._description = kwargs.get("description", [])
        self._steps = kwargs.get("steps", [])
        self._skip = kwargs.get("skip", None)

    @staticmethod
    def from_dict(name, data):
        ts = TestSpec(name, **data)
        return ts

    @staticmethod
    def from_file(file_path):
        test_specs = []
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            tests = data.get('tests', {})
            for t, params in tests.items():
                test_specs.append(TestSpec.from_dict(t, params))
        return test_specs
