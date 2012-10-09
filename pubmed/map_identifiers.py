import csv

def run(input_filename, output_filename, mapping_filename):
    mapping = dict(csv.reader(open(mapping_filename)))

    reader = csv.reader(open(input_filename))
    writer = csv.writer(open(output_filename, 'w'))

    for row in reader:
        row = map(mapping.__getitem__, row[:2]) + row[2:]
        writer.writerow(row)
