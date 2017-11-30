import os
# import glob
import xml.etree.ElementTree as ET
import csv


def get_trigrams(inpt_dir, file='ZHURGAZ.xml'):
    os.chdir(inpt_dir)
    # files = glob.glob('*.xml')
    trig_dict = {}

    # for file in files:
    tree = ET.parse(file)
    root = tree.getroot()

    # Пробегаемся по всем предложениям в файле
    for p in root:
        ts = ""

        for elem in p:
            # Вытаскиваем все характеристики слов
            if elem.tag == "w":
                ana = elem.get("ana")
                ts += str(ana)+" "
            # И теги пунктуации
            elif elem.tag == 'pc':
                ts += str(elem.tag) + "," + str(elem.get("ana") + " ")

        splts = ts.split()

        # Вытаскиваем из предложения все возможные триграммы
        for i in range(len(splts) - 3):
            lim = i + 3

            # Удаляем нехорошие
            if {"pc,Tr,_", "pc,Tr,Nt"} & {splts[i], splts[i + 1]}:
                continue
            else:
                trig_line = tuple(splts[i:lim])
                trig_dict.setdefault(trig_line, 0)
                trig_dict[trig_line] += 1

    # Это теперь не словарь, а список кортежей. Но это неважно
    trig_sort = sorted(trig_dict.items(), key=lambda x: -x[1])

    with open('trigrams.csv', mode='w', encoding='utf-8', newline='') as otpt:
        writer = csv.writer(otpt, delimiter=';')

        for pair in trig_sort:
            writer.writerow(list(pair[0]) + [pair[1]])


if __name__ == '__main__':
    try:
        get_trigrams(os.getcwd() + '\\otpt')
    except FileNotFoundError:
        print('Error: source file missing.')
