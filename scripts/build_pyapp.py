import contextlib
import itertools
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import urllib.error
import urllib.request


def main(
    PIXI_PROJECT_NAME: str,
    PIXI_PROJECT_VERSION: str,
    PIXI_PROJECT_ROOT: str,
    **env: str,
):
    os.makedirs('bin', exist_ok=True)
    suffix = '.exe' if sys.platform == 'win32' else ''
    dst = f'bin/{PIXI_PROJECT_NAME}{suffix}'
    try:
        os.unlink(dst)
    except FileNotFoundError:
        pass
    table = bytes.maketrans(b' -.', b'___')
    name = PIXI_PROJECT_NAME.translate(table)
    platform_ = sysconfig.get_platform().translate(table)
    env.update(
        PYAPP_PROJECT_NAME=PIXI_PROJECT_NAME,
        PYAPP_PROJECT_PATH=os.path.join(
            PIXI_PROJECT_ROOT,
            f'dist/{name}-{PIXI_PROJECT_VERSION}-cp39-abi3-{platform_}.whl',
        ),
        PYAPP_PROJECT_FEATURES='cli',
        PYAPP_FULL_ISOLATION='1',
        PYAPP_UV_ENABLED='1',
        PYAPP_UV_SOURCE='https://mirrors.cernet.edu.cn/pypi/packages/fd/ce/7002f0ca79f440f31c2cc393fcb94109b1d48c714d5ff63bbfedd92b3b50/uv-0.6.1-py3-none-win_amd64.whl',
        PYAPP_PIP_EXTRA_ARGS='-i https://mirrors.cernet.edu.cn/pypi/web/simple',
        PYAPP_SELF_COMMAND='none',
    )
    if sys.platform == 'win32':
        minor = 13
        micro = 2
        if sys.version_info[::3] == (3, 'final'):
            minor, micro = max((minor, micro), sys.version_info[1:3])
        for minor, micro in itertools.chain(
            itertools.product([minor], range(min(micro, 13), -1, -1)),
            itertools.product(range(minor-1, 8, -1), range(13, -1, -1)),
        ):
            ver = f'3.{minor}.{micro}'
            url = f'https://mirrors.cernet.edu.cn/python/{ver}/python-{ver}-embed-amd64.zip'
            req = urllib.request.Request(url, method='HEAD')
            with contextlib.ExitStack() as stack:
                try:
                    stack.enter_context(urllib.request.urlopen(req))
                except urllib.error.HTTPError as resp:
                    stack.enter_context(resp)
                else:
                    env.update(
                        PYAPP_EXEC_CODE='import runpy,site;'
                            'site.main();'
                            f"runpy.run_module('{name}',run_name='__main__')",
                        PYAPP_DISTRIBUTION_SOURCE=url,
                    )
                    break
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                'cargo', 'install',
                '--git', 'https://github.com/snekdesign/pyapp.git',
                '--locked',
                '--root', tmp,
            ],
            check=True,
            env=env,
        )
        shutil.move(
            os.path.join(tmp, f'bin/pyapp{suffix}'),
            dst,
        )


if __name__ == '__main__':
    main(**os.environ)
