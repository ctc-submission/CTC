import tools.command_tools as ctools
import tools.file_tools as ftools
import tools.list_tools as ltools
import os


def doCompile(gcc, lib, opt, src, out, error, timetoutReport, crashReport, limit):
    ftools.delete_if_exists(out)
    ftools.delete_if_exists(error)
    cmd = gcc + ' -I ' + lib + ' ' + opt + ' ' + src + ' -o ' + out + ' 2>' + error
    timein = ctools.execmd_limit_time(cmd, limit)
    if not timein:
        errorMsg = ftools.get_file_content(error)
        errorMsg = opt + '\n' + errorMsg
        ftools.put_file_content(timetoutReport, errorMsg)
        return 'compile_timeout'
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        errorMsg = ftools.get_file_content(error)
        errorMsg = opt + '\n' + errorMsg
        ftools.put_file_content(crashReport, errorMsg)
        return 'compile_crash'
    return 'success'


def doExec(out, res, opt, error, crashReport, timeoutReport, limit):
    ftools.delete_if_exists(res)
    ftools.delete_if_exists(error)
    cmd = out + ' 1>' + res + ' 2>' + error
    timein = ctools.execmd_limit_time(cmd, limit)
    if not timein:
        errorMsg = ftools.get_file_content(error)
        errorMsg = opt + '\n' + errorMsg
        ftools.put_file_content(timeoutReport, errorMsg)
        return 'exec_timeout'
    if not os.path.exists(res) or os.path.getsize(res) == 0:
        errorMsg = ftools.get_file_content(error)
        errorMsg = opt + '\n' + errorMsg
        ftools.put_file_content(crashReport, errorMsg)
        return 'exec_crash'
    return 'success'


def doDiff(file1, file2, opt, miscompileReport):
    cmd = 'diff ' + file1 + ' ' + file2
    diff = ctools.execmd(cmd)
    if len(diff) != 0:
        ftools.put_file_content(miscompileReport, opt + '\n' + diff)
        return 'miscompile'
    return 'success'


def doCompileSimplify(gcc, lib, opt, src, out, error, limit):
    ftools.delete_if_exists(out)
    ftools.delete_if_exists(error)
    cmd = gcc + ' -I ' + lib + ' ' + opt + ' ' + src + ' -o ' + out + ' 2>' + error
    timein = ctools.execmd_limit_time(cmd, limit)
    if not timein:
        return 'compile_timeout'
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        return 'compile_crash'
    return 'success'


def doExecSimplify(out, res, error, limit):
    ftools.delete_if_exists(res)
    ftools.delete_if_exists(error)
    cmd = out + ' 1>' + res + ' 2>' + error
    timein = ctools.execmd_limit_time(cmd, limit)
    if not timein:
        return 'exec_timeout'
    if not os.path.exists(res) or os.path.getsize(res) == 0:
        return 'exec_crash'
    lines = open(error, "r").readlines()
    for line in lines:
        if "runtime error" in line:
            return 'exec_crash'
    return 'success'


def doDiffSimplify(file1, file2):
    cmd = 'diff ' + file1 + ' ' + file2
    diff = ctools.execmd(cmd)
    if len(diff) != 0:
        return 'miscompile'
    return 'success'


def testPassSimplify(gcc, lib, opt, src, out, res, error, limit):
    passed = doCompileSimplify(gcc, lib, opt, src, out, error, limit)
    if passed != 'success':
        return passed
    passed = doExecSimplify(out, res, error, limit)
    return passed


def testPass(gcc, lib, opt, src, out, compileTimeoutReport, compileCrashReport,
             res, execTimeoutReport, execCrashReport, error, limit):
    passed = doCompile(gcc, lib, opt, src, out, error, compileTimeoutReport, compileCrashReport, limit)
    if passed != 'success':
        return passed
    passed = doExec(out, res, opt, error, execCrashReport, execTimeoutReport, limit)
    return passed
