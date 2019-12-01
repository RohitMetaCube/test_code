import csv


def create_new_file():
    f = open('/home/rohit/Downloads/YouTube-video-clean-1.7.2.csv', 'rb')
    fr = csv.reader(f)
    bad = 0
    f2 = open('/home/rohit/Downloads/YouTube-video-clean-1.7.4.csv', 'wb')
    fw = csv.writer(f2)
    for row in fr:
        if row[17] == "1" or row[17] == '11':
            bad += 1
            continue
        new_entry_data = row[:17] + row[18:19]
        fw.writerow(new_entry_data)
    print bad
    f2.close()
    f.close()


create_new_file()
