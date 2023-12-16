import tools.command_tools as ctools
import tools.LLVM_processor as LLVM
import tools.file_tools as ftools
import tools.list_tools as ltools
import threading
import llvm_multi_tools as lmtools
import tools.pca_tools as ptools
import tools.reduce_tools as rtools
import random
import time
import os

LLVM_PATH_OLD = '/home/ctc/llvm-releases/llvm-project-10.0.0/build/bin/'
LLVM_PATH_NEW = '/home/ctc/llvm-releases/llvm-project-10.0.0/build/bin/'


LLVM_PATH = LLVM_PATH_NEW
CLANG = LLVM_PATH + 'clang'
OPT = LLVM_PATH + 'opt'
LLC = LLVM_PATH + 'llc'

CSMITH_Path = '/home/ctc/csmith/bin/csmith'

LIB = '/home/ctc/csmith/include/csmith-2.3.0/'

TIME_LIMIT = 24 * 60 * 60

SAMPLINGCA_Path = '/home/ctc/SamplingCA-Plus-competition/SamplingCAPlus_final'
CNF_Path = '/home/ctc/llvm-test/example/pca/example_cnf.cnf'
PCA_Path = '/home/ctc/llvm-test/example/pca/example_pca.txt'
EXAMPLE_Path = '/home/ctc/llvm-test/example'
t_wise = 3
tupleList = []
mapOpt={}
mapTuple={}

def compileExec(clang, clang2BcOpts, lib, clang2BcSrc, clang2BcOut, clang2BcError, clang2BcTimeout, clang2BcCrash,
                opt, optOpts, optOut, optError, optTimeout, optCrash,
                clang2ExeOpt, clang2ExeOut, clang2ExeError, clang2ExeTimeout, clang2ExeCrash,
                exeOut, exeError, exeTimeout, exeCrash,
                originalRes, miscompile,
                limit):
    if clang2BcSrc != '':
        timein = LLVM.clang_c_emit_llvm(clang, clang2BcOpts, lib, clang2BcSrc, clang2BcOut, clang2BcError, limit)
        if not timein:
            errorMsg = ftools.get_file_content(clang2BcError)
            ftools.put_file_content(clang2BcTimeout, errorMsg)
            return 'clang_timeout'
        if not os.path.exists(clang2BcOut) or os.path.getsize(clang2BcOut) == 0:
            errorMsg = ftools.get_file_content(clang2BcError)
            ftools.put_file_content(clang2BcCrash, errorMsg)
            return 'clang_crash'

    clang2ExeSrc = clang2BcOut

    flagInfo = ''
    if opt != '':
        flagInfo = ' '.join(optOpts) + '\n'
        optSrc = clang2BcOut
        timein = LLVM.opt(opt, optOpts, optSrc, optOut, optError, limit)
        if not timein:
            errorMsg = ftools.get_file_content(optError)
            ftools.put_file_content(optTimeout, flagInfo + errorMsg)
            return 'opt_timeout'
        if not os.path.exists(optOut) or os.path.getsize(optOut) == 0:
            errorMsg = ftools.get_file_content(optError)
            ftools.put_file_content(optCrash, flagInfo + errorMsg)
            return 'opt_crash'
        clang2ExeSrc = optOut

    timein = LLVM.clang_direct(CLANG, clang2ExeOpt, LIB,clang2ExeSrc, clang2ExeOut, clang2ExeError, limit)
    if not timein:
        errorMsg = ftools.get_file_content(clang2ExeError)
        ftools.put_file_content(clang2ExeTimeout, flagInfo + errorMsg)
        return 'clang2exe_timeout'
    if not os.path.exists(clang2ExeOut) or os.path.getsize(clang2ExeOut) == 0:
        errorMsg = ftools.get_file_content(clang2ExeError)
        ftools.put_file_content(clang2ExeCrash, flagInfo + errorMsg)
        return 'clang2exe_crash'

    exeSrc = clang2ExeOut
    timein = LLVM.exe(exeSrc, exeOut, exeError, limit)
    if not timein:
        errorMsg = ftools.get_file_content(exeError)
        ftools.put_file_content(exeTimeout, flagInfo + errorMsg)
        return 'exe_timeout'
    if not os.path.exists(exeOut) or os.path.getsize(exeOut) == 0:
        errorMsg = ftools.get_file_content(exeError)
        ftools.put_file_content(exeCrash, flagInfo + errorMsg)
        ftools.put_file_content(exeCrash, exeSrc)
        return 'exe_crash'

    if originalRes != '':
        cmd = 'diff ' + originalRes + ' ' + exeOut
        diff = ctools.execmd(cmd)
        if len(diff) != 0:
            ftools.put_file_content(miscompile, flagInfo + diff)
            ftools.put_file_content(miscompile, exeOut)
            return 'miscompile'

    return 'success'



def genOptCnf(length, opts):
    ftools.delete_if_exists(CNF_Path)
    ftools.gen_file(CNF_Path)
    target = open(CNF_Path, 'w')
    for i in range(0, len(opts)):
        target.write('c ' + str(i + 1) + ' 0: ' + opts[i]+'\n')
    cntt = 0
    target.write('p cnf ' + str(length) + ' '+str(cntt)+'\n')
    target.close()

def genNewOptSet(SAMPLINGCA, CNF, output, length, opts):
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
            if x==1:
                Test.append(opts[pos])
            pos += 1
        Tests.append(Test)
    target.close()
    return Tests

def genOptSet(SAMPLINGCA, CNF, output, length,opts):
    ftools.delete_if_exists(output)
    genOptCnf(length, opts)
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
            if x==1:
                Test.append(opts[pos])
            pos += 1
        Tests.append(Test)
    target.close()
    return Tests

def generatePCA(SAMPLINGCA, input_path, output_path):
    ftools.gen_file(input_path)
    ftools.gen_file(output_path)
    cmd = SAMPLINGCA + ' -input_cnf_path ' + input_path + ' -output_testcase_path ' + output_path + ' -t_wise ' + str(
        t_wise)+' -p 30'
    ctools.execmd(cmd)

def writeBug(bugRecord,program,opt,bugType):
    ftools.put_file_content(bugRecord, program)
    ftools.put_file_content(bugRecord, '\n')
    ftools.put_file_content(bugRecord, opt)
    ftools.put_file_content(bugRecord, '\n')
    ftools.put_file_content(bugRecord, bugType)
    ftools.put_file_content(bugRecord, '\n')

def getBits():
    f = open(PCA_Path,"r")
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
        
        bugCountsMap = {'miscompile': 0, 'exe_timeout': 0, 'clang2exe_crash': 0, 'clang2exe_timeout': 0,
                        'llc_crash': 0, 'llc_timeout': 0, 'opt_crash': 0, 'opt_timeout': 0,'exe_crash':0}
        bugRecord = './bugRe'+str(self.idx)+'.txt'
        ctools.execmd("touch "+bugRecord)
        while endTime - startTime <= TIME_LIMIT:

            ptools.addTuple(CNF_Path,len(allOpts),tupleList)
            ptools.generateNewPCA(CNF_Path,PCA_Path)
            tests = genNewOptSet(SAMPLINGCA_Path, CNF_Path, PCA_Path, len(allOpts),allOpts)
            
            samples = randSample(len(allOpts),sampleLen[self.sampleIdx-1])
            bits = getBits()
            idxs = getSortedList(bits,samples)
            cutLen = getPartialLen(idxs,samples,bits,percList[self.percIdx-1])
            
            programs_and_tests = lmtools.gen_programs(ite,code_pre)
            programs = programs_and_tests[0]
            ite += 1
            for idxx in range(0, len(programs)):
                endTime = time.time()
                if endTime - startTime > TIME_LIMIT:
                    break
                program = programs[idxx]
                
                clang2BcSrc = program
                clang2BcOut = program[:-1] + 'bc'
                codeError = code_pre + 'tmp_error.txt'
                clang2BcTimeout = report_pre + 'clang2Bc_timeout.txt'
                clang2BcCrash = report_pre + 'clang2Bc_crash.txt'
                clang2ExeOut = program[:-1] + 'out'
                clang2ExeTimeout = report_pre + 'clang2Exe_timeout.txt'
                clang2ExeCrash = report_pre + 'clang2Exe_crash.txt'
                exeOut = code_pre + 'res0'
                resError = code_pre + 'error.txt'
                exeTimeout = report_pre + 'exe_timeout.txt'
                exeCrash = report_pre + 'exe_crash.txt'
                bug = compileExec(CLANG, ['-O3', '-mllvm', '-disable-llvm-optzns'], LIB,
                                clang2BcSrc, clang2BcOut, codeError, clang2BcTimeout, clang2BcCrash,
                                '', '', '', '', '', '',
                                '', clang2ExeOut, codeError, clang2ExeTimeout, clang2ExeCrash,
                                exeOut, resError, exeTimeout, exeCrash,
                                '', '',
                                30)
                if bug != 'success':
                    endTime = time.time()
                    continue

                originalRes = exeOut


                cntt = 0
                testId = 0
                for idx in idxs:
                    test = tests[idx-1]
                    testId += 1
                    endTime = time.time()
                    if testId > cutLen:
                        break
                    optList = test
                    if endTime - startTime > TIME_LIMIT:
                        break
                    clang2BcOut = program[:-1] + 'bc'
                    codeError = code_pre + 'tmp_error.txt'
                    optOut = program[:-1]+ 'opt.bc'
                    optTimeout = report_pre + 'flags_opt_timeout' + str(bugCountsMap['opt_timeout']) + '.txt'
                    optCrash = report_pre+ 'flags_opt_crash' + str(bugCountsMap['opt_crash']) + '.txt'
                    clang2ExeOut = program[:-1] + 'out'
                    clang2ExeTimeout = report_pre + 'flags_clang2Exe_timeout' + str(bugCountsMap['clang2exe_timeout']) + '.txt'
                    clang2ExeCrash = report_pre + 'flags_clang2Exe_crash' + str(bugCountsMap['clang2exe_crash']) + '.txt'
                    exeOut = code_pre + 'res1'
                    resError = code_pre + 'error.txt'
                    exeTimeout = report_pre + 'flags_exe_timeout' + str(bugCountsMap['exe_timeout']) + '.txt'
                    exeCrash = report_pre + 'flags_exe_crash-' + str(bugCountsMap['exe_crash']) + '.txt'
                    miscompile = report_pre + 'flags_miscompile' + str(bugCountsMap['miscompile']) + '.txt'
                    bugType = compileExec(CLANG,'', '', '', clang2BcOut, '', '', '',
                                    OPT, optList, optOut, codeError, optTimeout, optCrash,
                                    '', clang2ExeOut, codeError, clang2ExeTimeout, clang2ExeCrash,
                                    exeOut, resError, exeTimeout, exeCrash,
                                    originalRes, miscompile,
                                    30)
                    if bugType != 'success':
                        bugCountsMap[bugType] += 1
                        bugTriggers = rtools.reduce_main(program,test,bugType)
                        tempList = []
                        for bugTrigger in bugTriggers:
                            if mapOpt.__contains__(bugTrigger):
                                tempList.append(mapOpt[bugTrigger])
                        if len(tempList)==0:
                            writeBug(bugRecord,program,' '.join(test),bugType)
                            continue
                        strNums=[str(x) for x in tempList]
                        if mapTuple.__contains__(','.join(strNums)):
                            continue
                        mapTuple[','.join(strNums)]=1
                        tupleList.append(tempList)
                        writeBug(bugRecord,program,' '.join(test),bugType)
                        cntt += 1            
                    print(bugType)
            endTime = time.time()

def getOpts():
    cmd = LLVM_PATH + 'llvm-as < /dev/null | ' + LLVM_PATH + 'opt -O3 -disable-output -debug-pass=Arguments 2>&1'
    optList = ctools.execmd(cmd).split('\n')[:2]
    optList = [optList[i][optList[i].index(':') + 3:] for i in range(len(optList))]
    optList = ' '.join(optList).split(' ')
    n = len(optList)
    for i in range(0,n):
        mapOpt[optList[i]]=(i+1)*(-1)
    return optList

if __name__ == '__main__':
    allOpts = getOpts()
    tests = genOptSet(SAMPLINGCA_Path, CNF_Path, PCA_Path, len(allOpts),allOpts)
    lmtools.gen_pcas()
    for i in range(1,2):
        t = CTCThread(i,1,1)
        t.start()