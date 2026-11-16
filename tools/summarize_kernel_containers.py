"""Publish offline kernel container root audit and pointer derivation evidence."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from audit_kernel_containers import audit_e90, audit_n95
from paths import ROM

OUT = ROOT / "docs/evidence/2026-10-02"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    e90 = audit_e90(ROOT / "work/evidence/e90/rom")
    n95 = audit_n95(Path(ROM))
    report = {
        "scope": "Static ROM container root audit; ekern export 251 -> PDD factory -> Manager -> Board -> Context",
        "e90": e90,
        "n95": n95,
        "summary": {
            "e90_container_root": e90["container_root"]["root_address"],
            "e90_pdd_container_index": e90["container_root"]["pdd_container_type_index"],
            "e90_factory_vtable": e90["factory_identity"]["vtable"],
            "e90_manager_magic": e90["manager_identity"]["magic_word0"],
            "e90_manager_to_board_offset": e90["manager_identity"]["board_pointer_offset"],
            "e90_board_adjustment": e90["board_identity"]["adjustment_to_base"],
            "n95_container_root": n95["container_root"]["root_address"] if n95.get("available") else None,
            "n95_factory_vtable": n95.get("factory_vtable"),
        },
    }
    target = OUT / "kernel-containers-audit.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Published container root audit to {target.relative_to(ROOT).as_posix()}; E90={e90['container_root']['root_address']}, N95={n95.get('container_root', {}).get('root_address')}")


if __name__ == "__main__":
    main()
