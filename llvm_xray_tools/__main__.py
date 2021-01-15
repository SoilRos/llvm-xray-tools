import sys
import argparse
import logging
import itertools
import pandas
import hashlib

from .big_o import xray_trace
from .big_o import xray_accounting
from .big_o import xray_big_o

def sha256sum(filename):
  h  = hashlib.sha256()
  b  = bytearray(128*1024)
  mv = memoryview(b)
  with open(filename, 'rb', buffering=0) as f:
      for n in iter(lambda : f.readinto(mv), 0):
          h.update(mv[:n])
  return h

def big_o(args):
  # check sum binary to use it as cache id
  hash = sha256sum(args.program[0])

  # get growth numbers
  if not args.n_list:
    n_list = []
    for input in args.input_list:
      # split all integers present in input
      numbers_in_input = [int(''.join(i)) for is_digit, i in itertools.groupby(input, str.isdigit) if is_digit]
      # if there is only one, we assume that's our number
      assert len(numbers_in_input) == 1, "'n_list' cannot be deduced from 'input_list'"
      n_list.append(numbers_in_input[0])
    args.n_list = n_list
  else:
    args.n_list = args.n_list.split(',')

  assert len(args.n_list) == len(args.input_list), "'n_list' must have the same size as 'input list'"

  df = pandas.DataFrame()
  counter = {}
  for n, input in zip(args.n_list, args.input_list):
    for i in range(args.repeat[0]):
      counter.setdefault(n,0)
      counter[n] += 1
      hash_n = hash.copy()
      hash_n.update(str(n).encode('ascii'))
      hash_n.update(str(counter[n]).encode('ascii'))
      xray_file = xray_trace(args.program[0], input, hash_n.hexdigest(), args.cache)
      df_n = xray_accounting(xray_file)
      df_n['n'] = n
      df = pandas.concat([df,df_n])

  xray_big_o(df, args.field, args.plot_dir[0])

parser = argparse.ArgumentParser(
            prog='llvm-xray-tools',
            description='Tools for analysing results produced by the llvm-xray instrumentation')

parser.add_argument('--verbose', '-v', action='count', default=0)
parser.add_argument('--version', action='version', version='%(prog)s 0.0.0')
parser.add_argument('--loglevel', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument('--logformat', type=str, default='%(message)s')
parser.add_argument('--no-cache', dest='cache', action='store_false',
                           help='Do not use cache files for computations')
parser.add_argument('--cache', action='store_true', default=True,
                           help='Use cache files for computations (default)')

subparsers = parser.add_subparsers()

big_o_parser = subparsers.add_parser('big_o', help='complexity calculator')
big_o_parser.set_defaults(func = big_o)
big_o_parser.add_argument('program', type=str, nargs=1,
                           help='executable instrumented with xray')
big_o_parser.add_argument('--n-list', '-n', type=str,
                           help='list of comma-separated values that represent the growth of program inputs.'
                           'This argument is optional only if the value may be deduced from the input list')
big_o_parser.add_argument('--repeat','-r', nargs=1, type=int, default=[1],
                          help= "times to repeat each argument")
big_o_parser.add_argument('--plot-dir', nargs=1, type=str,
                          help= "directory to plot complexity graph for each function id")
big_o_parser.add_argument('input_list', type=str, nargs='+',
                           help='list input arguments to feed the executable on each run')
big_o_parser.add_argument('--field', type=str, default='med', choices=['count', 'med', 'min', '90p', '99p', 'max', 'sum'],
                          help="field to be compared")

def main():
  """The main routine"""
  args = parser.parse_args()

  # set up logging
  verbose_level = getattr(logging, args.loglevel) - args.verbose
  logging.basicConfig(level=verbose_level, format=args.logformat)
  args.func(args)

if __name__ == "__main__":
    sys.exit(main())



