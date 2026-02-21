User Interface
==============

Global Options
--------------

``--version``
   Show the version number and exit.

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

``--label <label>``
   Filter jobs by label. Can be specified multiple times to match jobs with any of the requested labels (OR logic).
   Only jobs with matching labels will be executed. Jobs without labels are skipped when a filter is active.
   If no jobs match the filter, the command exits successfully.

list
----

``<location>``
   Find tests in the location that would be executed.

``--label <label>``
   Filter jobs by label. Can be specified multiple times to match jobs with any of the requested labels (OR logic).
   Only jobs with matching labels will be displayed. Jobs without labels are skipped when a filter is active.

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

``--job <id>`` (required)
   Job ID to display information about.

``--run-id <id>``
   Run ID to display results for. If not specified, the latest run is assumed.

batch
-----

Interact with a batch system

``submit``
   Submit workflows into a batch system.

   ``--backend``
      Specify the backend. Possible value ``slurm``.

   ``--partition``
      Partition name to submit into.

   ``<location> [<location>]``
      Locations to search for workflow files. Multiple locations can be specified.

``status``
   Show status of jobs submitted into a batch system.

``run``
   Run a job in the batch system.

   ``<run_id>``
      ID of the run.

   ``<first_job_id>``
      First job ID to start from.

   ``<workflow_file>``
      Path to the workflow file to run.


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
