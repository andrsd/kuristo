User Interface
==============

``-f|--config <file>``
   Supply a config file.

``--no-ansi``
   Use plain terminal output, i.e. no colors, etc.

run
---

Run workflow(s).

``<file>``
   Run a specific workflow

``<location> [<location>]``
   Find all workflow files and run them.

``--verbose=<num>``
   Control verbosity.

   Verbosity levels:

   - `0`: silent
   - `1`: errors only
   - `2`: default
   - `3`: detailed output for each step

list
----

``<location>``
   Find tests in the location that would be executed.

status
------

Display status of a run.
By default, it will show the latest run status.

``--run-id <id>``
   Show status of a particular run

``--failed``
   Show only failed jobs.

``--skipped``
   Show only skipped jobs.

``--passed``
   Show only successful jobs.

log
---

List runs


show
----

Show the output (log) of a specified job.

``--job``
   Job ID to display information about.

``--run-id``
   Run ID. If not specified, the latest run is assumed.

batch
-----

Interact with a batch system

``submit``
   Submit workflows into a batch system.

   ``--backend``
      Secify the backend. Possible value ``slurm``.

   ``--partition``
      Partition name to submit into.

   ``<location>``
      Location to search for tests.

   ``<file>``
      File to submit into a queue.

``status``
   Show status of jobs submited into a batch system.


doctor
------

Show diagnostic report about your environment.
This outputs detailed information including:

- Kuristo version and Python interpreter
- Platform and CPU configuration
- Log and config file locations
- MPI launcher
- Active plugins, registered actions
- Logging and cleanup policies


report
------

Generate a report for a given run.

``--run-id``
   Run ID. If not specified, the latest run is assumed.

``<format>:<file>``
   File to save the report into with given ``format``.

   Supportted formats:

   - `xml` - junit XML file format
