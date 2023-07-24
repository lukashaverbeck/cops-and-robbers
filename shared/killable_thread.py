from __future__ import annotations

from ctypes import c_ulong, py_object, pythonapi
from threading import Thread
from typing import Any


class KillableThread(Thread):
    """Subclass of 'Thread' that allows termination."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__res = None
        self.__err = None

    def run(self) -> None:
        """Overrides 'Thread.run'.

        Stores result or exceptions to later pass them back to the caller.
        """
        try:
            if self._target:
                self.__res = self._target(*self._args, **self._kwargs)
        except SystemExit:
            return
        except BaseException as err:
            self.__err = err
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def join(self, timeout: float = None) -> Any:
        """Overrides 'Thread.join'.

        Calls the super join method. If the thread is not joined within the
        timeout limit raise a TimeoutError.
        If an exception has been raised, re-raise it as RuntimeError.
        Otherwise, if the target succeeded, return the result.

        :param timeout: The maximum time to wait for the thread result,
        defaults to None, which means no set time limit
        :raises TimeoutError: The exception describing the occurred timeout.
        :raises RuntimeError: The exception describing the inner exception,
        that occurred in the target.
        :return: The result of the target, in case it succeeded.
        """
        super().join(timeout)
        if self.is_alive():
            raise TimeoutError('The thread join timeout has been exceeded.')
        if self.__err:
            raise RuntimeError('The thread target raised an exception.') \
                from self.__err
        return self.__res

    def terminate(self):
        """Terminates the thread.

        Utilizes low-level libraries to inject a 'SystemExit' exception
        asynchronously into the running thread. This exception is then raised
        the next time the thread would perform any operation, causing it to
        terminate silently.
        """
        # PyThreadState_SetAsyncExc requires the global interpreter lock.
        gil_handle = pythonapi.PyGILState_Ensure()

        tid = c_ulong(self.ident)
        exit_exception = py_object(SystemExit)

        affected_threads = pythonapi.PyThreadState_SetAsyncExc(tid, exit_exception)

        # If 'affected_threads' is anything besides '0' (thread did already stop)
        # or '1' (successfully injected the exception), the call failed.
        # Revert the exception injection to avoid instabilities.
        if affected_threads > 1:
            pythonapi.PyThreadState_SetAsyncExc(tid, None)

        # Release the global interpreter lock.
        pythonapi.PyGILState_Release(gil_handle)
