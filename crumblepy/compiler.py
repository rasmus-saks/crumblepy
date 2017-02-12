from ast import *

from .assembly import Assembly

builtins = [
    "set_output",
    "get_digital",
    "get_analog",
    "set_sparkle",
    "set_all_sparkles",
    "wait",
    "random",
    "set_motor_1",
    "set_motor_2",
    "set_servo",
    "get_distance"
]


class CompileException(BaseException):
    def __init__(self, msg, node):
        super(CompileException, self).__init__("{0}:{1}".format(node.lineno - 1, node.col_offset), msg)


class Compiler:
    def __init__(self, output_format=None):
        self.output_format = output_format
        self.assembly = Assembly()
        self.labels = []
        self.label_count = 0
        self.vars = []

        # Loop break and continue
        self.start_label = None
        self.exit_label = None

    def new_label(self):
        label = "label_%d" % self.label_count
        self.label_count += 1
        self.labels.append(label)
        return label

    def declare_var(self, name):
        if name not in self.vars:
            self.vars.append(name)
            self.assembly.pushl(0)

    def assign(self, targets, value):
        # if len(targets) > 1:
        #     raise CompileException('Unsupported multiple assignment', targets[1])
        for i in range(len(targets)):
            target = targets[i]
            if type(target) != Name:
                raise CompileException('Values can only be assigned to variables', target)
            if target.id in ["A", "B", "C", "D"]:
                raise CompileException("A, B, C and D cannot be reassigned", target)
            self.declare_var(target.id)
            self.compile_expr(value)
            self.assembly.pop(self.vars.index(target.id))

    def compile(self, node):
        # First compile to determine label positions
        self.compile_stmt(node)
        self.assembly.stop()
        assembly = self.assembly.assembly[:]

        # Reset bytecode and compile again because now we know where the labels are
        self.assembly.bytecode = []
        self.label_count = 0
        self.compile_stmt(node)
        self.assembly.stop()
        if self.output_format in ["bytecode", "usb"]:
            return self.assembly.bytecode
        elif self.output_format == "assembly":
            return assembly

    def compile_stmt(self, node):
        if type(node) == Module:
            out = []
            for n in node.body:
                out.append(self.compile_stmt(n))
        elif type(node) == Expr:
            self.compile_expr(node.value)
        elif type(node) == If:
            self.if_stmt(node)
        elif type(node) == Assign:
            self.assign(node.targets, node.value)
        elif type(node) == While:
            self.while_stmt(node)
        elif type(node) == Pass:
            pass
        elif type(node) == Break:
            self.break_stmt(node)
        elif type(node) == Continue:
            self.continue_stmt(node)
        else:
            raise CompileException('Unsupported statement type %s.\n%s' % (str(type(node)), str(vars(node))), node)

    def compile_expr(self, node):
        if type(node) == Call:
            self.call(node)
        elif type(node) == Compare:
            self.compare(node.left, node.ops, node.comparators)
        elif type(node) == Num:
            self.assembly.pushl(node.n)
        elif type(node) == BinOp:
            self.bin_op(node.left, node.op, node.right)
        elif type(node) == Name:
            self.get_var(node)
        elif type(node) == NameConstant:
            self.constant(node)
        elif type(node) == UnaryOp:
            self.un_op(node.op, node.operand)
        elif type(node) == BoolOp:
            self.bool_op(node.op, node.values)
        else:
            raise CompileException('Unsupported expression type %s.\n%s' % (str(type(node)), str(vars(node))), node)

    def constant(self, node):
        if type(node.value) == bool:
            self.assembly.pushl(1 if node.value else 0)
        elif type(node.value) == int:
            self.assembly.pushl(node.value)
        else:
            raise CompileException('Unsupported constant type %s' % type(node.value), node)

    def while_stmt(self, node):
        self.start_label = self.new_label()
        self.exit_label = self.new_label()
        self.assembly.label(self.start_label)
        self.compile_expr(node.test)
        self.assembly.bez(self.exit_label)
        for n in node.body:
            self.compile_stmt(n)
        self.assembly.bra(self.start_label)
        self.assembly.label(self.exit_label)

    def get_var(self, node):
        if node.id in ["A", "B", "C", "D"]:
            self.assembly.pushl(["A", "B", "D", "C"].index(node.id))
            return
        if node.id not in self.vars:
            raise CompileException('Undefined variable %s' % node.id, node)
        self.assembly.push(self.vars.index(node.id))

    def bin_op(self, left, op, right):
        self.compile_expr(left)
        self.compile_expr(right)
        if type(op) == Add:
            self.assembly.add()
        elif type(op) == Sub:
            self.assembly.sub()
        elif type(op) == Mult:
            self.assembly.mul()
        elif type(op) == Div:
            self.assembly.div()
        else:
            raise CompileException('Unsupported operator', op)

    def compare(self, left, ops, comparators):
        if len(ops) > 1 or len(comparators) > 1:
            raise CompileException('Unsupported multiple comparisons', ops[1])
        op = ops[0]
        right = comparators[0]
        self.compile_expr(left)
        self.compile_expr(right)
        if type(op) == In or type(op) == NotIn:
            raise CompileException('Unsupported operator', op)
        getattr(self.assembly, type(op).__name__.lower())()
        if type(op) in [NotEq, IsNot]:
            self.assembly.not_op()

    def if_stmt(self, node):
        self.compile_expr(node.test)
        label = self.new_label()
        self.assembly.bez(label)
        for n in node.body:
            self.compile_stmt(n)
        if len(node.orelse) > 0:
            else_label = self.labels.pop()
            end_label = self.new_label()
            self.assembly.bra(end_label)
            self.assembly.label(else_label)
            for n in node.orelse:
                self.compile_stmt(n)
        self.assembly.label(self.labels.pop())

    def call(self, node):
        func = node.func.id
        if func in builtins:
            return getattr(self, func)(*node.args)
        raise CompileException("Unknown function call %s" % func, node)

    def set_sparkle(self, sparkle_node, r_node, g_node, b_node):
        self.compile_expr(sparkle_node)
        self.compile_expr(r_node)
        self.compile_expr(g_node)
        self.compile_expr(b_node)
        self.assembly.ssprk()
        self.assembly.osprk()

    def set_output(self, output_node, signal_node):
        self.compile_expr(output_node)
        self.compile_expr(signal_node)
        self.assembly.dwr()

    def get_digital(self, output_node):
        self.compile_expr(output_node)
        self.assembly.drd()

    def get_analog(self, output_node):
        self.compile_expr(output_node)
        self.assembly.ard()

    def set_motor_1(self, pct):
        self.compile_expr(pct)
        self.assembly.pushl(187)
        self.assembly.mul()
        self.assembly.pushl(100)
        self.assembly.div()
        self.assembly.mot1()

    def set_motor_2(self, pct):
        self.compile_expr(pct)
        self.assembly.pushl(187)
        self.assembly.mul()
        self.assembly.pushl(100)
        self.assembly.div()
        self.assembly.mot2()

    def set_servo(self, output_node, degree_node):
        self.compile_expr(output_node)
        self.assembly.pushl(4545)
        self.compile_expr(degree_node)
        self.assembly.pushl(34)
        self.assembly.mul()
        self.assembly.add()
        self.assembly.srv()

    def get_distance(self, t_node, e_node):
        self.compile_expr(t_node)
        self.compile_expr(e_node)
        self.assembly.usons()
        self.assembly.usonl()

    def wait(self, time_node):
        if type(time_node) is not Num or type(time_node.n) is not int or time_node.n < 1:
            raise CompileException("Wait time must be a positive integer of milliseconds", time_node)
        self.assembly.pushl(time_node.n)
        start = self.new_label()
        end = self.new_label()
        self.assembly.label(start)
        self.assembly.dup()
        self.assembly.bez(end)
        self.assembly.wait()
        self.assembly.pushl(1)
        self.assembly.sub()
        self.assembly.bra(start)
        self.assembly.label(end)
        self.assembly.poprm()
        self.labels.pop()
        self.labels.pop()

    def random(self, low, high):
        self.compile_expr(low)
        self.compile_expr(high)
        self.assembly.rnd()

    def un_op(self, op, operand):
        if type(op) == USub:
            self.compile_expr(operand)
            self.assembly.pushl(-1)
            self.assembly.mul()
        elif type(op) == UAdd:
            self.compile_expr(operand)
        elif type(op) == Not:
            self.compile_expr(operand)
            self.assembly.not_op()
        else:
            raise CompileException("Unsupported operator %s" % type(op), op)

    def break_stmt(self, node):
        if self.exit_label is None:
            raise CompileException("No loop to break", node)
        self.assembly.bra(self.exit_label)

    def continue_stmt(self, node):
        if self.start_label is None:
            raise CompileException("No loop to continue", node)
        self.assembly.bra(self.start_label)

    def bool_op(self, op, values):
        self.compile_expr(values[0])
        for i in range(1, len(values)):
            self.compile_expr(values[i])
            if type(op) == And:
                self.assembly.and_op()
            elif type(op) == Or:
                self.assembly.or_op()
            else:
                raise CompileException("Unknown operator %s" % type(op), op)
