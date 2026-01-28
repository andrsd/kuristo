checks/convergence-rate
=======================

The ``convergence-rate`` action verifies the observed rate of convergence of a dataset.
It is most commonly used to check mesh convergence behavior by fitting error data against a measure of resolution (for example, the number of degrees of freedom).

Both single-component and multi-component datasets are supported.

Example Usage
-------------

.. code-block:: yaml

   steps:
     - uses: checks/convergence-rate
       with:
          input: some/file.h5
          x-axis: "/dataset-name-for-x"
          y-axis: "/dataset-name-for-y"
          expected-order: 2.
          abs-tol: 1e-3


Arguments
---------

``input`` (string, required)
   Path to the HDF5 file containing the datasets to be checked.

``x-axis`` (string, required)
   Name of the dataset containing the x-axis values (e.g. degrees of freedom).


``y-axis`` (string, required)
   Name of the dataset containing the y-axis values (typically error norms).

``expected-order`` (float, required)
   | Expected order of convergence for each component.
   | If a single value is specified, it is applied to all components.

``abs-tol`` (float, required)
   | Allowed absolute deviation from the expected order, evaluated per component.
   | If a single value is specified, it is applied to all components.


.. admonition:: Notes

   - The dataset specified by ``x-axis`` must contain ``N`` values.
   - The dataset specified by ``y-axis`` must contain either:

     - ``N`` values (single-component data), or
     - ``c × N`` values for multi-component data, where each row corresponds to one component.


.. seealso::

   - :doc:`h5diff`
