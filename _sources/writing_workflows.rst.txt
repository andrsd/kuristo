Writing Workflows
=================

This page explains how to create and structure Kuristo workflow files using YAML syntax.

Basic Structure
---------------

A Kuristo workflow defines a set of **jobs**, each identified by a unique job ID.
Jobs contain one or more **steps** to execute.

.. rubric:: Example of a workflow file

.. code-block:: yaml

   jobs:
     job1:
       name: simulation
       steps:
         - run: ./prepare.sh
         - run: ./simulate --input data.in
         - run: ./postprocess.sh

``jobs.<id>`` (string, required)
   Job ID that is unique within the workflow file

``jobs.<id>.name`` (string, optional)
   Descriptive job name shown in logs and reports

``jobs.<id>.steps`` (list, required)
   Commands or structured actions to run

Step Fields
-----------

Each step represents a unit of work (e.g., a script or an action).

.. rubric:: Example of running a shell command

.. code-block:: yaml

   jobs:
     mesh:
       name: Generate mesh
       steps:
         - run: ./mesh.sh
           working-directory: scripts/

``jobs.<id>.steps[*].run`` (string)
   Shell command to execute

``jobs.<id>.steps[*].working-directory`` (string, optional)
   Directory to run the command in

.. rubric:: Example of running an action

.. code-block:: yaml

   jobs:
     mesh:
       name: Generate mesh
       steps:
         - uses: my-action/execute
           with:
             input: input_file.txt

``jobs.<id>.steps[*].uses`` (string)
   The name of the action to execute

``jobs.<id>.steps[*].with:``
   Specify parameters that are used by the action

Job Dependencies
----------------

Use the ``needs`` field to create dependencies between jobs. This controls execution order.

.. rubric:: Example of setting dependencies

.. code-block:: yaml

   jobs:
     prep:
       name: Prepare
       steps:
         - run: ./prepare_inputs.sh

     sim:
       name: Run Simulation
       needs: [prep]
       steps:
         - run: ./simulate

``jobs.<id>.needs`` (list of job IDs, optional)
   Name of the job that must finish before this job starts

Jobs without dependencies may run in parallel, depending on available system resources.

Strategy Matrix
---------------

Use ``jobs.<id>.strategy.matrix`` to create multiple job variations automatically. Each combination runs as a separate job.
This is useful for running the same test or simulation with different parameters, configurations, or mesh sizes.

.. rubric:: Cartesian Product

Create jobs from all combinations of matrix variables:

.. code-block:: yaml

   jobs:
     convergence-study:
       strategy:
         matrix:
           mesh_size: [coarse, medium, fine]
           solver: [direct, iterative]
       steps:
         - run: ./simulate --mesh ${{ matrix.mesh_size }} --solver ${{ matrix.solver }}
         - uses: checks/exodiff
           with:
             input: results.e
             gold: gold/results_${{ matrix.mesh_size }}_${{ matrix.solver }}.e

This creates 6 job variations (3 mesh sizes × 2 solvers), each running independently.

.. rubric:: Explicit Combinations

Use ``include`` to specify exact combinations when not all are valid or needed:

.. code-block:: yaml

   jobs:
     verification:
       strategy:
         matrix:
           include:
             - model: steady_state
               preconditioner: ilu
             - model: transient
               preconditioner: ml
             - model: transient
               preconditioner: ilu
               slow: true
       steps:
         - run: ./verify --model ${{ matrix.model }} --prec ${{ matrix.preconditioner }}

This creates only the specified 3 combinations rather than all possible pairs.

Job Labels
----------

Use the ``labels`` field to tag jobs for selective execution. This allows you to run subsets of jobs without creating separate workflow files.

.. rubric:: Example of using labels

.. code-block:: yaml

   jobs:
     smoke-test:
       name: Smoke Test
       labels: [smoke, quick]
       steps:
         - run: ./test_smoke.sh

     integration-test:
       name: Integration Test
       labels: [integration, slow]
       steps:
         - run: ./test_integration.sh

     unit-test:
       name: Unit Tests
       steps:
         - run: ./test_unit.sh

``jobs.<id>.labels`` (list of strings, optional)
   Tags for filtering jobs during execution. Jobs can have multiple labels.
   See the User Interface documentation for information on filtering jobs with the ``--label`` option.
