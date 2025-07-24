import kuristo


@kuristo.action("app-name/run-me")
class RunSimulationStep(kuristo.FunctionAction):
    def __init__(self, name, context: kuristo.Context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._in = kwargs.get("input", "")
        self._out = kwargs.get("output", "")

    def execute(self):
        print("Simulating with:", self._in, self._out)


@kuristo.action("app-name/custom-step")
class MyCustomStep(kuristo.ProcessStep):
    def __init__(self, name, context: kuristo.Context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._in = kwargs.get("input", "")
        self._out = kwargs.get("output", "")

    def create_command(self):
        return f"echo Custom action: input={self._in}, output={self._out}"


@kuristo.action("app-name/mpi")
class CustomMPIAction(kuristo.MPIAction):
    def create_sub_command(self) -> str:
        return "bash -c 'echo A'"
