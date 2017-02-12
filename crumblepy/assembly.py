class Assembly:
    def __init__(self):
        self.bytecode = []
        self.labels = {}
        self.assembly = []

    def label_address(self, name):
        if name in self.labels:
            return self.labels[name]
        return 0

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__') and name not in ['label_address', 'append']:
            def wrapper(*args):
                self.assembly.append(name.upper() + ("" if len(args) == 0 else " " + " ".join(map(str, args))))
                return attr(*args)
            return wrapper
        return attr

    def label(self, name):
        self.labels[name] = len(self.bytecode)

    def append(self, code):
        self.bytecode.append(code)

    def push(self, num):
        self.append(0x0000 + (int(num) & 0xFF))

    def pushf(self, num):
        self.append(0x0100 + (int(num) & 0xFF))

    def pushl(self, num):
        self.append(0x0200 + (int(num) & 0xFF))
        self.append((int(num) & 0xFF00) >> 8)

    def pop(self, num):
        self.append(0x0300 + (int(num) & 0xFF))

    def popf(self, num):
        self.append(0x0400 + (int(num) & 0xFF))

    def poprm(self):
        self.append(0x0500)

    def dup(self):
        self.append(0x0600)

    def add(self):
        self.append(0x0800)

    def sub(self):
        self.append(0x0900)

    def mul(self):
        self.append(0x0A00)

    def div(self):
        self.append(0x0B00)

    def rnd(self):
        self.append(0x0C00)

    def gte(self):
        self.append(0x1000)

    def gt(self):
        self.append(0x1100)

    def lte(self):
        self.append(0x1200)

    def lt(self):
        self.append(0x1300)

    def eq(self):
        self.append(0x1400)

    # Jump to label unconditionally
    def bra(self, label):
        self.append(0x1800 + (self.label_address(label) & 0xFF))
        self.append((self.label_address(label) & 0xFF00) >> 8)

    # Jump to label if top of stack is not 1
    def bez(self, label):
        self.append(0x1900 + (self.label_address(label) & 0xFF))
        self.append((self.label_address(label) & 0xFF00) >> 8)

    def bnz(self, label):
        self.append(0x1A00 + (self.label_address(label) & 0xFF))
        self.append((self.label_address(label) & 0xFF00) >> 8)

    def and_op(self):
        self.append(0x2000)

    def eor_op(self):
        self.append(0x2100)

    def not_op(self):
        self.append(0x2200)

    def or_op(self):
        self.append(0x2300)

    def drd(self):
        self.append(0x2800)

    def dwr(self):
        self.append(0x2900)

    def ard(self):
        self.append(0x2A00)

    def mot1(self):
        self.append(0x3000)

    def mot2(self):
        self.append(0x3100)

    def ssprk(self):
        self.append(0x3200)

    def osprk(self):
        self.append(0x3300)

    def wait(self):
        self.append(0x3400)

    def srv(self):
        self.append(0x3600)

    def usons(self):
        self.append(0x3700)

    def usonl(self):
        self.append(0x3800)

    def stop(self):
        self.append(0x3FFF)
