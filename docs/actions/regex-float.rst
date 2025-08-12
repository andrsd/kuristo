checks/regex-float
==================

The ``regex-float`` action extracts floating-point numbers from a file using a regular expression, then compares them to reference values with specified tolerances.

This is useful when validating log files that report numerical results such as errors, residuals, or timing metrics.

Example Usage
-------------

.. code-block:: yaml

   steps:
     - name: Run test
       id: result
       run: |
         echo Value: 1.23456789
     - name: Check ok
       uses: checks/regex-float
       with:
         input: ${{ steps.result.output }}
         pattern: "Value: ([0-9\\.]+)"
         gold: 1.23456789
         rel-tol: 1e-5


Arguments
---------

``input`` (string, required)
   Input that will be checked.

``pattern`` (string, required)
   Regular expression with **one capture group** for the float value.

``gold`` (float or list of floats, required)
   Reference value(s) to compare against.

``abs-tol`` (float, optional)
   | Maximum absolute difference allowed.
   | Default is ``0.0``.

``rel-tol`` (float, optional)
   | Maximum relative difference allowed.
   | Default is ``1e-8``.


.. admonition:: Notes

   - Only the **first capture group** in the regex is used; the pattern must match the number format fully.
   - Use raw strings or escape characters properly (e.g., ``[0-9\\.]+`` in YAML).
   - Use ``{:float:}`` alias to capture floating point numbers. This will use the correct regular expression under the hood.
     Do not use the group ``(...)`` operator, it is included in the alias for convenience.


.. seealso::

   - :doc:`regex`
   - :doc:`csv-diff`
