#
# Text file comment queue
#
# Provides functions to:
# * get  = read out first non-commented line
# * pop  = read out first non-commented line and comment it in afterwards
# * push = append a line to the file
#


def queue(file_name):
    while True:
        item = pop(file_name)
        if item is None:
            break

        yield item


def push(file_name, line):
    with open(file_name,'a') as fh:
        fh.write(line+"\n")

def get(file_name):
    with open(file_name) as fh:
        for line in fh:
            if has_comment(line):
                continue
            return rm(line)
    
    return None

def pop(file_name):
    with open(file_name) as fh:
        lines = fh.readlines()
    
    out = None
    with open(file_name,'w') as fh:
        for line in lines:
            if out is None and not has_comment(line):
                out = line
                line  = "# " + line

            fh.write(line)

    return rm(out)



def has_comment(line):
    if line.strip()[0] == '#':
        return True

    return False

def rm(line):
    # carfully remover last letter
    if not type(line) is str:
        return line
    if line == '':
        return ''

    return line[:-1]
    
