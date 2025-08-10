Getting Started
===============

This guide walks you through installing Kuristo, writing your first workflow, and running it locally.


Installation
------------

.. tab-set::

   .. tab-item:: pip

      Install from PyPI:

      .. code-block:: bash

         pip install kuristo

   .. tab-item:: source

      Clone the repository and install it from source:

      .. code-block:: bash

         git clone https://github.com/andrsd/kuristo.git
         cd kuristo
         pip install .


Basic Workflow
--------------

Kuristo workflows are written in YAML. Here's a minimal example:

.. code-block:: yaml

   jobs:
     single-case:
       - name: simple test
         steps:
           - run: ./generate_mesh.sh
           - run: ./simulate --input mesh.exo
           - run: ./check_results output.csv

Save this as ``kuristo.yml``.


Running the Workflow
--------------------

To run a workflow:

.. code-block:: bash

   kuristo run /path/to/workflow-file.yaml

Or run all workflows from a location:

.. code-block:: bash

   kuristo run /root/dir/with/workflows

Kuristo will traverse the directory structure and try to find ``kuristo.yaml`` files with workflows.
Then, it will execute each job in order, tracking progress and logging output into the ``.kuristo-out/`` directory.
If no parameter is used it will search from the current working directory.

The command-line output will look like this:

.. code-block:: text

   [ PASS ] #19 simple test ............................................. 1.01s

   Success: 1    Failed: 0    Skipped: 0    Total: 1
   Took: 1.5s

By default, output is printed to the terminal and stored in per-run and per-job subdirectories under ``.kuristo-out/``.


**Options and Verbosity**

You can control verbosity with the ``--verbosity`` option:

.. code-block:: bash

   kuristo run workflow.yml --verbosity=2

Verbosity levels:

- `0`: silent
- `1`: errors only
- `2`: default
- `3`: detailed output for each step

It is possible to specify multiple locations to scan, i.e.:

.. code-block:: bash

   kuristo run /path1 /path2


List available jobs
-------------------

Use this to see what jobs are would be executed:

.. code-block:: bash

   kuristo list

This will traverse the directory structure from the current working directory and look for ``kuristo.yaml`` files.
You can specify different location via

.. code-block:: bash

   kuristo list /path/to/start/search/from


Environment diagnostics
-----------------------

Use the ``doctor`` command to generate a diagnostic report about your Kuristo environment:

.. code-block:: bash

   kuristo doctor

This outputs detailed information including:

- Kuristo version and Python interpreter
- Platform and CPU configuration
- Log and config file locations
- MPI launcher
- Active plugins, registered actions
- Logging and cleanup policies
