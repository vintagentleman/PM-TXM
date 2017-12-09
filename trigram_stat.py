import os
import glob
import xml.etree.ElementTree as etree
import csv


def get_trigrams(inpt_dir, file=None):
    os.chdir(inpt_dir)
    print('Please wait. Python is processing your data...')
    trig_dict = {}

    if file is None:
        files = glob.glob('*.xml')
    else:
        files = [file]

    for file in files:
        tree = etree.parse(file)
        root = tree.getroot()

        # Пробегаемся по всем предложениям в файле
        for p in root:
            ts = ''

            for elem in p:
                # Вытаскиваем все характеристики слов и знаков пунктуации
                if elem.tag in ('w', 'pc'):
                    ts += str(elem.get('ana')) + ' '

            splts = ts.split()

            # Вытаскиваем из предложения все возможные триграммы
            for i in range(len(splts) - 3):
                lim = i + 3

                # Удаляем нехорошие
                if {'PM,Tr,_', 'PM,Tr,Nt'} & {splts[i], splts[i + 1]}:
                    continue
                else:
                    trig_line = tuple(splts[i:lim])
                    trig_dict.setdefault(trig_line, 0)
                    trig_dict[trig_line] += 1

    # Это теперь не словарь, а список кортежей
    trig_sort = sorted(trig_dict.items(), key=lambda x: -x[1])

    with open('trigrams.csv', mode='w', encoding='utf-8', newline='') as otpt:
        writer = csv.writer(otpt, delimiter=';')

        for pair in trig_sort:
            writer.writerow(list(pair[0]) + [pair[1]])


if __name__ == '__main__':
    try:
        get_trigrams(os.getcwd() + '\\otpt', 'ZHURGAZ.xml')
    except FileNotFoundError:
        print('Error: source file missing.')
