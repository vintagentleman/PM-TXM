import os
import xml.etree.ElementTree as ET


def get_trigrams(inpt_dir, file):
    os.chdir(inpt_dir)

    tree = ET.parse(file)
    root = tree.getroot()
    trig_dict = {}

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
            if {"pc,Tr", "pc,Tr,Nt"} & {splts[i], splts[i + 1]}:
                continue
            else:
                trig_line = str(splts[i:lim]).replace("'", "").replace("[", "").replace("]", "")

                if trig_line in trig_dict:
                    trig_dict[trig_line] += 1
                else:
                    trig_dict[trig_line] = 1

    # Это теперь не словарь, а список кортежей. Но это неважно
    trig_sort = sorted(trig_dict.items(), key=lambda x: -x[1])

    with open('trigrams.txt', mode='w', encoding='utf-8') as otpt:
        for pair in trig_sort:
            otpt.write('%s;%s\n' % pair)


if __name__ == '__main__':
    try:
        get_trigrams(os.getcwd() + '\\gold', 'LAW.xml')
    except FileNotFoundError:
        print('Error: source file missing.')
