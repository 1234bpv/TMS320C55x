"""Small bounded client for the existing phone daemon; never scans another IP."""
import argparse
import hashlib
import pathlib
import socket
import time


class Device:
    def __init__(self, ip, device, timeout=8, connect_timeout=3):
        self.socket = socket.create_connection((ip, 2323), timeout=connect_timeout)
        self.socket.settimeout(timeout)
        self.timeout = timeout
        self.reader = self.socket.makefile("rb")
        try:
            info = self.cmd("INFO")
        except Exception:
            self.close()
            raise
        expected = "screen " + {"n95": "320x240", "e90": "800x352"}[device]
        if not any(x.startswith(expected) for x in info):
            self.close()
            raise RuntimeError(f"identity check failed for {device}: {info}")

    def close(self):
        self.reader.close()
        self.socket.close()

    def line(self):
        value = self.reader.readline(65537)
        if not value.endswith(b"\n") or len(value) > 65536:
            raise RuntimeError("missing or oversized daemon response")
        return value.rstrip(b"\r\n").decode("ascii", "replace")

    def send(self, command):
        if "\n" in command or "\r" in command:
            raise ValueError("a command must be one line")
        print("> " + command, flush=True)
        self.socket.sendall(command.encode("ascii") + b"\n")

    def cmd(self, command, allow_error=False):
        self.send(command)
        deadline = time.monotonic() + self.timeout
        lines = [self.line()]
        if command.split()[0].upper() in ("LS", "PS", "WG", "INFO", "TOP", "AP") and lines[0].startswith("OK"):
            while True:
                left = deadline - time.monotonic()
                if left <= 0 or len(lines) >= 4096:
                    raise TimeoutError("daemon response exceeded its limit")
                self.socket.settimeout(left)
                line = self.line()
                if line == "END":
                    break
                lines.append(line)
        self.socket.settimeout(self.timeout)
        for line in lines:
            print("< " + line, flush=True)
        if lines[0].startswith("ERR") and not allow_error:
            raise RuntimeError(lines[0])
        return lines

    def get(self, remote, local):
        self.send("GET " + remote)
        response = self.line()
        if not response.startswith("OK "):
            raise RuntimeError(response)
        remaining = int(response.split()[1])
        if remaining < 0 or remaining > 32 * 1024 * 1024:
            raise RuntimeError("unexpected GET size")
        local = pathlib.Path(local)
        local.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + 30
        with local.open("wb") as output:
            while remaining:
                left = deadline - time.monotonic()
                if left <= 0:
                    raise TimeoutError("GET exceeded 30 seconds")
                self.socket.settimeout(min(left, self.timeout))
                data = self.reader.read(min(remaining, 8192))
                if not data:
                    raise RuntimeError("incomplete GET")
                output.write(data)
                remaining -= len(data)
        self.socket.settimeout(self.timeout)
        print("< " + response + " -> " + str(local), flush=True)

    def put(self, remote, data):
        self.send(f"PUT {remote} {len(data)}")
        self.socket.sendall(data)
        response = self.line()
        print("< " + response, flush=True)
        if response != f"OK {len(data)}":
            raise RuntimeError(response)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ip", required=True)
    p.add_argument("--device", choices=("n95", "e90"), required=True)
    p.add_argument("--cmd", action="append", default=[])
    p.add_argument("--get", nargs=2, metavar=("REMOTE", "LOCAL"))
    p.add_argument("--put", nargs=2, metavar=("LOCAL", "REMOTE"))
    p.add_argument("--hash-remote")
    p.add_argument("--timeout", type=int, default=8, help="response deadline in seconds (3..185)")
    p.add_argument("--require-exit-zero", action="store_true")
    a = p.parse_args()
    if not 3 <= a.timeout <= 185:
        p.error("timeout must be 3..185 seconds")
    if a.require_exit_zero and len(a.cmd) != 1:
        p.error("require-exit-zero needs exactly one EXEC or completed WAIT command")
    d = Device(a.ip, a.device, timeout=a.timeout)
    try:
        process_error = None
        if a.put:
            data = pathlib.Path(a.put[0]).read_bytes()
            d.put(a.put[1], data)
            if a.hash_remote:
                d.put(a.hash_remote, hashlib.sha1(data).digest())
        for command in a.cmd:
            response = d.cmd(command)
            if a.require_exit_zero and response != ["EXIT 0 Kill"]:
                process_error = "process did not exit successfully: " + str(response)
        if a.get:
            d.get(*a.get)
        if process_error:
            raise RuntimeError(process_error)
    finally:
        d.close()


if __name__ == "__main__":
    main()
