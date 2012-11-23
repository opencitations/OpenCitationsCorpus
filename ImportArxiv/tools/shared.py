import os
from unicodedata import normalize

def to_ascii(string):
    '''Converts a unicode string to ascii'''
    try:
        out = normalize('NFKD', string).encode('ascii','ignore')
    except TypeError:
        out = string
    return out
    

def group_generator(generator, size):
    count = 0
    end_flag = False
    while True:
        if end_flag: break
        batch = []
        while True:
            count += 1
            if count % (size + 1) == 0: break

            try:
                item = generator.next()
            except StopIteration:
                end_flag = True
                break

            batch.append(item)

        if not batch == []:
            yield batch


def yield_lines_from_dir(dir_name, extension='', remove=False):
    """
    Finds all flies in dir_name ending with extension, 
    and returns content as generator.
    """

    for file_name in os.listdir(dir_name):
        if not file_name.endswith(extension): continue

        fh = open(dir_name + file_name)
        for line in fh:
            yield line

        fh.close()
        if remove:
            os.remove(dir_name + file_name)


def yield_lines_from_file(file_name, remove=False):
    """
    Returns lines of file as an iterator.
    """

    fh = open(file_name)
    for line in fh:
        yield line

    fh.close()
    if remove:
        os.remove(dir_name + file_name)
