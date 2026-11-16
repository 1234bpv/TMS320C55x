"""Keep one verified daemon connection active while observing installer steps.

Read JSON objects from stdin: {"cmd":"..."}, {"get":["remote","local"]},
{"put":["local","remote"]}, or {"close":true}. All daemon I/O is serial.
An INFO heartbeat runs between commands; no reconnect or device discovery.
This does not recover an unresponsive phone or make a DSP call safe.
"""
import argparse
import contextlib
import datetime
import json
import pathlib
import queue
import sys
import threading
import time

from strict_net import Device


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--device", choices=("n95", "e90"), required=True)
    parser.add_argument("--log", type=pathlib.Path, required=True)
    parser.add_argument("--duration", type=int, default=300)
    args = parser.parse_args()
    if not 30 <= args.duration <= 600:
        parser.error("duration must be 30..600 seconds")
    args.log.parent.mkdir(parents=True, exist_ok=True)
    pending = queue.Queue()

    def receive():
        for line in sys.stdin:
            pending.put(line)
        pending.put(None)

    with args.log.open("x", encoding="utf-8", buffering=1) as log:
        def stamp(message):
            log.write(datetime.datetime.now(datetime.timezone.utc).isoformat()
                      + " " + message + "\n")

        stamp("CONNECT " + args.device + " " + args.ip)
        with contextlib.redirect_stdout(log):
            device = Device(args.ip, args.device, timeout=30)
        threading.Thread(target=receive, daemon=True).start()
        deadline = time.monotonic() + args.duration
        heartbeat = time.monotonic() + 2
        no_command = object()
        print("READY " + args.device, flush=True)
        try:
            while time.monotonic() < deadline:
                try:
                    line = pending.get(timeout=max(0, min(heartbeat, deadline) - time.monotonic()))
                except queue.Empty:
                    line = no_command
                if line is no_command:
                    if time.monotonic() >= deadline:
                        break
                    stamp("HEARTBEAT")
                    with contextlib.redirect_stdout(log):
                        device.cmd("INFO")
                    heartbeat = time.monotonic() + 2
                    continue
                if line is None:
                    break
                request = json.loads(line)
                if not isinstance(request, dict) or len(request) != 1:
                    raise ValueError("one operation required per JSON object")
                operation, value = next(iter(request.items()))
                stamp("OP " + json.dumps(request, ensure_ascii=True))
                if operation == "close" and value is True:
                    break
                with contextlib.redirect_stdout(log):
                    if operation == "cmd" and isinstance(value, str):
                        result = device.cmd(value)
                    elif operation in ("get", "put") and isinstance(value, list) and len(value) == 2 and all(isinstance(x, str) for x in value):
                        if operation == "get":
                            if pathlib.Path(value[1]).exists():
                                raise FileExistsError("evidence destination already exists")
                            device.get(value[0], value[1])
                        else:
                            device.put(value[1], pathlib.Path(value[0]).read_bytes())
                        result = ["OK " + operation]
                    else:
                        raise ValueError("unsupported operation")
                print(json.dumps(result), flush=True)
                heartbeat = time.monotonic() + 2
        except Exception as exc:
            stamp("FAILED " + type(exc).__name__ + ": " + str(exc))
            raise
        finally:
            device.close()
            stamp("CLOSED")


if __name__ == "__main__":
    main()
