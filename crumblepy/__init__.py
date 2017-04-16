import argparse
import sys

from crumblepy.compiler import Compiler, CompileException
from crumblepy.usb import send_byte_code

crpy_compiler = Compiler()


def run():
    arg_parser = argparse.ArgumentParser(description="Compile a .crpy source file")
    arg_parser.add_argument("file", help="The .crpy file to compile")
    arg_parser.add_argument("--output", "-o",
                            help="File to save output to (instead of sending to controller over USB). "
                                 "Use --format to specify format. If unspecified, output is instead printed to console")
    arg_parser.add_argument("--format", "-f", help="Output format", choices=["bytecode", "assembly", "usb"],
                            default="usb")
    args = arg_parser.parse_args()

    try:
        code = compile(args.file, args.format)
    except CompileException as e:
        sys.stderr.write("Compile error: %s (%s): %s\n" % (args.file, str(e.args[0]), str(e.args[1])))
        sys.stderr.flush()
    else:
        if args.format != "usb":
            if args.format == "bytecode":
                txt = str(list(map(lambda x: "0x%x" % x, code)))
            else:
                txt = "\n".join(code)
            if args.output:
                with open(args.output, "w") as f:
                    f.writelines(txt)
            else:
                print(txt)
        else:
            print("Sending code over USB")
            send_byte_code(code)
            print("Code sent")


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