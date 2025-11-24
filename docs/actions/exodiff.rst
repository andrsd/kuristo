checks/exodiff
==============

The ``exodiff`` action compares two Exodus files (`.exo`) to verify that simulation results match a known reference.

It is typically used to perform regression tests on output files produced by finite element solvers that write Exodus format.


Example Usage
-------------

.. code-block:: yaml

   steps:
     - uses: checks/exodiff
       with:
         gold: ref.exo
         test: result.exo
         abs-tol: 1e-8
         rel-tol: 1e-6


Arguments
---------

``gold`` (string, required)
   Path to the reference Exodus file.

``test`` (string, required)
   Path to the simulation output file to compare.

``abs-tol`` (float, optional)
   Absolute difference threshold.

``rel-tol`` (float, optional)
   Relative difference threshold.



.. admonition:: Notes

   - This action assumes the input files use compatible mesh topologies and metadata.
   - Uses ``exodiff`` from SEACAS. Make sure it is on your PATH when running kuristo.


.. seealso::

   - :doc:`csv-diff`
   - :doc:`h5diff`
