Writing Workflows
=================

This page explains how to create and structure Kuristo workflow files using YAML syntax.

Basic Structure
---------------

A Kuristo workflow defines a set of **jobs**, each identified by a unique job ID.
Jobs contain one or more **steps** to execute.

Example:

.. code-block:: yaml

   jobs:
     job1:
       name: simulation
       steps:
         - run: ./prepare.sh
         - run: ./simulate --input data.in
         - run: ./postprocess.sh

- ``job1`` is the job ID (must be unique within the workflow)


Job Fields
----------

- ``name`` (string, optional): Descriptive job name shown in logs and reports
- ``needs`` (list of job IDs, optional): Defines job execution order
- ``steps`` (list, required): Commands or structured actions to run
- ``strategy``: TODO

Step Fields
-----------

Each step represents a unit of work (e.g., a script or an action).
You can also customize the runtime environment.

Supported step fields:

- ``run`` (string): Shell command to execute
- ``working-directory`` (string, optional): Directory to run the command in
- ``id`` (string, optional): Assign unique identified to a step
- ``uses:`` (string): Name of the action to run

Example:

.. code-block:: yaml

   jobs:
     mesh:
       name: Generate mesh
       steps:
         - run: ./mesh.sh
           shell: /bin/bash
           workdir: scripts/


Job Dependencies
----------------

Use the ``needs`` field to create dependencies between jobs. This controls execution order.

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

Jobs without dependencies may run in parallel, depending on available system resources.
