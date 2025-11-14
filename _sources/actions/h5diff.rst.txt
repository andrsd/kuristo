checks/h5diff
=============

The ``h5diff`` action compares two HDF5 files (`.h5`) to verify that simulation results
match a known reference.


Example Usage
-------------

.. code-block:: yaml

   steps:
     - uses: checks/h5diff
       with:
         gold: ref.h5
         test: result.h5
         rel-tol: 1e-6


Arguments
---------

``gold`` (string, required)
   Path to the reference HDF5 file.

``test`` (string, required)
   Path to the output HDF5 file to compare.

``abs-tol`` (float, optional)
   Absolute difference threshold.

``rel-tol`` (float, optional)
   Relative difference threshold.



.. admonition:: Notes

   - Either ``abs-tol`` or ``rel-tol`` must be provided
   - Uses ``h5diff`` from HDF5 distribution. Make sure it is on your PATH when running kuristo.


.. seealso::

   - :doc:`exodiff`
   - :doc:`csv-diff`
