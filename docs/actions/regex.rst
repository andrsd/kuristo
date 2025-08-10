checks/regex
============

The ``regex`` action checks whether a specific regular expression appears in its input.
It is typically used to validate log or text output (e.g., looking for convergence messages, warnings, or specific patterns).


Example Usage
-------------

.. code-block:: yaml

   steps:
     - name: Produce output
       id: sim
       run: |
         echo This is some text
         echo Simulation completed successfully

     - uses: checks/regex
       with:
         input: ${{ steps.sim.output }}
         pattern: "Simulation completed successfully"


Arguments
---------

``input`` (string, required)
   Input that will be checked

``pattern`` (string, required)
   The regular expression to match (interpreted using Python’s `re` module).



.. admonition:: Notes

   - This action uses **exact string matching** (not float-aware); use :doc:`regex-float` for numerical comparisons.
   - Useful for checking message logs, printed summaries, or warnings.


.. seealso::

   - :doc:`regex-float`
   - :doc:`csv-diff`
