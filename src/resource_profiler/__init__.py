__all__ = ('Popen', 'run')

import contextlib
import subprocess
import types
from typing import Any
from typing import TYPE_CHECKING
import webbrowser

from bokeh.settings import settings
import cython  # pyright: ignore[reportMissingTypeStubs]
import dask.diagnostics.profile
from typing_extensions import override

if cython.compiled:  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    assert not TYPE_CHECKING
else:
    def tauri_open(_url: bytes) -> None: ...


@contextlib.contextmanager
def Popen(*args: Any, **kwargs: Any):
    class ResourceProfiler(dask.diagnostics.profile.ResourceProfiler):
        def _start_collect(self):
            if not self._is_running():
                self._tracker = dask.diagnostics.profile._Tracker(self._dt)  # pyright: ignore[reportPrivateUsage]
                self._tracker.parent_pid = proc.pid
                self._tracker.start()
            self._tracker.parent_conn.send('collect')

    old = settings.browser._user_value  # pyright: ignore[reportPrivateUsage]
    if cython.compiled:  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        settings.browser = 'resource-profiler'
    with contextlib.ExitStack() as stack:
        stack.callback(lambda: settings.browser.set_value(old))  # pyright: ignore[reportArgumentType]
        stack.callback(lambda: prof.results and prof.visualize(  # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType]
            save=False,
            sizing_mode='stretch_both',
        ))
        prof = stack.push(ResourceProfiler())
        proc = stack.enter_context(subprocess.Popen(*args, **kwargs))
        prof.__enter__()
        yield proc


run = types.FunctionType(
    subprocess.run.__code__,
    dict(subprocess.run.__globals__, Popen=Popen),
    subprocess.run.__name__,
    subprocess.run.__defaults__,
    subprocess.run.__closure__,
    subprocess.run.__kwdefaults__,
)


if cython.compiled:  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    class _Tauri(webbrowser.BaseBrowser):
        @override
        def open(self, url: str, new: int = 0, autoraise: bool = True):
            tauri_open(url.encode('ascii'))
            return True


    webbrowser.register('resource-profiler', _Tauri)
