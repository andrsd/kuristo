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
