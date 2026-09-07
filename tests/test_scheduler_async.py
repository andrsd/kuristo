import asyncio
from unittest.mock import MagicMock

from kuristo.resources import Resources
from kuristo.scheduler import AsyncResources, Scheduler
from kuristo.workflow import Workflow


def test_async_resources():
    """Test that AsyncResources allocates/frees cores correctly and supports priority blocking."""

    async def run_test():
        rcs = Resources()
        # Mocking num_cores to 4
        rcs._max_cores = 4
        rcs._n_cores_available = 4

        async_rcs = AsyncResources(rcs)

        # Acquire 2 cores
        await async_rcs.acquire(2)
        assert rcs.available_cores == 2

        acquired_non_priority = False
        acquired_priority = False

        async def run_priority():
            nonlocal acquired_priority
            # Needs 3 cores (which are not immediately available because 2 are used)
            await async_rcs.acquire(3, priority=True)
            acquired_priority = True
            await async_rcs.release(3)

        async def run_non_priority():
            nonlocal acquired_non_priority
            # Needs 1 core (which is available, but must wait because a priority task is queued)
            await async_rcs.acquire(1, priority=False)
            acquired_non_priority = True
            await async_rcs.release(1)

        # Start priority and non-priority tasks
        asyncio.create_task(run_priority())
        asyncio.create_task(run_non_priority())

        # Let tasks run and yield
        await asyncio.sleep(0.01)

        # Neither should be acquired yet (priority needs 3 cores, total free is 2; non-priority must yield to priority)
        assert not acquired_priority
        assert not acquired_non_priority

        # Release 1 core (total free becomes 3) -> Priority task should acquire and finish
        await async_rcs.release(1)
        await asyncio.sleep(0.01)

        assert acquired_priority
        # Now non-priority should also have acquired and finished
        assert acquired_non_priority

    asyncio.run(run_test())


def test_scheduler_async_run(tmp_path):
    """Test Scheduler run_all_jobs runs with asyncio successfully."""
    # Create mock workflows and resources
    mock_workflow = MagicMock(spec=Workflow)
    mock_workflow.file_name = "test_wf.yaml"
    mock_workflow.jobs = {}

    rcs = Resources()
    scheduler = Scheduler(workflows=[mock_workflow], rcs=rcs, out_dir=tmp_path)

    # Run the scheduler (should execute without error since there are no jobs to run)
    scheduler.run_all_jobs()

    assert scheduler.total_runtime >= 0
    assert scheduler.exit_code() == 0
