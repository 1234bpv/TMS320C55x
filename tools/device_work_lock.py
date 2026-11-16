"""OS-owned nonblocking per-phone lock; nested actions in one runner are allowed."""
import contextlib
import msvcrt
import threading

_held={}


@contextlib.contextmanager
def device_lock(path):
    key=str(path.resolve()); owner=threading.get_ident()
    if key in _held:
        if _held[key]!=owner: raise RuntimeError("another thread owns device work: "+key)
        yield
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a+b") as stream:
        if stream.seek(0,2)==0: stream.write(b"0"); stream.flush()
        stream.seek(0)
        try: msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as exc: raise RuntimeError("device work already running; no connection attempted: "+key) from exc
        _held[key]=owner
        try: yield
        finally:
            del _held[key]; stream.seek(0); msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
