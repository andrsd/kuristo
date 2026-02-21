checks/h5diff
=============

The ``h5diff`` action compares HDF5 files (`.h5`) to verify that simulation results
match a known reference. You can compare entire files or specific datasets within files.


Example Usage - Compare Entire Files
-------------------------------------

.. code-block:: yaml

   steps:
     - uses: checks/h5diff
       with:
         gold: ref.h5
         test: result.h5
         rel-tol: 1e-6


Example Usage - Compare Multiple Datasets
------------------------------------------

Compare specific datasets within the HDF5 files, each with its own tolerance:

.. code-block:: yaml

   steps:
     - uses: checks/h5diff
       with:
         gold: ref.h5
         test: result.h5
         datasets:
           - path: /pressure
             rel-tol: 1e-6
           - path: /velocity
             abs-tol: 0.001
           - path: /temperature
             rel-tol: 1e-5


Arguments - File Comparison
---------------------------

``gold`` (string, required)
   Path to the reference HDF5 file.

``test`` (string, required)
   Path to the output HDF5 file to compare.

``abs-tol`` (float, optional)
   Absolute difference threshold. Used when comparing entire files.

``rel-tol`` (float, optional)
   Relative difference threshold. Used when comparing entire files.


Arguments - Dataset Comparison
------------------------------

``gold`` (string, required)
   Path to the reference HDF5 file.

``test`` (string, required)
   Path to the output HDF5 file to compare.

``datasets`` (list, optional)
   List of datasets to compare. Each dataset is a dictionary with:

   - ``path`` (string, required): Path to the dataset (e.g., ``/pressure``, ``/data/velocity``)
   - ``rel-tol`` (float, optional): Relative tolerance for this dataset
   - ``abs-tol`` (float, optional): Absolute tolerance for this dataset

   Either ``rel-tol`` or ``abs-tol`` must be provided for each dataset.


Optional Arguments
------------------

``fail-on-diff`` (boolean, optional, default: true)
   If ``false``, differences found by h5diff will not cause the step to fail.
   Useful for development and debugging.


.. admonition:: Notes

   - Either ``abs-tol`` or ``rel-tol`` must be provided (for entire file comparison) or for each dataset
   - Uses ``h5diff`` from HDF5 distribution. Make sure it is on your PATH when running kuristo.
   - When comparing multiple datasets, the step fails if any dataset comparison fails (unless ``fail-on-diff`` is false)


.. seealso::

   - :doc:`exodiff`
   - :doc:`csv-diff`
