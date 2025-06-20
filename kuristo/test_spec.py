

class TestSpec:
    """
    Data class with a test specification
    """

    class Step:
        """
        Data class with description of a step
        """

        def __init__(self, **kwargs):
            self._description = kwargs.get("description", "")
            self._name = kwargs.get("name", None)
            self._uses = kwargs.get("uses", None)
            self._with = kwargs.get("with", {})
            self._run = kwargs.get("run", None)
            self._shell = kwargs.get("shell", "sh")
            self._id = kwargs.get("id", None)
            self._work_dir = kwargs.get("working-directory", None)
            self._timeout_minutes = kwargs.get("timeout-minutes", 60)

        @property
        def name(self):
            """
            Return step name
            """
            return self._name

        @property
        def uses(self):
            """
            Return the action name that is used by the step
            """
            return self._uses

        @property
        def run(self):
            """
            Return the "script" that should be executed
            """
            return self._run

        @property
        def id(self):
            """
            Return the step ID
            """
            return self._id

        @property
        def working_directory(self):
            """
            Return the step working directory
            """
            return self._work_dir

        @property
        def timeout_minutes(self):
            """
            Return the timeout in minutes
            """
            return self._timeout_minutes

        @property
        def params(self):
            """
            Return the step ID
            """
            return self._with

        @staticmethod
        def from_dict(**kwargs):
            step = TestSpec.Step(**kwargs)
            return step

    def __init__(self, name, **kwargs) -> None:
        self._name = name
        self._description = kwargs.get("description", "")
        self._steps = self._build_steps(kwargs.get("steps"))
        self._skip = kwargs.get("skip", None)
        self._timeout_minutes = kwargs.get("timeout-minutes", 60)
        val = kwargs.get("needs", [])
        self._needs = val if isinstance(val, list) else [val]

    @property
    def name(self):
        """
        Return test name
        """
        return self._name

    @property
    def steps(self):
        """
        Return test steps
        """
        return self._steps

    @property
    def description(self):
        """
        Return test description
        """
        return self._description

    @property
    def skip(self):
        """
        Should the test be skipped?
        """
        return self._skip is not None

    @property
    def skip_reason(self):
        """
        Return the reason why test is marked as skipped
        """
        return self._skip

    @property
    def needs(self):
        """
        Return the dependencies
        """
        return self._needs

    @property
    def timeout_minutes(self):
        """
        Return the timeout in minutes
        """
        return self._timeout_minutes

    def _build_steps(self, data):
        """
        Build test steps
        """
        steps = []
        for entry in data:
            steps.append(self.Step.from_dict(**entry))
        return steps

    @staticmethod
    def from_dict(name, data):
        ts = TestSpec(name, **data)
        return ts
