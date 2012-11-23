import os, heapq, sys
import itertools, tempfile

def run(input_filename, output_filename):
    lines = open(input_filename)

    tempfiles = []

    try:
        exhausted = False
        while not exhausted:
            data = []
            for line in lines:
                data.append(line)
                if len(data) > 1000000:
                    print "Stopping at %d." % len(data)
                    break
            else:
                exhausted = True

            data.sort()
            f = tempfile.NamedTemporaryFile(delete=False)
            tempfiles.append(f.name)
            f.writelines(data)
            f.close()

        out = open(output_filename, 'w')

        streams = [open(fn) for fn in tempfiles]
        out.writelines(heapq.merge(*streams))
    finally:
        for fn in tempfiles:
            os.unlink(fn)

if __name__ == '__main__':
    run(*sys.argv[1:3])


