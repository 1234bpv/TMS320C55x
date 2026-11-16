void test_endian(unsigned long val, unsigned short *w) {
    w[0] = (unsigned short)val;
    w[1] = (unsigned short)(val >> 16);
}
unsigned long read_dbl(unsigned long *p) {
    return *p;
}
void write_dbl(unsigned long *p, unsigned long val) {
    *p = val;
}
