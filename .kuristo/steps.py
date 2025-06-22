import kuristo


@kuristo.step("app-name/run-me")
def run_simulation(params):
    print("Simulating with:", params)


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
        return "echo A"
