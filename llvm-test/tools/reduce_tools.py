# -*- coding=utf-8 -*-
import tools.file_tools as ftools
import tools.command_tools as ctools
import tools.LLVM_processor as LLVM
import os
import tools.list_tools as ltools

CSMITH0 = '/home/ctc/csmith/bin/csmith'
CSMITH1 = '/home/suocy/bin/csmith_exnted0/bin/csmith'

WORK_DIR = '/home/data/tmp10'

LLVM_PATH = '/home/ctc/llvm-releases/llvm-project-10.0.0/build/bin/'
CLANG = LLVM_PATH + 'clang'
OPT = LLVM_PATH + 'opt'
LIB = '/home/ctc/csmith/include/csmith-2.3.0'

def getSeed(reportPath):
    seed = reportPath.split('/')[-2]
    return seed.split('-')[0] if '-' in seed else seed


def generateProgram0(seed, src):
    cmd = CSMITH0 + ' --seed ' + seed + ' > ' + src
    ctools.execmd_limit_time(cmd, 90)


def generateProgram1(seed, src):
    cmd = CSMITH1 + ' --seed ' + seed + ' > ' + src
    ctools.execmd_limit_time(cmd, 90)

def get_negation(flag):
    if '-fno-' not in flag:
        if '-fweb-' not in flag:
            return flag[:2] + 'no-' + flag[2:]
        else:
            print(flag[6:7] + 'no-' + flag[7:])
            return flag[6:7] + 'no-' + flag[7:]
    else:
        return flag[:2] + flag[5:]


def getOpts(LLVM_PATH):
    '''
    获取O3的优化序列
    :param LLVM_PATH: llvm的bin文件夹的路径
    :return:
    '''
    cmd = LLVM_PATH + 'llvm-as < /dev/null | ' + LLVM_PATH + 'opt -O3 -disable-output -debug-pass=Arguments 2>&1'
    optList = ctools.execmd(cmd).split('\n')[:2]
    optList = [optList[i][optList[i].index(':') + 3:] for i in range(len(optList))]
    optList = ' '.join(optList).split(' ')
    return optList


def mapOpt(opts0):
    optList = getOpts(LLVM_PATH)
    tmp = []
    for o in opts0:
        if o in optList:
            tmp.append(o)
    return tmp


def clangTest(clang, opt, lib, src, out, crashReport, timeoutReport, error, limit):
    '''
    clang的测试步骤
    :param clang: clang的路径
    :param opt: 优化列表
    :param lib: 库的路径
    :param src: 源文件路径，指c文件的路径
    :param out: 输出文件的路径，指bc文件
    :param crashReport: 发生崩溃时，报告的路径
    :param timeoutReport: 发生超时时，报告的路径
    :param error: 在编译过程中的错误输出的文件
    :param limit: 时间限制
    :return:
    '''
    timein = LLVM.clang_c_emit_llvm(clang, opt, lib, src, out, error, limit)
    if not timein:
        errorMsg = ftools.get_file_content(error)
        ftools.put_file_content(timeoutReport, errorMsg)
        return 'clang2Bc_timeout'
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        errorMsg = ftools.get_file_content(error)
        ftools.put_file_content(crashReport, errorMsg)
        return 'clang2Bc_crash'
    return 'success'


def optTest(opt, opts, src, out, error, limit, crashReport, timeoutReport):
    '''
    opt组件的测试过程
    :param opt: opt组件的位置
    :param opts: 优化列表，就是List
    :param src: bc文件路径
    :param out: 优化之后的bc文件的路径
    :param error: 错误输出的路径
    :param limit: 时间限制
    :param crashReport: crash报告的位置
    :param timeoutReport: timeout报告的位置
    :return:
    '''
    timein = LLVM.opt(opt, opts, src, out, error, limit)
    if not timein:
        errorMsg = ftools.get_file_content(error)
        errorMsg = ' '.join(opts) + '\n' + errorMsg
        ftools.put_file_content(timeoutReport, errorMsg)
        return 'opt_timeout'
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        errorMsg = ftools.get_file_content(error)
        errorMsg = ' '.join(opts) + '\n' + errorMsg
        ftools.put_file_content(crashReport, errorMsg)
        return 'opt_crash'
    return 'success'


def clang2Exe(clang, opts, src, out, error, limit, crashReport, timeoutReport, optInfo):
    timein = LLVM.clang_direct(clang, opts, '', src, out, error, limit)
    if not timein:
        errorMsg = ftools.get_file_content(error)
        errorMsg = ' '.join(optInfo) + '\n' + errorMsg
        ftools.put_file_content(timeoutReport, errorMsg)
        return 'clang2Exe_timeout'
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        errorMsg = ftools.get_file_content(error)
        errorMsg = ' '.join(optInfo) + '\n' + errorMsg
        ftools.put_file_content(crashReport, errorMsg)
        return 'clang2Exe_crash'
    return 'success'


def exe(src, out, error, limit, crashReport, timeoutReport, optInfo):
    timein = LLVM.exe(src, out, error, limit)
    if not timein:
        errorMsg = ftools.get_file_content(error)
        errorMsg = ' '.join(optInfo) + '\n' + errorMsg
        ftools.put_file_content(timeoutReport, errorMsg)
        return 'exe_timeout'
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        errorMsg = ftools.get_file_content(error)
        errorMsg = ' '.join(optInfo) + '\n' + errorMsg
        ftools.put_file_content(crashReport, errorMsg)
        return 'exe_crash'
    return 'success'


def diff(tmpRes, oriRes, miscompileReport, optInfo):
    cmd = 'diff ' + tmpRes + ' ' + oriRes
    diffRes = ctools.execmd(cmd)
    if len(diffRes) != 0:
        errorMsg = ' '.join(optInfo) + '\n' + diffRes
        ftools.put_file_content(miscompileReport, errorMsg)
        return 'miscompile'
    return 'success'


def compileExec(clang, clang2BcOpts, lib, clang2BcSrc, clang2BcOut, clang2BcCrashReport, clang2BcTimeoutReport,
                opt, optOpts, optOut, optCrashReport, optTimeoutReport,
                clang2ExeOpts, clang2ExeOut, clang2ExeCrashReport, clang2ExeTimeoutReport,
                tmpRes, exeCrashReport, exeTimeoutReport,
                oriRes, miscompileReport,
                error, limit):
    if len(clang2BcSrc) != 0:
        bugType = clangTest(clang, clang2BcOpts, lib, clang2BcSrc, clang2BcOut, clang2BcCrashReport,
                            clang2BcTimeoutReport, error, limit)
        if bugType != 'success':
            return bugType

    bugType = optTest(opt, optOpts, clang2BcOut, optOut, error, limit, optCrashReport, optTimeoutReport)
    if bugType != 'success':
        return bugType

    bugType = clang2Exe(clang, clang2ExeOpts, optOut, clang2ExeOut, error, limit, clang2ExeCrashReport, clang2ExeTimeoutReport, optOpts)
    if bugType != 'success':
        return bugType

    bugType = exe(clang2ExeOut, tmpRes, error, limit, exeCrashReport, exeTimeoutReport, optOpts)
    if bugType != 'success':
        return bugType

    if len(oriRes) != 0:
        bugType = diff(tmpRes, oriRes, miscompileReport, optOpts)
        if bugType != 'success':
            return bugType

    return 'success'


def reduceFlags(optList,status):
    # level = optList[0]
    # del optList[0]
    start = 0
    step = len(optList) / 2
    end = len(optList) if start + step > len(optList) else start + step
    while step >= 1:
        while start < len(optList):
            print('[reduceFlags] [len=' + str(len(optList)) + ', s=' + str(start) + ', e=' + str(end) + ', step=' + str(step) + ']')
            print(optList)
            end = int(end)
            start = int(start)
            tmpOpt = optList[:start]  + optList[end:]
            clang2BcOut = WORK_DIR + '/a.bc'
            optOut = WORK_DIR + '/a.opt.bc'
            optCrashReport = WORK_DIR + '/true_opt_crash.txt'
            optTimeoutReport = WORK_DIR + '/true_opt_timeeout.txt'
            clang2ExeOut = WORK_DIR + '/a.o'
            clang2ExeCrashReport = WORK_DIR + '/true_clang2Exe_crash.txt'
            clang2ExeTimeoutReport = WORK_DIR + '/true_clang2Exe_timeeout.txt'
            tmpRes = WORK_DIR + '/tmp_res.txt'
            exeCrashReport = WORK_DIR + '/true_exe_crash.txt'
            exeTimeoutReport = WORK_DIR + '/true_exe_timeout.txt'
            miscompileReport = WORK_DIR + '/true_miscompile.txt'
            error = WORK_DIR + '/error.txt'
            oriRes = WORK_DIR + '/ori_res.txt'
            bugType = compileExec(CLANG, '', '', '', clang2BcOut, '', '',
                                  OPT, tmpOpt, optOut, optCrashReport, optTimeoutReport,
                                  [], clang2ExeOut, clang2ExeCrashReport, clang2ExeTimeoutReport,
                                  tmpRes, exeCrashReport, exeTimeoutReport,
                                  oriRes, miscompileReport,
                                  error, 30)
            if bugType == status:
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
    # optList.insert(0, level)
    return optList


def reduceMore(optList,status):
    # level = optList[0]
    # del optList[0]
    inx = 0
    while inx < len(optList):
        print('[len=' + str(len(optList)) + ', inx=' + str(inx) + ']')
        print(optList)
        tmpOpt = optList[:inx] + optList[inx + 1:]
        clang2BcOut = WORK_DIR + '/a.bc'
        optOut = WORK_DIR + '/a.opt.bc'
        optCrashReport = WORK_DIR + '/true_opt_crash.txt'
        optTimeoutReport = WORK_DIR + '/true_opt_timeeout.txt'
        clang2ExeOut = WORK_DIR + '/a.o'
        clang2ExeCrashReport = WORK_DIR + '/true_clang2Exe_crash.txt'
        clang2ExeTimeoutReport = WORK_DIR + '/true_clang2Exe_timeeout.txt'
        tmpRes = WORK_DIR + '/tmp_res.txt'
        exeCrashReport = WORK_DIR + '/true_exe_crash.txt'
        exeTimeoutReport = WORK_DIR + '/true_exe_timeout.txt'
        miscompileReport = WORK_DIR + '/true_miscompile.txt'
        error = WORK_DIR + '/error.txt'
        oriRes = WORK_DIR + '/ori_res.txt'
        bugType = compileExec(CLANG, '', '', '', clang2BcOut, '', '',
                              OPT, tmpOpt, optOut, optCrashReport, optTimeoutReport,
                              [], clang2ExeOut, clang2ExeCrashReport, clang2ExeTimeoutReport,
                              tmpRes, exeCrashReport, exeTimeoutReport,
                              oriRes, miscompileReport,
                              error, 30)
        if bugType == status:
            print('[reduceMore] failed')
            optList = tmpOpt[:]
        else:
            print('[reduceMore] pass')
            inx += 1
    # optList.insert(0, level)
    return optList


def original_execute():
    clang2BcSrc = WORK_DIR + '/a.c'
    clang2BcOut = WORK_DIR + '/a.bc'
    clang2BcCrashReport = WORK_DIR + '/clang2Bc_crash.txt'
    clang2BcTimeoutReport = WORK_DIR + '/clang2Bc_timeout.txt'
    optOut = WORK_DIR + '/a.opt.bc'
    optCrashReport = WORK_DIR + '/ori_opt_crash.txt'
    optTimeoutReport = WORK_DIR + '/ori_opt_timeeout.txt'
    clang2ExeOut = WORK_DIR + '/a.o'
    clang2ExeCrashReport = WORK_DIR + '/ori_clang2Exe_crash.txt'
    clang2ExeTimeoutReport = WORK_DIR + '/ori_clang2Exe_timeout.txt'
    tmpRes = WORK_DIR + '/ori_res.txt'
    exeCrashReport = WORK_DIR + '/ori_exe_crash.txt'
    exeTimeoutReport = WORK_DIR + '/ori_exe_timeout.txt'
    error = WORK_DIR + '/error.txt'
    bugType = compileExec(CLANG, ['-O3', '-mllvm', '-disable-llvm-optzns'], LIB, clang2BcSrc, clang2BcOut,
                          clang2BcCrashReport, clang2BcTimeoutReport,
                          OPT, [], optOut, optCrashReport, optTimeoutReport,
                          [], clang2ExeOut, clang2ExeCrashReport, clang2ExeTimeoutReport,
                          tmpRes, exeCrashReport, exeTimeoutReport,
                          '', '',
                          error, 30)
    return bugType == 'success'


def reduce_main(src_file, flags_file,bugType):
    cp_cmd = 'cp ' + src_file + ' ' + WORK_DIR + '/a.c'
    ctools.execmd(cp_cmd)

    if not original_execute():
        print('[error] when original execute')
        exit(1)
    opt_list = flags_file
    opt_list = reduceFlags(opt_list,bugType)
    opt_list = reduceMore(opt_list,bugType)
    return opt_list