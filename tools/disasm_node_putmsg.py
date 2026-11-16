from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from extract_doff_section import Doff

b = Doff(ROOT / "work/evidence/e90/baseimage.dof")
addr_base, code = b.text("EXTERNAL_common_code")

def disasm_func(name, addr, length=200):
    off = addr - addr_base
    data = code[off : off + length]
    lines = [' .sect ".text"', f' .def {name}', f'{name}:']
    for byte in data:
        lines.append(f" .byte 0{byte:02x}h")
    asm_path = ROOT / f"out/scratch_{name}.s55"
    asm_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    cgt = Path("C:/Program Files (x86)/Texas Instruments/C5500 Code Generation Tools 4.4.1/bin")
    subprocess.run([str(cgt / "asm55.exe"), str(asm_path), "-o", f"out/scratch_{name}.obj"], check=True)
    res = subprocess.run([str(cgt / "dis55.exe"), "-qq", "-e", f"out/scratch_{name}.obj"], capture_output=True, text=True, check=True)
    print(f"=== {name} (0x{addr:x}) ===")
    print(res.stdout)

disasm_func("NODE_putMsg", 0x24dd5c, 240)
