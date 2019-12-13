Application Programming Interface
---------------------------------

The main interface to controlling your TMS coil with localite-flow


Localite Flow
*************

.. automodule:: localite.flow.mitm
   :members: start, kill

Controlling the Coil
********************

Before you can control the coil and read its parameters, make sure the localite-flow is running, e.g. with :meth:`~localite.flow.mitm.start` or using the command-line-interface.


.. automodule:: localite.coil
   :members: Coil