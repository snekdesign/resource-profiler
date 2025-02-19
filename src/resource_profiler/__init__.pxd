# cython: language_level=3

cdef extern void tauri_open(const char *url) noexcept nogil
