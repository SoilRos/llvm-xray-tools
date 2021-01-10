import os
import subprocess
import shutil
import big_o

if 'XRAY_EXECUTABLE' in os.environ:
  LLVM_XRAY_EXEC = os.environ['XRAY_EXECUTABLE']
else:
  LLVM_XRAY_EXEC = 'llvm-xray'

if shutil.which(LLVM_XRAY_EXEC) is None:
  raise FileNotFoundError("Exacutable for XRay was not found! Set 'XRAY_EXECUTABLE' with the path to the executable")

def xray_trace(program, args):

  # extract symbols from program
  symbols = subprocess.check_output('nm ' + program, shell=True, text=True)
  
  # check if program was linked to xray
  assert 'xray' in symbols

  # save current xray settings
  if 'XRAY_OPTIONS' in os.environ:
    xray_options = os.environ['XRAY_OPTIONS']
  
  try:
    # set enviroment needed to trace the program
    os.environ['XRAY_OPTIONS'] = 'xray_mode=xray-basic patch_premain=true verbosity=1'
    
    if shutil.which(program) is None:
      raise FileNotFoundError("Exacutable '%s' is not executable" % program)

    # run program
    cmd = '%s %s' % (program, args)
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, text=True)
  except:
    pass

  # set old xray settings back to environment
  if not xray_options is None:
    os.environ['XRAY_OPTIONS'] = xray_options

  # walk each line from output 
  for line in output.splitlines():
    # try to find xray log file keyword
    xray_key = line.rfind("XRAY_OUTPUT=")
    if xray_key != -1:
      # extract log file inmediately after keyword
      xray_file = line[xray_key:].split("'")[0]
      break

  # check if output file was found
  if xray_file is None:
    raise BaseException("")

  return xray_file

def xray_accounting(xray_file):
  # run accounting command from xray
  output = os.system('%s account %s' % (LLVM_XRAY_EXEC, xray_file))

  # register stats in a map
  stats_by_function = output

  return stats_by_function

def xray_bigo(ns, stats_by_program):

  stats_by_function = {}
  bigo_stats = {}

  # combine xray_stats into one class
  # list of single run stats -> map of function if to list of times
  for n, program_stats in zip(ns,stats_by_program):
    for function_stats in program_stats:
      id = function_stats['id']
      stats_by_function[id][str(n)] = function_stats

  for function_stats in stats_by_function:
    function_id = function_stats['id']
    function_times = []
    function_ns = []
    for n in ns:
      if str(n) in function_stats:
        function_times.append(function_stats[str(n)]['time'])
        function_ns.append(n)
    
    if len(function_ns) > 5:
      best, fitted = big_o.infer_big_o_class(function_ns,function_times)
      bigo_stats[function_id]['best'] = best
      bigo_stats[function_id]['fitted'] = fitted

  return bigo_stats