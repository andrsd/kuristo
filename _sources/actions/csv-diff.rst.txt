checks/csv-diff
===============

The ``csv-diff`` action compares two CSV files and reports differences in numerical values.

It is typically used to validate simulation results against a reference file.


Example usage
-------------

.. code-block:: yaml

   steps:
     - uses: checks/csv-diff
       with:
         gold: ref.csv
         test: results.csv


Arguments
---------

``gold`` (string, required)
   Path to the reference CSV file.

``test`` (string, required)
   Path to the generated output file.

``abs-tol`` (float, optional)
   | Allowed absolute difference per value.
   | Default is ``1e-12``.

``rel-tol`` (float, optional)
   | Allowed relative difference per value.
   | Default is ``1e-6``.


.. seealso::

   - :doc:`exodiff`
   - :doc:`h5diff`
