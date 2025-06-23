from abc import abstractmethod
from .step import Step


class CompositeAction(Step):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._steps = self.create_steps()

    @abstractmethod
    def create_steps(self) -> list[Step]:
        """
        Subclasses implement this to return the list of sub-steps.
        """
        pass

    def run(self, context=None):
        output_lines = []
        for step in self._steps:
            step.run(context)
            output_lines.append(f"[{step.name}] {step.output.decode(errors='ignore').strip()}")
            if step.return_code != 0:
                self._return_code = step.return_code
                self._output = "\n".join(output_lines).encode()
                return
        self._return_code = 0
        self._output = "\n".join(output_lines).encode()
