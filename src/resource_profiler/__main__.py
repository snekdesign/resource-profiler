import contextlib
import io
import os
import pathlib
import subprocess
import sys
from typing import Any
from typing import cast
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import Union

import pydantic
import pydantic_settings
import rich_argparse

from . import run

_SpecialPath = Literal['-', 'nul', '/dev/null']


def main():
    pydantic_settings.CliApp.run(
        Popen,
        cli_args=sys.argv[1:] or ['--help'],
        cli_settings_source=pydantic_settings.CliSettingsSource(
            Popen,
            formatter_class=rich_argparse.RawDescriptionRichHelpFormatter,
        ),
    )


class Popen(pydantic_settings.BaseSettings):
    """Run a process, and show its resource usage after it exits.

    Check https://docs.python.org/3/library/subprocess.html for details.
    """

    args: pydantic_settings.CliPositionalArg[list[str]]
    executable: Optional[pydantic.FilePath] = None
    if TYPE_CHECKING:
        stdin: Union[_SpecialPath, Literal['/dev/stdin'], pydantic.FilePath]
        stdout: Union[_SpecialPath, Literal['/dev/stdout'], pydantic.NewPath]
        stderr: Union[
            _SpecialPath,
            Literal['/dev/stdout', '/dev/stderr'],
            pydantic.NewPath,
        ]
    else:
        stdin: Union[
            Literal['-', os.devnull, '/dev/stdin'],
            pydantic.FilePath,
        ] = '/dev/stdin'
        stdout: Union[
            Literal['-', os.devnull, '/dev/stdout'],
            pydantic.NewPath,
        ] = '/dev/stdout'
        stderr: Union[
            Literal['-', os.devnull, '/dev/stdout', '/dev/stderr'],
            pydantic.NewPath,
        ] = '/dev/stderr'
    shell: bool = False
    cwd: Optional[pydantic.DirectoryPath] = None
    env: Optional[dict[str, str]] = None
    if sys.platform == 'win32':
        creationflags: int = 0
    else:
        restore_signals: bool = True
        start_new_session: bool = False
        user: Optional[Union[int, str]] = None
        group: Optional[Union[int, str]] = None
        extra_groups: Optional[list[Union[int, str]]] = None
        umask: int = -1
        if sys.version_info >= (3, 11):
            process_group: Optional[int] = None

    model_config = pydantic_settings.SettingsConfigDict(
        nested_model_default_partial_update=True,
        case_sensitive=True,
        cli_hide_none_type=True,
        cli_avoid_json=True,
        cli_enforce_required=True,
        cli_implicit_flags=True,
        cli_kebab_case=True,
        cli_prog_name=__package__,
    )

    def cli_cmd(self):
        with contextlib.ExitStack() as stack:
            if isinstance(self.stdin, pathlib.Path):
                stdin = stack.enter_context(self.stdin.open('rb'))
            elif self.stdin == '/dev/stdin':
                stdin = None
            elif self.stdin == '-':
                stdin = sys.stdin.buffer
            else:
                stdin = subprocess.DEVNULL

            if isinstance(self.stdout, pathlib.Path):
                stdout = stack.enter_context(self.stdout.open('xb'))
            elif self.stdout == '/dev/stdout':
                stdout = None
            elif self.stdout == '-':
                stdout = sys.stdout.buffer
            else:
                stdout = subprocess.DEVNULL

            if isinstance(self.stderr, pathlib.Path):
                if (
                    isinstance(stdout, io.IOBase)
                    and _samefile(stdout.fileno(), self.stderr)
                ):
                    stderr = subprocess.STDOUT
                else:
                    stderr = stack.enter_context(self.stderr.open('xb'))
            elif self.stderr == '/dev/stdout':
                stderr = subprocess.STDOUT
            elif self.stderr == '/dev/stderr':
                stderr = None
            elif self.stderr == '-':
                stderr = sys.stderr.buffer
            else:
                stderr = subprocess.DEVNULL

            kwargs = _Kwargs()
            if sys.version_info >= (3, 11):
                kwargs['process_group'] = getattr(self, 'process_group', None)

            proc = run(
                self.args,
                executable=self.executable,
                stdin=stdin,
                stdout=cast(Any, stdout),
                stderr=stderr,
                shell=self.shell,
                cwd=self.cwd,
                env=self.env,
                creationflags=getattr(self, 'creationflags', 0),
                restore_signals=getattr(self, 'restore_signals', True),
                start_new_session=getattr(self, 'start_new_session', False),
                user=getattr(self, 'user', None),
                group=getattr(self, 'group', None),
                extra_groups=getattr(self, 'extra_groups', None),
                umask=getattr(self, 'umask', -1),
                **kwargs,
            )
        sys.exit(proc.returncode)


if sys.version_info >= (3, 11):
    class _Kwargs(TypedDict, total=False):
        process_group: Optional[int]
else:
    class _Kwargs(TypedDict, total=False):
        pass


def _samefile(f1: int, f2: pathlib.Path):
    try:
        return os.path.samefile(f1, f2)
    except Exception:
        return False


if __name__ == '__main__':
    main()
