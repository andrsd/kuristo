Architecture
============

.. figure:: images/kuristo-arch.svg
   :alt: kuristo architecture
   :align: center
   :figwidth: 100%

   Core architecture

| Kuristo works with *workflow description* files.
| It reads these files and turns them into *jobs*.
| The *scanner* is used to traverse the directories to find the workflow files.

Each job:

* has a series of *steps* that run specific actions
* comes with a *context* and an environment (*env*)

| Actions are created by an *action factory*.
| You can add your own actions, but they must be registered with the factory (see :doc:`custom_actions`).

| The *scheduler* decides the order in which jobs run when running locally.
| *Resources* describe the available capacity the scheduler can use.

When you submit jobs to a queue, each workflow is placed in that queue, and the queue’s own scheduler handles the execution order.

Scheduler
---------

Scheduler is the heart of the system.
It builds up a directed acyclic graph to connect jobs together such that it captures the dependecies betweeen them.
Jobs start as ``waiting`` to be executed.
When scheduled, they are marked as ``running``.
When they are done they are marked as ``finished``.
Jobs carry information about their exit code which determines if the finished sucessfully, failed, or timed out.

.. figure:: images/kuristo-job-status.svg
   :alt: job status
   :align: center
   :figwidth: 90%

   Job statuses
