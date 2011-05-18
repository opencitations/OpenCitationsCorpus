import os, heapq, sys
import csv, itertools, tempfile

def run(input_filename, output_filename):
    articles = iter(csv.reader(open(input_filename)))

    tempfiles = []

    exhausted = False
    while not exhausted:
        data = []
        for article in articles:
            data.append(article)
            if len(data) > 1000000:
                print "Stopping at %d." % len(data)
                break
        else:
            exhausted = True

        data.sort()
        f = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        tempfiles.append(f.name)
        csv.writer(f).writerows(data)
        f.close()

    out = csv.writer(open(output_filename, 'w'))

    streams = [csv.reader(open(fn)) for fn in tempfiles]
    out.writerows(heapq.merge(*streams))

    for fn in tempfiles:
        os.unlink(fn)

if __name__ == '__main__':
    run(*sys.argv[1:3])


