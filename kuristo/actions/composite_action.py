from abc import abstractmethod
from kuristo.actions.action import Action


class CompositeAction(Action):
    def __init__(self, name, context, **kwargs):
        super().__init__(name, context, **kwargs)
        self._steps = self.create_steps()

    @abstractmethod
    def create_steps(self) -> list[Action]:
        """
        Subclasses implement this to return the list of sub-steps.
        """
        pass

    def run(self) -> int:
        output_lines = []
        for step in self._steps:
            step.run()
            output_lines.append(f"[{step.name}] {step.output.decode(errors='ignore').strip()}")
            if step.return_code != 0:
                self.output = "\n".join(output_lines)
                return step.return_code
        self.output = "\n".join(output_lines)
        return 0
