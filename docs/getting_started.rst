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

Status of a run
---------------

To display status of a run:

.. code-block:: bash

   kuristo status

Which will show somthing like this:

.. code-block:: text

   [ PASS ] #19 simple test ............................................. 1.01s

   Success: 1    Failed: 0    Skipped: 0    Total: 1
   Took: 1.5s


List available jobs
-------------------

Use this to see what jobs would be executed:

.. code-block:: bash

   kuristo list

This will traverse the directory structure from the current working directory and look for ``kuristo.yaml`` files.
You can specify different location via

.. code-block:: bash

   kuristo list /path/to/start/search/from
