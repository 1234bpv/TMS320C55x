import sys, re, glob, os

# DCD strings in DOFF C55x files are stored one ASCII char per 16-bit big-endian
# word: 00 XX. Pull every run of >=8 such words and print it.
pat = re.compile(rb'(?:\x00[\x20-\x7e]){12,}')

for path in sys.argv[1:]:
    data = open(path, 'rb').read()
    hits = []
    for m in pat.finditer(data):
        s = m.group()[1::2].decode('ascii')
        hits.append((m.start(), s))
    if not hits:
        continue
    print('=' * 70)
    print(os.path.basename(path), len(data))
    for off, s in hits:
        if ',' in s or ':' in s:
            print('  %06x  %s' % (off, s))
