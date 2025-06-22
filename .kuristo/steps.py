import kuristo


@kuristo.step("app-name/run-me")
def run_simulation(params):
    print("Simulating with:", params)


@kuristo.action("app-name/custom-step")
class MyCustomStep(kuristo.Step):
    def __init__(self, name, context: kuristo.Context, **kwargs):
        super().__init__(name, context, **kwargs)
        self.input = kwargs.get("input", "")
        self.output = kwargs.get("output", "")

    def create_command(self):
        return f"echo Custom action: input={self.input}, output={self.output}"


@kuristo.action("app-name/mpi")
class CustomMPIAction(kuristo.MPIAction):
    def _create_sub_command(self) -> str | None:
        return "echo A"
