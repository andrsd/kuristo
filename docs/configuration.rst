Configuration
====

Kuristo’s behavior can be customized using a configuration file named ``config.yaml``.
Kuristo searches for this file in a ``.kuristo`` directory, starting from the current working directory and moving up through parent directories until it finds the first match.
The available configuration options are listed below.

Basic options
----

``base:``
   Logging settings section.

``workflow-filename``
   Name of files that contain workflow descriptions.
   These files are looked for whne we have kuristo execute workflows from a location.

   Default value: ``kuristo.yaml``


Logging options
----

``log:``
   Logging settings section.

``log.dir-name``
   Directory where logs will be stored.

``log.history``
   Number of past log files to keep.

   Default value: ``5``

``log.cleanup``
   Currently, does nothing.


Runner
----

``runner:``
   Main runner settings.

``runner.mpi-launcher``
   MPI command used to launch jobs.

   Default value: ``mpirun``


Batch
----

``batch:``
   Batch submission settings.

``batch.backend``
   Which batch system to use (e.g., slurm).

``batch.default-account``
   Currently, does nothing.

``batch.partition``
   Cluster partition or queue to submit jobs to.


Example
----

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
