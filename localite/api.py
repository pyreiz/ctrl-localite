"""
Localite Flow
-------------

.. automodule:: localite.flow.mitm
   :members: start, kill

Controlling the Coil
--------------------

Before you can control the coil and read its parameters, make sure the localite-flow is running, e.g. with :meth:`~localite.flow.mitm.start` or the command-line-interface.


.. automodule:: localite.coil
   :members: Coil


"""

from localite.flow.mitm import start, kill
from localite.coil import Coil

