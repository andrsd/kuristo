.. kuristo documentation master file, created by

Kuristo
=======

Kuristo is a lightweight automation framework for scientific and high-performance computing (HPC) workflows.
It allows you to define and run simulation-based validation and verification tasks using a simple, declarative YAML syntax.

Kuristo is particularly suited for:

- Running structured tests for scientific codes
- Automating multi-step workflows (e.g., mesh generation → simulation → postprocessing)
- Integrating with both sequential and MPI-based applications
- Keeping reproducibility and traceability in focus

It is inspired by GitHub Actions, but tailored for scientific computing.

**Quick Example**

.. code-block:: yaml

   jobs:
     single-case:
       - name: single case
         description: Single test case
         steps:
           - run: generate_mesh.sh
           - run: run_simulation --input mesh.exo
           - run: compare_results reference.csv output.csv

Contents
--------

.. toctree::
   :maxdepth: 1

   getting_started
   user_interface
   writing_workflows
   actions/index
   custom_actions
   configuration
   architecture
   reference
