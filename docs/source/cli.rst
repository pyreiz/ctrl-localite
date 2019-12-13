Command Line Interface
----------------------

Use ``localite-flow`` to interface with a real localite TMS Navigator.


.. code-block:: none

    usage: localite-flow [-h] [--host HOST] [--kill]

    optional arguments:
    -h, --help   show this help message and exit
    --host HOST  The IP-Adress of the localite-PC
    --kill


Use ``localite-mock`` if you don't have access to a real TMS Navigator, but want to develop and tests tasks or experiments using the API.

.. code-block:: none

    usage: localite-mock [-h] [--kill]

    optional arguments:
    -h, --help  show this help message and exit
    --kill

