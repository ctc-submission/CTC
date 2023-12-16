import math
import random

import tools.command_tools as ctools
import tools.file_tools as ftools
import tools.list_tools as ltools
import tools.test_tools as ttools
import tools.reduce_tools as rtools
import tools.pca_tools as ptools
import time
import os
import threading
import csmith_multi_tools as cst

GCC_Path = '/home/ctc/gcc-releases/gcc-4.5/bin/gcc'
CSMITH_Path = '/home/ctc/csmith/bin/csmith'
SAMPLINGCA_Path = '/home/ctc/gcc-SamplingCA/SamplingCA-Plus/SamplingCAPlus_final'
CNF_Path = '/home/ctc/gcc-test/example/pca/example_cnf.cnf'
PCA_Path = '/home/ctc/gcc-test/example/pca/example_pca.txt'
REPORT_Path = '/home/ctc/gcc-test/example/report/'
EXAMPLE_Path = '/home/ctc/gcc-test/example'
LIB = '/home/ctc/csmith/include/csmith-2.3.0/'
t_wise = 3
tupleList = []
mapOpt={}
mapTuple={}
TIME_LIMIT = 24 * 60 * 60



forbiddenList = ["-fselective-scheduling"]


def generateProgram(CSMITH, src):
    cmd = CSMITH + ' > ' + src
    ctools.execmd_limit_time(cmd, 60)


def generatePCA(SAMPLINGCA, input_path, output_path):
    ftools.gen_file(input_path)
    ftools.gen_file(output_path)
    cmd = SAMPLINGCA + ' -input_cnf_path ' + input_path + ' -output_testcase_path ' + output_path + ' -t_wise ' + str(
        t_wise)
    ctools.execmd(cmd)


def getFullOpts(GCC):
    opt3 = ctools.execmd(GCC + ' -O3 -Q --help=optimizers').split('\n')
    opt3 = ltools.extract(opt3, '[enabled]')
    opt3 = ltools.strip(opt3)
    opt3 = ltools.get_first_word(opt3)

    opt4 = ctools.execmd(GCC + ' -O3 -Q --help=optimizers').split('\n')
    opt4 = ltools.extract(opt4, '[disabled]')
    opt4 = ltools.strip(opt4)
    opt4 = ltools.get_first_word(opt4)
    for i in opt4:
        fl = 0
        for j in forbiddenList:
            if j in i:
                fl = 1
        if fl:
            continue
        opt3.append(i)
    return opt3


def getFullO3Opts(GCC):
    opt3 = ctools.execmd(GCC + ' -O3 -Q --help=optimizers').split('\n')
    opt3 = ltools.extract(opt3, '[enabled]')
    opt3 = ltools.strip(opt3)
    opt3 = ltools.get_first_word(opt3)
    return opt3


def getFullO2Opts(GCC):
    opt3 = ctools.execmd(GCC + ' -O2 -Q --help=optimizers').split('\n')
    opt3 = ltools.extract(opt3, '[enabled]')
    opt3 = ltools.strip(opt3)
    opt3 = ltools.get_first_word(opt3)
    return opt3


def get_negation(flag):
    if '-fno-' not in flag:
        if '-fweb-' not in flag:
            return flag[:2] + 'no-' + flag[2:]
        else:
            return flag[6:7] + 'no-' + flag[7:]
    else:
        return flag[:2] + flag[5:]


def getNegativeOpts(GCC):
    opt3 = ctools.execmd(GCC + ' -O3 -Q --help=optimizers').split('\n')
    opt3 = ltools.extract(opt3, '[enabled]')
    opt3 = ltools.strip(opt3)
    opt3 = ltools.get_first_word(opt3)

    opt4 = ctools.execmd(GCC + ' -O3 -Q --help=optimizers').split('\n')
    opt4 = ltools.extract(opt4, '[disabled]')
    opt4 = ltools.strip(opt4)
    opt4 = ltools.get_first_word(opt4)
    for i in opt4:
        fl = 0
        for j in forbiddenList:
            if j in i:
                fl = 1
        if fl:
            continue
        opt3.append(i)

    opt3 = [get_negation(opt3[i]) for i in range(len(opt3))]

    return opt3


def getNegativeO3Opts(GCC):
    opt3 = ctools.execmd(GCC + ' -O3 -Q --help=optimizers').split('\n')
    opt3 = ltools.extract(opt3, '[enabled]')
    opt3 = ltools.strip(opt3)
    opt3 = ltools.get_first_word(opt3)

    opt3 = [get_negation(opt3[i]) for i in range(len(opt3))]

    return opt3


def genOptCnf(length, opts, opts1, opts2):
    ftools.delete_if_exists(CNF_Path)
    ftools.gen_file(CNF_Path)
    target = open(CNF_Path, 'w')
    for i in range(0, len(opts[0])):
        target.write('c ' + str(i + 1) + ' 0: ' + opts[0][i] + ' 1: ' + opts[1][i] + '\n')
    l = -1
    r = -1
    j = -1
    for i in range(0, len(opts2)):
        if opts2[i] == '-funit-at-a-time':
            l = i
        if opts2[i] == '-ftoplevel-reorder':
            r = i
        if opts2[i] == '-fsection-anchors':
            j = i
    l += 1
    r += 1
    j += 1
    cntt = 0
    if l != 0 and r != 0:
        cntt+=1
    if r != 0 and j != 0:
        cntt+=1
    target.write('p cnf ' + str(length) + ' '+str(cntt)+'\n')
    
    if l != 0 and r != 0:
        tupleList.append([l,r*(-1)])
        target.write(str(l) + ' -' + str(r) + ' 0\n')
    if r != 0 and j != 0:
        tupleList.append([r,r*(-j)])
        target.write(str(r) + ' -' + str(j) + ' 0\n')
    target.close()


def genOptSet(SAMPLINGCA, CNF, output, length, opts1, opts2):
    ftools.delete_if_exists(output)
    opts = [opts1, opts2]
    genOptCnf(length, opts, opts1, opts2)
    generatePCA(SAMPLINGCA, CNF, output)
    target = open(output, 'r')
    Tests = []
    lines = target.readlines()
    for line in lines:
        tmp = line.split(' ')
        tmp = tmp[:-1]
        Test = []
        pos = 0
        for i in tmp:
            x = int(i)
            Test.append(opts[x][pos])
            pos += 1
        Tests.append(Test)
    target.close()
    return Tests

def genNewOptSet(SAMPLINGCA, CNF, output, length, opts1, opts2):
    opts = [opts1, opts2]
    target = open(output, 'r')
    Tests = []
    lines = target.readlines()
    for line in lines:
        tmp = line.split(' ')
        tmp = tmp[:-1]
        Test = []
        pos = 0
        for i in tmp:
            x = int(i)
            Test.append(opts[x][pos])
            pos += 1
        Tests.append(Test)
    target.close()
    return Tests

def genAllPositiveAndNegativeOpt(opts1, opts2):
    Tests = []
    opt = ''
    for i in range(0, len(opts1)):
        mapOpt[opts1[i]]=(i+1)*(-1)
        if i != 0:
            opt += ' '
        opt += opts1[i]
    Tests.append(opt)
    opt2 = ''
    for i in range(0, len(opts2)):
        mapOpt[opts2[i]]=i+1
        if i != 0:
            opt2 += ' '
        opt2 += opts2[i]
    Tests.append(opt2)
    return Tests

def getBits():
    f = open("/home/ctc/gcc-test/example/pca/example_pca.txt","r")
    lines = f.readlines()
    bits = []
    cntt = 0
    for line in lines:
        tmp = line.split(' ')[:-1]
        bit = []
        for i in tmp:
            if i=='1':
                bit.append(1)
            elif i == '0':
                bit.append(0)
        bits.append(bit)
    return bits

def getPartialLen(idxs,samples,bits,perc):
    mp = {}
    cntt = 0
    n = len(samples)
    for idx in idxs:
        tbit = bits[idx-1]
        for i in range(0,n):
            sample = samples[i]
            fl = 0
            for t in sample:
                if tbit[t[0]]!=t[1]:
                   fl = 1
            if fl==0:
                mp[i]=1 
        cntt+=1
        if(float(len(mp.items()))>n*perc):
            break
    return cntt

def randSample(numOpts,numSamples):
    sampleList = []
    for i in range(0,numSamples):
        a = random.randint(0,numOpts-1)
        b = random.randint(0,numOpts-1)
        c = random.randint(0,numOpts-1)
        avalue = random.randint(0,1)
        bvalue = random.randint(0,1)
        cvalue = random.randint(0,1)
        la = [a,avalue]
        lb = [b,bvalue]
        lc = [c,cvalue]
        sampleList.append([la,lb,lc])
    return sampleList

def getSortedList(testList,sampleList):
    contri = []
    for test in testList:
        c = 0
        for sample in sampleList:
            fl = 0
            for t in sample:
                if test[t[0]]!=t[1]:
                    fl=1
            if fl==0:
                c+=1
        contri.append(c)
    idxs = [i for i in range(0,len(testList))]
    idxs.sort(key=lambda x: contri[x])
    return idxs

sampleLen = [100000]
percList = [0.90]


class CTCThread(threading.Thread):

    def __init__(self, idx,sampleIdx,percIdx):
        self.idx = idx
        self.sampleIdx=sampleIdx
        self.percIdx=percIdx
        super().__init__()

    def run(self) -> None:
        startTime = time.time()
        endTime = time.time()
        ite = 0
        ctools.execmd("rm -rf "+EXAMPLE_Path+'/'+str(self.idx))
        ctools.execmd("mkdir "+EXAMPLE_Path+'/'+str(self.idx))
        ctools.execmd("mkdir "+EXAMPLE_Path+'/'+str(self.idx)+'/code')
        ctools.execmd("mkdir "+EXAMPLE_Path+'/'+str(self.idx)+'/report')
        report_pre = EXAMPLE_Path+'/'+str(self.idx)+'/report/'
        code_pre = EXAMPLE_Path+'/'+str(self.idx)+'/code/'
        
        BugMapping = {'compile_timeout': 0, 'compile_crash': 0, 'exec_timeout': 0, 'exec_crash': 0, 'miscompile': 0}
        bugRecord = './bugRe'+str(self.idx)+'.txt'
        ctools.execmd("touch "+bugRecord)
        while endTime - startTime <= TIME_LIMIT:
            ptools.addTuple(CNF_Path,len(allOpts),tupleList)
            ptools.generateNewPCA(CNF_Path,PCA_Path)
            tests = genNewOptSet(SAMPLINGCA_Path, CNF_Path, PCA_Path, len(allOpts), allNegativeOpts, allOpts)
            samples = randSample(len(allOpts),sampleLen[self.sampleIdx-1])
            bits = getBits()
            idxs = getSortedList(bits,samples)
            cutLen = getPartialLen(idxs,samples,bits,percList[self.percIdx-1])
            programs_and_tests = cst.gen_programs(ite,code_pre)
            programs = programs_and_tests[0]
            ite += 1
            for idxx in range(0, len(programs)):
                endTime = time.time()
                if endTime - startTime > TIME_LIMIT:
                    break
                program = programs[idxx]
                rdm = random.randint(0, 100000)
                compileTimeoutReport = report_pre + 'compile_timeout-' + str(BugMapping['compile_timeout']) + '.txt'
                compileCrashReport = report_pre + 'compile_crash-' + str(BugMapping['compile_crash']) + '.txt'
                exeTimeoutReport = report_pre + 'exec_timeout-' + str(BugMapping['exec_timeout']) + '.txt'
                exeCrashReport = report_pre + 'exec_crash-' + str(BugMapping['exec_crash']) + '.txt'
                misCompileReport = report_pre + 'miscompile-' + str(rdm) + '-' + str(BugMapping['miscompile']) + '.txt'
                tmpRes = code_pre + 'tmp_res.txt'
                error = code_pre + 'tmp_error.txt'
                out = program[:-1]
                out += 'o'
                negativeType = ttools.testPassSimplify(GCC_Path, LIB, '', program, out, tmpRes, error, 60)
                if negativeType != 'success':
                    continue
                cntt = 0
                testId = 0
                for idx in idxs:
                    test = tests[idx-1]
                    testId += 1
                    endTime = time.time()
                    if testId > cutLen:
                        break
                    if endTime - startTime > TIME_LIMIT:
                        break
                    opt = ' -O3 ' + PAndN[0] + ' '
                    for i in range(0, len(test)):
                        if i != 0:
                            opt += ' '
                        opt += test[i]
                    res = code_pre + 'res.txt'
                    bugType = ttools.testPass(GCC_Path, LIB, opt, program, out, compileTimeoutReport, compileCrashReport,
                                            res, exeTimeoutReport, exeCrashReport, error, 60)
                    if bugType != 'success':
                        if "timeout" not in bugType:
                            bugTriggers = rtools.reduce(program,opt,bugType)
                            tempList = []
                            for bugTrigger in bugTriggers:
                                if "-f" not in bugTrigger:
                                    continue
                                tempList.append(mapOpt[bugTrigger])
                            if len(tempList)==0:
                                ftools.put_file_content(bugRecord, program)
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, ' '.join(bugTriggers))
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, bugType)
                                ftools.put_file_content(bugRecord, '\n')
                                BugMapping[bugType] += 1
                                cntt += 1
                                continue
                            strNums=[str(x) for x in tempList]
                            if mapTuple.__contains__(','.join(strNums)):
                                continue
                            else:
                                mapTuple[','.join(strNums)]=1
                                tupleList.append(tempList)
                                BugMapping[bugType] += 1
                                ftools.put_file_content(bugRecord, program)
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, ' '.join(bugTriggers))
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, bugType)
                                ftools.put_file_content(bugRecord, '\n')
                                cntt += 1
                    else:
                        bugType = ttools.doDiff(res, tmpRes, opt, misCompileReport)
                        if bugType != 'success':
                            bugTriggers = rtools.reduce(program,opt,bugType)
                            tempList = []
                            for bugTrigger in bugTriggers:
                                if "-f" not in bugTrigger:
                                    continue
                                tempList.append(mapOpt[bugTrigger])
                            if len(tempList)==0:
                                ftools.put_file_content(bugRecord, program)
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, ' '.join(bugTriggers))
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, bugType)
                                ftools.put_file_content(bugRecord, '\n')
                                BugMapping[bugType] += 1
                                cntt += 1
                                continue
                            strNums=[str(x) for x in tempList]
                            if mapTuple.__contains__(','.join(strNums)):
                                continue
                            else:
                                mapTuple[','.join(strNums)]=1
                                tupleList.append(tempList)
                                ftools.put_file_content(bugRecord, program)
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, ' '.join(bugTriggers))
                                ftools.put_file_content(bugRecord, '\n')
                                ftools.put_file_content(bugRecord, bugType)
                                ftools.put_file_content(bugRecord, '\n')
                                BugMapping[bugType] += 1
                                cntt += 1
                            
                    compileTimeoutReport = report_pre + 'compile_timeout-' + str(
                        BugMapping['compile_timeout']) + '.txt'
                    compileCrashReport = report_pre + 'compile_crash-' + str(
                        BugMapping['compile_crash']) + '.txt'
                    exeTimeoutReport = report_pre + 'exec_timeout-' + str(BugMapping['exec_timeout']) + '.txt'
                    exeCrashReport = report_pre + 'exec_crash-' + str(BugMapping['exec_crash']) + '.txt'
                    misCompileReport = report_pre + 'miscompile-' + str(rdm) + '-' + str(
                        BugMapping['miscompile']) + '.txt'
                    print(bugType)
            endTime = time.time()




if __name__ == '__main__':
    allOpts = getFullO3Opts(GCC_Path)
    allNegativeOpts = getNegativeO3Opts(GCC_Path)
    tests = genOptSet(SAMPLINGCA_Path, CNF_Path, PCA_Path, len(allOpts), allNegativeOpts, allOpts)
    PAndN = genAllPositiveAndNegativeOpt(allNegativeOpts, allOpts)
    cst.gen_pcas()
    for i in range(1,2):
        t = CTCThread(i,1,1)
        t.start()
            
