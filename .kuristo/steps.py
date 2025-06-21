import kuristo

@kuristo.step("app-name/run-me")
def run_simulation(params):
    print("Simulating with:", params)


@kuristo.action("app-name/custom-step")
class MyCustomStep(kuristo.Step):
    def __init__(self, name, cwd, timeout, context: kuristo.Context, **kwargs):
        super().__init__(name, cwd, timeout, context)
        self.input = kwargs.get("input", "")
        self.output = kwargs.get("output", "")

    def _create_command(self):
        return f"echo Custom action: input={self.input}, output={self.output}"
