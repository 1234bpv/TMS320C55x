from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from extract_doff_section import Doff

b = Doff(ROOT / "work/evidence/e90/baseimage.dof")
sec = b.sections["EXTERNAL_common_code"]
off = 0x24E6F0 - sec[1]
data = b.data[sec[6] + off : sec[6] + off + 200]

lines = [' .sect ".text"', ' .def _test', '_test:']
for byte in data:
    lines.append(f" .byte 0{byte:02x}h")

asm_path = ROOT / "out/scratch_wrapper.s55"
asm_path.write_text("\n".join(lines) + "\n", encoding="ascii")
cgt = Path("C:/Program Files (x86)/Texas Instruments/C5500 Code Generation Tools 4.4.1/bin")
subprocess.run([str(cgt / "asm55.exe"), str(asm_path), "-o", str(ROOT / "out/scratch_wrapper.obj")], check=True)
res = subprocess.run([str(cgt / "dis55.exe"), "-qq", "-e", str(ROOT / "out/scratch_wrapper.obj")], capture_output=True, text=True, check=True)
print(res.stdout)
