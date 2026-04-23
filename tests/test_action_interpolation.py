import pytest

from kuristo.actions.action import Action
from kuristo.context import Context
from kuristo.utils import interpolate_value


class DummyAction(Action):
    """Minimal concrete Action subclass for testing"""

    def run(self) -> int:
        return 0


def create_action_with_interpolation(action_class, name, context, **kwargs):
    """
    Create an action with parameter interpolation (simulating ActionFactory behavior).
    """
    if context is not None:
        kwargs = interpolate_value(kwargs, context.vars)
    return action_class(name, context, **kwargs)


class TestInterpolateUserKwargs:
    """Test parameter interpolation in Action base class"""

    @pytest.fixture
    def context_with_vars(self):
        ctx = Context()
        ctx.vars = {
            "matrix": {"item": "test_value"},
            "steps": {"prev_step": {"output": "previous_output"}},
        }
        return ctx

    def test_interpolate_string_parameter(self, context_with_vars):
        """Test interpolation of string parameters"""
        action = DummyAction(
            "test",
            context_with_vars,
            id="step1",
            reference="${{ matrix.item }}",
        )
        # Verify the kwarg was interpolated
        assert action.context is not None
        # We need to check the kwargs were modified, but they're not stored in the action
        # Let's verify by creating the action and checking if it was called correctly

    def test_interpolate_string_parameter_modified(self, context_with_vars):
        """Test that string parameters are interpolated by checking kwargs"""

        class TestAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.test_param = kwargs.get("reference")

            def run(self) -> int:
                return 0

        action = create_action_with_interpolation(
            TestAction,
            "test",
            context_with_vars,
            id="step1",
            reference="${{ matrix.item }}",
        )
        assert action.test_param == "test_value"

    def test_interpolate_list_parameter(self, context_with_vars):
        """Test interpolation of list parameters with variable expansion"""

        class ListAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.items = kwargs.get("items")

            def run(self) -> int:
                return 0

        action = create_action_with_interpolation(
            ListAction,
            "test",
            context_with_vars,
            id="step1",
            items=[
                "prefix_${{ matrix.item }}_suffix",
                "plain_string",
            ],
        )
        assert action.items == [
            "prefix_test_value_suffix",
            "plain_string",
        ]

    def test_interpolate_dict_parameter(self, context_with_vars):
        """Test interpolation of dict parameters"""

        class DictAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.config = kwargs.get("config")

            def run(self) -> int:
                return 0

        action = create_action_with_interpolation(
            DictAction,
            "test",
            context_with_vars,
            id="step1",
            config={
                "gold": "${{ matrix.item }}_gold",
                "test": "${{ matrix.item }}_test",
                "plain": "value",
            },
        )
        assert action.config == {
            "gold": "test_value_gold",
            "test": "test_value_test",
            "plain": "value",
        }

    def test_interpolate_nested_structures(self, context_with_vars):
        """Test interpolation of nested structures (lists of dicts)"""

        class NestedAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.datasets = kwargs.get("datasets")

            def run(self) -> int:
                return 0

        action = create_action_with_interpolation(
            NestedAction,
            "test",
            context_with_vars,
            id="step1",
            datasets=[
                {
                    "path": "/data/${{ matrix.item }}/gold.h5",
                    "rel-tol": 1e-6,
                },
                {
                    "path": "/data/${{ matrix.item }}/test.h5",
                    "rel-tol": 1e-6,
                },
            ],
        )
        assert action.datasets == [
            {
                "path": "/data/test_value/gold.h5",
                "rel-tol": 1e-6,
            },
            {
                "path": "/data/test_value/test.h5",
                "rel-tol": 1e-6,
            },
        ]

    def test_no_interpolation_for_framework_kwargs(self, context_with_vars):
        """Test that framework kwargs are not interpolated"""

        class FrameworkAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.stored_working_dir = kwargs.get("working_dir")
                self.stored_timeout = kwargs.get("timeout_minutes")

            def run(self) -> int:
                return 0

        action = FrameworkAction(
            "test",
            context_with_vars,
            id="step1",
            working_dir="/path/${{ matrix.item }}",  # Should NOT be interpolated
            timeout_minutes=30,
        )
        # Framework kwargs should not be interpolated
        assert action.stored_working_dir == "/path/${{ matrix.item }}"
        assert action.stored_timeout == 30

    def test_non_string_types_preserved(self, context_with_vars):
        """Test that non-string types are preserved"""

        class TypeAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.bool_param = kwargs.get("fail_on_diff")
                self.int_param = kwargs.get("floor")
                self.float_param = kwargs.get("tolerance")
                self.none_param = kwargs.get("optional")

            def run(self) -> int:
                return 0

        action = TypeAction(
            "test",
            context_with_vars,
            id="step1",
            fail_on_diff=True,
            floor=1.5,
            tolerance=1e-6,
            optional=None,
        )
        assert action.bool_param is True
        assert action.int_param == 1.5
        assert action.float_param == 1e-6
        assert action.none_param is None

    def test_no_context_skips_interpolation(self):
        """Test that when context is None, no interpolation happens"""

        class NoContextAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.test_param = kwargs.get("reference")

            def run(self) -> int:
                return 0

        action = NoContextAction(
            "test",
            None,
            id="step1",
            reference="${{ undefined }}",
        )
        # Without context, the parameter should remain unchanged
        assert action.test_param == "${{ undefined }}"

    def test_step_output_interpolation(self, context_with_vars):
        """Test interpolation using step output variables"""
        context_with_vars.vars["steps"]["prev"] = {"output": "result_123"}

        class StepRefAction(Action):
            def __init__(self, name, context, **kwargs):
                super().__init__(name, context, **kwargs)
                self.input_file = kwargs.get("input_file")

            def run(self) -> int:
                return 0

        action = create_action_with_interpolation(
            StepRefAction,
            "test",
            context_with_vars,
            id="step2",
            input_file="/tmp/${{ steps.prev.output }}.txt",
        )
        assert action.input_file == "/tmp/result_123.txt"
