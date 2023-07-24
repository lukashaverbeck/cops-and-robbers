from __future__ import annotations

from logging import getLogger
from multiprocessing import active_children

logger = getLogger('resource_manager')

unkillable_processes = []


def dispose_unmanaged_resources() -> None:
    """Disposes unmanaged resources.

    This method is called after the initialization and every step of the
    players, whether it was successful or not.

    Since player classes are largely unregulated in what they are allowed
    to do, they can leave behind unmanaged resources that are not properly
    cleaned up. This method targets those resources for disposal. If other
    types of leftover resources are discovered in the future, they should
    be dealt with through this method.
    """
    # Terminates any potentially detached child processes that players may
    # not have properly closed themselves.
    for orphan in active_children():
        orphan.kill()

        # If an orphan does not respond to the kill signal, it most likely
        # became a zombie which should automatically terminate once joined.
        if orphan.is_alive():
            orphan.join(.1)

            # If the orphan is somehow still alive, log a critical warning.
            if orphan.is_alive() and orphan.pid not in unkillable_processes:
                unkillable_processes.append(orphan.pid)
                logger.critical("An unkillable child process remains (PID: %s).",
                                orphan.pid)
