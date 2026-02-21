Reference
=========

Workflow files use YAML syntax.
If you are new to YAML, you can `Learn YAML in Y minutes <https://learnxinyminutes.com/yaml/>`_.

jobs
----

Workflow is made up of jobs, which run in parallel by default.

jobs.<id>
---------

The job ID, which must be unique within the workflow file.
This ID is used to reference the job in ``needs`` dependencies and in command line output.

jobs.<id>.name
--------------

| Display name for the job shown in the user interface and logs.
| Optional field; defaults to the job ID if not specified.

Example:

.. code:: yaml

   my-job:
     name: "Convergence Study"

jobs.<id>.description
---------------------

| Longer description of what the job does.
| Optional field used for documentation purposes.

Example:

.. code:: yaml

   my-job:
     description: "Run simulation with varying mesh refinements"

jobs.<id>.needs
---------------

| Job dependencies - other jobs that must finish before this job starts.
| Optional field; can be a single job ID (string) or multiple job IDs (list).
| Dependent jobs run in parallel only if all their dependencies are satisfied.

Example with single dependency:

.. code:: yaml

   jobs:
     prepare:
       description: "Generate mesh"
       steps:
         - run: ./generate_mesh.sh

     simulate:
       name: "Run Simulation"
       needs: prepare
       steps:
         - run: ./simulate

Example with multiple dependencies:

.. code:: yaml

   jobs:
     build:
       steps:
         - run: make

     test-unit:
       needs: build
       steps:
         - run: pytest unit_tests/

     test-integration:
       needs: build
       steps:
         - run: pytest integration_tests/

     report:
       needs: [test-unit, test-integration]
       steps:
         - run: ./generate_report.py

jobs.<id>.labels
----------------

| List of labels for filtering jobs during execution.
| Allows selective execution of job subsets using the ``--label`` CLI option.
| Optional field with no default value.

Example:

.. code:: yaml

   my-job:
     labels: [smoke, quick]


jobs.<id>.env
-------------

| Environment variables for the job.
| Optional field; a dictionary of key-value pairs passed to all steps in the job.

Example:

.. code:: yaml

   my-job:
     env:
       PRECISION: double
       NUM_THREADS: 4
     steps:
       - run: ./simulate  # Can use $PRECISION and $NUM_THREADS

jobs.<id>.skip
--------------

| Skip this job and mark it as skipped in the report.
| Optional field; provide a string describing why the job is skipped.
| If not set or empty, the job runs normally.

Example:

.. code:: yaml

   my-job:
     skip: "Not supported on this platform"
     steps:
       - run: ./test

jobs.<id>.timeout-minutes
-------------------------

| Maximum time for the job to finish, in minutes.
| Default value is ``60``.

jobs.<id>.strategy
------------------

| Defines matrix configurations to create multiple job variations.
| Optional field; if not specified, the job runs once without variations.

jobs.<id>.strategy.matrix
-------------------------

| Dictionary of variables and their values for creating job combinations.
| Creates a job for each combination of variable values (Cartesian product).
| Variables are accessible in steps and job fields via ``${{ matrix.variable-name }}``.

Example (Cartesian product of 3 mesh sizes × 2 solvers = 6 jobs):

.. code:: yaml

   my-job:
     strategy:
       matrix:
         mesh: [coarse, medium, fine]
         solver: [direct, iterative]
     steps:
       - run: ./simulate --mesh ${{ matrix.mesh }} --solver ${{ matrix.solver }}

jobs.<id>.strategy.matrix.include
---------------------------------

| List of explicit combinations to use instead of a full Cartesian product.
| Optional field; if present, only these combinations are created.
| Useful when not all variable combinations are valid or desired.

Example (only 2 specific combinations):

.. code:: yaml

   my-job:
     strategy:
       matrix:
         include:
           - mesh: coarse
             solver: direct
           - mesh: fine
             solver: iterative
     steps:
       - run: ./simulate --mesh ${{ matrix.mesh }} --solver ${{ matrix.solver }}

jobs.<id>.steps
---------------

| List of steps that make up the job.
| Required field; every job must have at least one step.
| Steps are executed sequentially within a job.
| If any step fails (unless ``continue-on-error`` is true), the job fails.

jobs.<id>.steps[*].id
---------------------

| Unique identifier for the step within the job.
| Optional field; useful for referencing step outputs in later steps.

Example:

.. code:: yaml

   steps:
     - id: simulation
       run: ./simulate > results.txt
     - name: Verify results
       run: grep "SUCCESS" ${{ steps.simulation.output }}

jobs.<id>.steps[*].name
-----------------------

| Display name for the step shown in logs and user interface.
| Optional field; defaults to showing the step index if not specified.

Example:

.. code:: yaml

   steps:
     - name: "Run convergence study"
       run: ./simulate

jobs.<id>.steps[*].num-cores
----------------------------

| Number of CPU cores required for this step.
| Optional field; default is ``1``.
| Kuristo will allocate the requested cores and ensure total allocation doesn't exceed configured limit.

jobs.<id>.steps[*].continue-on-error
------------------------------------

| Indicates if the workflow execution should continue if this step fails.
| Default value is ``False``

jobs.<id>.steps[*].description
------------------------------

| Documentation string describing what the step does.
| Optional field; useful for understanding workflow purpose.

jobs.<id>.steps[*].run
----------------------

| Shell commands to execute.
| Either ``run`` or ``uses`` must be specified (mutually exclusive).
| Commands are executed with the specified shell.

Example:

.. code:: yaml

   steps:
     - name: "Prepare and run simulation"
       run: |
         ./prepare_mesh.sh data/input.msh
         ./simulate --config sim.cfg --output results.e
         ./postprocess.py results.e > analysis.txt

jobs.<id>.steps[*].uses
-----------------------

| Name of a custom action (plugin) to execute.
| Either ``run`` or ``uses`` must be specified (mutually exclusive).
| Action names follow the format ``namespace/action-name``.

Example:

.. code:: yaml

   steps:
     - name: "Validate output"
       uses: checks/exodiff
       with:
         input: results.e
         gold: gold.e

jobs.<id>.steps[*].with
-----------------------

| Parameters passed to the action specified by ``uses``.
| Optional field; a dictionary of key-value pairs.
| Each action defines which parameters it accepts.

Example:

.. code:: yaml

   steps:
     - uses: checks/regex
       with:
         input: output.txt
         pattern: "SUCCESS"

jobs.<id>.steps[*].shell
------------------------

| Shell to use for executing ``run`` commands.
| Optional field; default is ``sh``.
| Common values: ``sh``, ``bash``, ``zsh``.

jobs.<id>.steps[*].working-directory
------------------------------------

| Directory to execute the step in.
| Optional field; if not specified, uses the job's working directory.

Example:

.. code:: yaml

   steps:
     - name: "Build"
       working-directory: build/
       run: cmake .. && make

jobs.<id>.steps[*].env
----------------------

| Environment variables specific to this step.
| Optional field; a dictionary of key-value pairs.
| Merged with job-level environment variables.

Example:

.. code:: yaml

   steps:
     - name: "Run with custom settings"
       env:
         OMP_NUM_THREADS: 4
         DEBUG: 1
       run: ./simulate

jobs.<id>.steps[*].timeout-minutes
----------------------------------

| Maximum time for the step to complete, in minutes.
| Optional field; default is ``60``.
| If exceeded, the step is terminated and marked as failed.

jobs.<id>.steps[*].continue-on-error
------------------------------------

| Continue job execution if this step fails.
| Optional field; default is ``false``.
| When ``true``, a failed step does not fail the entire job.
