import os
import subprocess
import shutil
import big_o
import logging
import csv
import pandas
import io
import numpy
import altair

def llvm_xray_exec():
  if 'XRAY_EXECUTABLE' in os.environ:
    executable = os.environ['XRAY_EXECUTABLE']
  else:
    executable = 'llvm-xray'

  if shutil.which(executable) is None:
    raise FileNotFoundError("Exacutable for XRay was not found! Set 'XRAY_EXECUTABLE' with the path to the executable")
  return executable

def xray_trace(program, args, id, cache = True):

  xray_log = '/tmp/xray-log.%s' % id

  if cache and os.path.isfile(xray_log):
    return xray_log

  # extract symbols from program
  symbols = subprocess.check_output('nm ' + program, shell=True, text=True)

  # check if program was linked to xray
  assert 'xray' in symbols, "Program doesn't seem to use the xray library"

  # save current xray settings
  xray_options = None
  if 'XRAY_OPTIONS' in os.environ:
    xray_options = os.environ['XRAY_OPTIONS']

#  try:
  # set enviroment needed to trace the program
  os.environ['XRAY_OPTIONS'] = 'xray_mode=xray-basic patch_premain=true verbosity=1'

  if shutil.which(program) is None:
    raise FileNotFoundError("Exacutable '%s' is not executable" % program)

  # run program
  cmd = '%s %s' % (program, args)
  logging.log(logging.INFO-1,"Tracing events on command: '%s'" % cmd)
  output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, text=True)

  for line in output.splitlines():
    logging.log(logging.INFO-3,"\t%s" % str(line))

  # set old xray settings back to environment
  if not xray_options is None:
    os.environ['XRAY_OPTIONS'] = xray_options

  xray_log_raw = None
  # walk each line from output
  for line in output.splitlines():
    # try to find xray log file keyword
    xray_key = line.rfind("XRay: Log file in '")
    if xray_key != -1:
      # extract log file inmediately after keyword
      xray_log_raw = line[xray_key:].split("'")[1]
      break

  # check if output file was found
  if xray_log_raw is None:
    raise ValueError("XRay file was not found")

  assert os.path.isfile(xray_log_raw)
  os.rename(xray_log_raw,xray_log)

  logging.info("XRay tracing file: %s" % xray_log)

  return xray_log

def xray_accounting(xray_log):
  # run accounting command from xray
  cmd = '%s account --format=csv --sort=funcid %s' % (llvm_xray_exec(), xray_log)
  output = subprocess.check_output(cmd, shell=True, text=True)

  # return accounting as a pandas dataframe
  return pandas.read_csv(io.StringIO(output))

def xray_big_o(stats):
  assert isinstance(stats,pandas.DataFrame)

  for funcid in stats.funcid.unique():
    ns = stats[stats['funcid'] == funcid]['n'].to_numpy()
    times = stats[stats['funcid'] == funcid]['median'].to_numpy()
    if len(times) < 4:
      continue

    classes = [
        big_o.complexities.Constant,
        big_o.complexities.Linear,
        big_o.complexities.Quadratic,
        big_o.complexities.Cubic,
        # big_o.complexities.Polynomial, # broken
        big_o.complexities.Logarithmic,
        big_o.complexities.Linearithmic,
        # big_o.complexities.Exponential # broken
      ]

    best, fitted = big_o.infer_big_o_class(ns,times,classes)

    stats.loc[stats['funcid'] == funcid,'complexity'] = best
    stats.loc[stats['funcid'] == funcid,'complexities'] = [fitted]


    loc = stats.loc[(stats['funcid'] == funcid)][['funcid','median','n']]
    loc['fit'] = best.compute(ns)
    circles = altair.Chart(loc).mark_circle().encode(
        x='n',
        y='median',
    )
    line = altair.Chart(loc).mark_line(
      color='black'
    ).encode(
        x='n',
        y='fit'
    )

    (line + circles).save('complexity-%s.html' % funcid)


  stats_by_funcid = stats.drop_duplicates('funcid')
  complexity = pandas.DataFrame(
    {
      'complexity': stats_by_funcid['complexity'].to_numpy(),
      'complexities': stats_by_funcid['complexities'].to_numpy()
    },
    index= stats_by_funcid['funcid'].to_numpy(),
    copy = True)

  complexity.sort_values(by=['complexity'], ascending = False, inplace = True)
  complexity.dropna(inplace=True)
  with pandas.option_context('display.max_rows', None, 'display.max_columns', None):
   print(complexity['complexity'])

