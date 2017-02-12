from .compiler import Compiler
from .parser import Parser
from .usb import send_byte_code

crpy_compiler = Compiler()


def get_assembly(file):
    return compile(file, "assembly")


def get_bytecode(file):
    return compile(file, "bytecode")


def compile(file, output_format):
    global crpy_compiler
    crpy_parser = Parser(file)
    crpy_compiler = Compiler(output_format)
    return crpy_compiler.compile(crpy_parser.root)


def compile_to_device(file):
    code = compile(file, "usb")
    send_byte_code(code)
    return code