import re,sys,struct
from paths import ROM as Z
for mod in sys.argv[1:]:
    b=open(Z+mod,'rb').read()
    ca=struct.unpack_from('<I',b,20)[0]; HDR=120
    print('#### %s codeAddr=0x%08X size=%d' % (mod,ca,len(b)))
    for m in re.finditer(rb'[\x20-\x7e]{5,}', b[HDR:]):
        print('  %08x  %s' % (ca+m.start(), m.group().decode()))
    for m in re.finditer(rb'(?:[\x20-\x7e]\x00){4,}', b[HDR:]):
        print('  %08x  W16: %s' % (ca+m.start(), m.group()[::2].decode()))
