import tools.command_tools as ctools
import tools.file_tools as ftools
import tools.list_tools as ltools
import tools.test_tools as ttools
import os

CSMITH0 = '/home/ctc/csmith/bin/csmith'

WORK_DIR = '/home/gcc/par1'

GCC = '/home/ctc/gcc-releases/gcc-4.5/bin/gcc'
GCC_Path = GCC
LIB = '/home/ctc/csmith/include/csmith-2.3.0'

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
    if not os.path.exists(out):
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


def testPass(gcc, lib, opt, src, out, compileTimeoutReport, compileCrashReport,
             res, execTimeoutReport, execCrashReport,
             oriRes, miscompileReport,
             error, limit):
    passed = doCompile(gcc, lib, opt, src, out, error, compileTimeoutReport, compileCrashReport, limit)
    if passed != 'success':
        return passed
    passed = doExec(out, res, opt, error, execCrashReport, execTimeoutReport, limit)
    if passed != 'success':
        return passed
    if len(oriRes) != 0:
        passed = doDiff(res, oriRes, opt, miscompileReport)
        if passed != 'success':
            return passed
    return passed


def reduceFlags(optList, status):
    level = optList[0]
    del optList[0]
    start = 0
    step = len(optList) / 2
    end = len(optList) if start + step > len(optList) else start + step
    end = int(end)
    start = int(start)
    while step >= 1:
        while start < len(optList):
            end = int(end)
            start = int(start)
            print('[reduceFlags] [len=' + str(len(optList)) + ', s=' + str(start) + ', e=' + str(end) + ', step=' + str(
                step) + ']')
            print(optList)

            tmpOpt = optList[:start] + optList[end:]
            out = WORK_DIR + '/a.o'
            compileCrashReport = WORK_DIR + '/flags_compile_crash.txt'
            compileTimeoutReport = WORK_DIR + '/flags_compile_timeout.txt'
            res = WORK_DIR + '/res.txt'
            execTimeoutReport = WORK_DIR + '/flags_exec_timeout.txt'
            execCrashReport = WORK_DIR + '/flags_exec_crash.txt'
            oriRes = WORK_DIR + '/ori_res.txt'
            error = WORK_DIR + '/error.txt'
            miscompileReport = WORK_DIR + '/flags_miscompile.txt'
            passed = testPass(GCC, LIB, ' -Wall -Wextra ' + ' '.join([level] + tmpOpt),
                              WORK_DIR + '/a.c', out, compileTimeoutReport, compileCrashReport,
                              res, execTimeoutReport, execCrashReport,
                              oriRes, miscompileReport, error,60)
            if passed == status:
                print('[reduceFlags] failed')
                optList = tmpOpt[:]
                end = len(optList) if start + step > len(optList) else start + step
            else:
                print('[reduceFlags] pass')
                start = end
                end = len(optList) if start + step > len(optList) else start + step
        start = 0
        step = step / 2
        end = len(optList) if start + step > len(optList) else start + step
    optList.insert(0, level)
    return optList


def reduceMore(optList, status):
    level = optList[0]
    del optList[0]
    inx = 0
    while inx < len(optList):
        print('[len=' + str(len(optList)) + ', inx=' + str(inx) + ']')
        print(optList)

        tmpOpt = optList[:inx] + optList[inx + 1:]
        out = WORK_DIR + '/a.o'
        compileCrashReport = WORK_DIR + '/flags_compile_crash.txt'
        compileTimeoutReport = WORK_DIR + '/flags_compile_timeout.txt'
        res = WORK_DIR + '/res.txt'
        execTimeoutReport = WORK_DIR + '/flags_exec_timeout.txt'
        execCrashReport = WORK_DIR + '/flags_exec_crash.txt'
        oriRes = WORK_DIR + '/ori_res.txt'
        error = WORK_DIR + '/error.txt'
        miscompileReport = WORK_DIR + '/flags_miscompile.txt'
        passed = testPass(GCC, LIB, ' -Wall -Wextra ' + ' '.join([level] + tmpOpt),
                          WORK_DIR + '/a.c', out, compileTimeoutReport, compileCrashReport,
                          res, execTimeoutReport, execCrashReport,
                          oriRes, miscompileReport, error, 60)
        if passed == status:
            print('[reduceMore] failed')
            optList = tmpOpt[:]
        else:
            print('[reduceMore] pass')
            inx += 1
    optList.insert(0, level)
    return optList


def test_original(opt_list):
    out = WORK_DIR + '/a.o'
    compileCrashReport = WORK_DIR + '/ori_compile_crash.txt'
    compileTimeoutReport = WORK_DIR + '/ori_compile_timeout.txt'
    res = WORK_DIR + '/ori_res.txt'
    execTimeoutReport = WORK_DIR + '/ori_exec_timeout.txt'
    execCrashReport = WORK_DIR + '/ori_exec_crash.txt'
    error = WORK_DIR + '/error.txt'
    passed = testPass(GCC, LIB, '', WORK_DIR + '/a.c', out, compileTimeoutReport, compileCrashReport,
                      res, execTimeoutReport, execCrashReport,
                      '', '', error,60)
    if passed != 'success':
        print('[test_original] Failed at original compile, don\'t interest')
        return False

    out = WORK_DIR + '/a.o'
    compileCrashReport = WORK_DIR + '/flags_compile_crash.txt'
    compileTimeoutReport = WORK_DIR + '/flags_compile_timeout.txt'
    res = WORK_DIR + '/res.txt'
    execTimeoutReport = WORK_DIR + '/flags_exec_timeout.txt'
    execCrashReport = WORK_DIR + '/flags_exec_crash.txt'
    oriRes = WORK_DIR + '/ori_res.txt'
    error = WORK_DIR + '/error.txt'
    miscompileReport = WORK_DIR + '/flags_miscompile.txt'
    passed = testPass(GCC, LIB, opt_list, WORK_DIR + '/a.c', out, compileTimeoutReport, compileCrashReport,
                      res, execTimeoutReport, execCrashReport,
                      oriRes, miscompileReport, error,60)
    if passed == 'success':
        print('[test_original] pass at optlist, is not a bug(has fixed)')
        return False
    return True


def preprocess(src):
    preprocess_cmd = GCC_Path + ' -E -I ' + LIB + ' ' + WORK_DIR + '/a.c' + ' -o ' + src
    ctools.execmd(preprocess_cmd)


def original_execute():
    out = WORK_DIR + '/a.o'
    compileCrashReport = WORK_DIR + '/ori_compile_crash.txt'
    compileTimeoutReport = WORK_DIR + '/ori_compile_timeout.txt'
    res = WORK_DIR + '/ori_res.txt'
    execTimeoutReport = WORK_DIR + '/ori_exec_timeout.txt'
    execCrashReport = WORK_DIR + '/ori_exec_crash.txt'
    error = WORK_DIR + '/error.txt'
    passed = testPass(GCC_Path, LIB, '', WORK_DIR + '/a.c', out, compileTimeoutReport, compileCrashReport,
                      res, execTimeoutReport, execCrashReport,
                      '', '', error,60)
    return passed == 'success'

def reduce(src_file,flags,status):
    cp_cmd = 'cp ' + src_file + ' ' + WORK_DIR + '/a.c'
    ctools.execmd(cp_cmd)
    if not original_execute():
        print('[error] when original execute')
        return ["false"]
    opt_list = flags.split(' ')
    opt_list = reduceFlags(opt_list, status)
    opt_list = reduceMore(opt_list, status)
    print(opt_list)
    return opt_list