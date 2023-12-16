def execmd(cmd):
    import os
    pipe = os.popen(cmd)
    reval = pipe.read()
    print(cmd)
    return reval

def execmd_with_status(cmd):
    import os
    pipe = os.system(cmd)
    print(cmd)
    return pipe

def execmdNoOutput(cmd):
    import os
    pipe = os.popen(cmd)
    reval = pipe.read()
    return reval


def execmd_limit_time(cmd, limit):
    import time
    start = time.time()
    execmd("timeout " + str(limit) + " " + cmd)
    end = time.time()
    if (end - start) >= limit:
        return False
    else:
        return True
