# resource-profiler
`dask.diagnostics.ResourceProfiler` for subprocesses.
## Build-time dependencies
- msvc (Windows only)
- pixi
## Build
Choose a format in your favor:
```sh
pixi r build-wheel
pixi r build-conda
pixi r build-pyapp
```
## Usage
### Python API
The Python API is almost exactly the same as `subprocess.Popen` and
`subprocess.run`, except that `resource_profiler.Popen` must be used as a
context manager (via `with` or `contextlib.[Async]ExitStack`).  
The `__exit__` method of the context manager will block until the plot window is
closed.
### CLI
Run `resource-profiler --help` for help.
