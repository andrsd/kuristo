Reference
=========

Workflow files use YAML syntax.
If you are new to YAML, you can `Learn YAML in Y minutes <https://learnxinyminutes.com/yaml/>`_.

jobs
----

Workflow is made up of jobs, which run in parallel by default.

jobs.<id>
---------

This is the job ID and must be unique within the workflow file.

jobs.<id>.name
--------------

Job name which will be displayed in the user interface.

jobs.<id>.description
---------------------

Job description.

jobs.<id>.needs
---------------

Job dependecies.
These are job IDs that must finish before this job starts.

jobs.<id>.skip
--------------

If set, the job will be skipped.
It is recommended to describe the reason why the job is skipped.

jobs.<id>.timeout-minutes
-------------------------

| Maximum time for the job to finish, in minutes.
| Default value is ``60``.

jobs.<id>.strategy
------------------

TODO

jobs.<id>.strategy.matrix
-------------------------

TODO

jobs.<id>.strategy.matrix.include
---------------------------------

TODO

jobs.<id>.steps
---------------

Steps that made up the job

jobs.<id>.steps[*].id
---------------------

Step ID.

jobs.<id>.steps[*].name
-----------------------

Step name.
This is displayed in user interface.

jobs.<id>.steps[*].num-cores
----------------------------

Number of cores to use.

jobs.<id>.steps[*].continue-on-error
------------------------------------

| Indicates if the workflow execution should continue if this step fails.
| Default value is ``False``

jobs.<id>.steps[*].description
------------------------------

Step description.

jobs.<id>.steps[*].uses
-----------------------

Action name that is used for this step.

jobs.<id>.steps[*].with
-----------------------

Parameters passed into the action.

jobs.<id>.steps[*].run
----------------------

Shell commands to execute.

jobs.<id>.steps[*].shell
------------------------

| Shell to use.
| Default value is ``sh``.

jobs.<id>.steps[*].working-directory
------------------------------------

Working directory for the step.

jobs.<id>.steps[*].timeout-minutes
----------------------------------

| Maximum time for the step to finish, in minutes.
| Default value is ``60``.
