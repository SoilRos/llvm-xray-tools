import argparse

parser = argparse.ArgumentParser(
            prog='llvm-xray-tools',
            description='Tools for analysing results produced by the llvm-xray instrumentation')

subparsers = parser.add_subparsers()

big_o = subparsers.add_parser('big_o', help='complexity calculator')
big_o.add_argument('program', type=str, nargs=1,
                    help='executable instrumented with xray')
big_o.add_argument('var_list', type=str,
                    help='list of values that represent the growth of program inputs')
big_o.add_argument('input_list', type=str,
                    help='list input to feed the executable on each run')

args = parser.parse_args()

# args.var_list = args.var_list.split()
# args.input_list = args.input_list.split()
# assert len(args.var_list) == len(args.input_list), "'var_list' and 'input_list' must have the same size"