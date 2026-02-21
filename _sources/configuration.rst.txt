Configuration
=============

Kuristo’s behavior can be customized using a configuration file named ``config.yaml``.
Kuristo searches for this file in a ``.kuristo`` directory, starting from the current working directory and moving up through parent directories until it finds the first match.
The available configuration options are listed below.

Basic options
-------------

``base:``
   General settings section.

``base.workflow-filename``
   Name of files that contain workflow descriptions.
   These files are looked for when Kuristo executes workflows from a location.

   Default value: ``kuristo.yaml``

``base.console-width``
   Maximum width for console output, in characters.

   Default value: ``100``


Logging options
---------------

``log:``
   Logging settings section.

``log.dir-name``
   Directory where logs will be stored.

``log.history``
   Number of recent runs to keep. Older runs are automatically deleted when this limit is exceeded.
   Tagged runs are protected from deletion and do not count toward this limit.
   Use the ``tag`` command to protect important results (e.g., versions, baselines).

   Default value: ``5``

``log.cleanup``
   Currently, does nothing.


Resources
---------

``resources:``
   Resource allocation settings.

``resources.num-cores``
   Maximum number of CPU cores available for parallel job execution.
   Kuristo will not attempt to run more than this many cores in parallel.

   Default value: System CPU count (determined automatically)


Runner
------

``runner:``
   Main runner settings.

``runner.mpi-launcher``
   MPI command used to launch jobs.

   Default value: ``mpirun``

   Can be overridden with the ``KURISTO_MPI_LAUNCHER`` environment variable:

   .. code:: bash

      KURISTO_MPI_LAUNCHER=mpiexec kuristo run tests/


Batch
-----

``batch:``
   Batch submission settings.

``batch.backend``
   Which batch system to use (e.g., slurm).

``batch.default-account``
   Currently, does nothing.

``batch.partition``
   Cluster partition or queue to submit jobs to.


Example
-------

This example shows how to setup kuristo for a slurm queue, submitting into
a ``default`` partition.
The MPI launcher is set to ``mpiexec``.
And we want to keep 10 previous runs.


.. code:: yaml

   log:
      history: 10

   runner:
      mpi-launcher: mpiexec

   batch:
      backend: slurm
      partition: default
