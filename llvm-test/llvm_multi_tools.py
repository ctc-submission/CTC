import tools.command_tools as ctools
import tools.LLVM_processor as LLVM
import tools.file_tools as ftools
import tools.list_tools as ltools
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
CNF_Path = '/home/ctc/llvm-test/example/csmith_mixed/pca/example_cnf.cnf'
PCA_Path = '/home/ctc/llvm-test/example/csmith_mixed/pca/example_pca.txt'
t_wise = 3
optionList = "/home/ctc/llvm-test/example/csmith_option/options.txt"

def generateProgram(CSMITH, opts, src,workDir):
    opt = ''
    for i in opts:
        opt = opt + ' ' + i
    cmd = CSMITH + ' ' + opt+'  > ' + src
    reval = ctools.execmd_with_status(cmd)
    if reval != 0:
        ctools.execmd("rm -rf "+src)
        return 1
    return 0
    


def generatePCA(SAMPLINGCA, input_path, output_path):
    ftools.gen_file(input_path)
    ftools.gen_file(output_path)
    cmd = SAMPLINGCA + ' -input_cnf_path ' + input_path + ' -output_testcase_path ' + output_path + ' -t_wise ' + str(
        t_wise)
    ctools.execmd(cmd)


def genOptCnf(csmith_len):
    ftools.delete_if_exists(CNF_Path)
    ftools.gen_file(CNF_Path)
    target = open(CNF_Path, 'w')
    cntt = 0
    target.write('p cnf ' + str(csmith_len) + ' ' + str(cntt) + '\n')
    target.close()


def get_negation(flag):
    if "function-attributes" in flag:
        return "--no-func-attributes"
    if "--no-signed-char-index" in flag:
        return ""
    if "--strict-float" in flag:
        return ""
    if "--no" not in flag:
        return flag[:2] + 'no-' + flag[2:]
    return flag[:2] + flag[5:]

def gen_pcas():
    f = open(optionList, "r")
    lines = f.readlines()
    opts = []
    for line in lines:
        if '|' in line:
            if '-enable-builtin-kinds' in line:
                continue
            s = ''
            pos = 0
            while line[pos] != '|':
                s += line[pos]
                pos += 1
            pos += 1
            t = ''
            while line[pos] != ':':
                t += line[pos]
                pos += 1
            opt = s.rstrip(" ")
            if opt[-1]=='\n':
                opt = opt[:-1]
            opts.append([opt, t])
    csmith_len = len(opts)
    genOptCnf(len(opts))
    generatePCA(SAMPLINGCA_Path, CNF_Path, PCA_Path)

def get_pcas():
    fca = open(PCA_Path, "r")
    lines2 = fca.readlines()
    res = []
    for line in lines2:
        if line[-1]=='\n':
            line = line[:-1]
        optList = line.split(' ')
        optList.remove(optList[len(optList) - 1])
        opts = []
        for i in range(0, len(optList)):
            idx = int(optList[i])
            opts.append(idx)
        res.append(opts)
    return res


def gen_programs(pre,CODE_Path):
    f = open(optionList, "r")
    lines = f.readlines()
    opts = []
    for line in lines:
        if '|' in line:
            if '-enable-builtin-kinds' in line:
                continue
            s = ''
            pos = 0
            while line[pos] != '|':
                s += line[pos]
                pos += 1
            pos += 1
            t = ''
            while line[pos] != ':':
                t += line[pos]
                pos += 1
            opt = s.rstrip(" ")
            if opt[-1]=='\n':
                opt = opt[:-1]
            opts.append([opt, t])
    csmith_len = len(opts)
    fca = open(PCA_Path, "r")
    lines2 = fca.readlines()
    cnt = 0
    codes = []
    for line in lines2:
        if line[-1]=='\n':
            line = line[:-1]
        optList = line.split(' ')
        optList.remove(optList[len(optList) - 1])
        opts2 = []
        for i in range(0, len(optList)):
            if i < csmith_len:
                idx = int(optList[i])
                s = opts[i][idx]
                if "--global-variables" in s:
                    s = ""
                opts2.append(s)
        src = CODE_Path + str(pre) + '-' + str(cnt) + '.c'
        wordDir = str(pre) + '-' + str(cnt)
        genMaxRounds = 10
        genSuccess = False
        for jj in range(0,genMaxRounds):
            b=generateProgram(CSMITH_Path, opts2, src,wordDir)
            if b == 1:
                continue
            else:
                genSuccess = True
                break
        if genSuccess==False:
            cnt += 1
            continue
        codes.append(src)
        cnt+=1
    codes_and_flags = [codes]
    return codes_and_flags
