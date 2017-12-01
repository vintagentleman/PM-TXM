import glob
import os
import nltk
import csv
from collections import OrderedDict
from xml.etree import ElementTree as etree
from xml.dom.minidom import parseString
from pymorphy2 import MorphAnalyzer
from tags import pymorphy_all
import conj


def format_tag(t):

    if t in pymorphy_all:
        return pymorphy_all[t]

    return '_'


def format_parse_list(parse_list):
    ana_list = []

    for i, parse in enumerate(parse_list):
        ana = OrderedDict()

        for j, item in enumerate(parse):
            pos = format_tag(item.tag.POS)

            if pos != '_':
                animacy = format_tag(item.tag.animacy)
                case = format_tag(item.tag.case)
                number = format_tag(item.tag.number)
                gender = format_tag(item.tag.gender)
                person = format_tag(item.tag.person)
                aspect = format_tag(item.tag.aspect)

                if pos == 'Nn':

                    if case != 'Ac':
                        animacy = '_'

                    if number == 'Pl':
                        gender = '_'

                elif pos == 'Vb':

                    if person == '_' and number == 'Pl':
                            gender = format_tag(item.tag.person)

                elif pos in ('Pt', 'Vp', 'Aj', 'Ap', 'Pn'):

                    if number == 'Pl':
                        gender = format_tag(item.tag.gender)

                if all(grammeme == '_' for grammeme in (animacy, case, number, gender, person, aspect)):
                    ana[pos] = item.normal_form
                else:
                    ana[','.join((pos, animacy, case, number, gender, person, aspect))] = item.normal_form

            # Знаки препинания, числа, иностранные слова и прочее
            else:
                pos = format_tag(str(item.tag).split(',')[0])

                if pos == 'PM':
                    try:
                        next_word = parse_list[i + 1][0].normal_form
                        next_pair = '%s %s' % (parse_list[i + 1][0].normal_form, parse_list[i + 2][0].normal_form)

                        # Терминал, если 1) в списке, 2) перед союзами
                        if item.normal_form in '?!;()[]//' or next_pair in conj.doub or next_word in conj.sing:
                            ana['pc,Tr,_'] = item.normal_form
                        # Нетерминал, если в списке
                        elif item.normal_form in '"%':
                            ana['pc,Nt,_'] = item.normal_form
                        # If all else fails, признаём неоднозначность
                        else:
                            for tag in ('pc,Nt,Tr', 'pc,Nt,_', 'pc,Tr,_'):
                                ana[tag] = item.normal_form

                    # Терминал, если 3) в конце предложения
                    except IndexError:
                        ana['pc,Tr,_'] = item.normal_form

                else:
                    ana[pos] = item.normal_form

        ana_list.append(ana)

    '''
    # Если мест.-пред., то отсекаем сущ.
    for ana in ana_list:
        for j, item in enumerate(ana):
            if item[0].startswith('Pd'):
                ana = ana[:j + 1] + [p for p in ana[j + 1:] if not p[0].startswith('Nn')]

    # Если союз, пред. или част., то отсекаем сущ., прил., мест. и межд.
    for ana in ana_list:
        for j, item in enumerate(ana):
            if item[0].startswith(('Cj', 'Pp', 'Pc')):
                ana = ana[:j + 1] + [p for p in ana[j + 1:] if not p[0].startswith(('Nn', 'Aj', 'Pn', 'Ij'))]
    '''

    return ana_list


def process(inpt_dir, otpt_dir, gold):
    # Создаём директорию с выходными данными на случай, если её нет
    os.makedirs(otpt_dir, exist_ok=True)
    # Если директории со входными данными нет, тут возбуждается исключение
    os.chdir(inpt_dir)
    # Если директория есть, всё в порядке - программа начинает работу
    print('Please wait. Python is processing your data...')

    morph = MorphAnalyzer()
    files = glob.glob('*.txt')

    gold_file = open(gold, mode='r', encoding='utf-8')
    gold_reader = csv.reader(gold_file, delimiter=';')

    # Файлы с текстами обрабатываем поштучно
    for file in files:
        f = open(file, mode='r', encoding='windows-1251')
        root = etree.Element('text')
        lines = f.readlines()

        # Массив для фолбэков
        logmass = []

        for line in lines:
            # Массив токенов
            line_tokens = nltk.word_tokenize(line)
            # Массив упорядоченных словарей вида {разбор: лемма}
            line_parses = format_parse_list([morph.parse(token) for token in line_tokens])

            p = etree.SubElement(root, 'p')
            prev_ana = ''

            for i, ana in enumerate(line_parses):
                parses = list(ana.keys())
                check = 0

                if parses[0].startswith('pc'):
                    elem = etree.SubElement(p, 'pc')
                else:
                    elem = etree.SubElement(p, 'w')
                elem.text = line_tokens[i]

                for row in gold_reader:
                    # Если текущий элемент - однозначно терминальный ЗП, то искать с ним триграмму бессмысленно
                    if parses[0] == 'pc,Tr,_':
                        elem.set('lemma', ana['pc,Tr,_'])
                        elem.set('ana', 'pc,Tr,_')

                        prev_ana = 'pc,Tr,_'
                        check += 1
                        break

                    else:
                        # Если находимся в абсолютном начале предложения/чанка, рассматриваем левые биграммы
                        if i == 0 or prev_ana == 'pc,Tr,_':

                            # Фолбэк к pymorphy2, если текущий элемент последний в предложении
                            if i + 1 == len(line_parses):
                                break
                            else:
                                if row[0] in parses and row[1] in line_parses[i + 1]:
                                    elem.set('lemma', ana[row[0]])
                                    elem.set('ana', row[0])

                                    prev_ana = row[0]
                                    check += 1
                                    break

                        # Если текущий элемент последний в предложении, рассматриваем правые биграммы
                        elif i + 1 == len(line_parses):
                            if prev_ana == row[1] and row[2] in parses:
                                elem.set('lemma', ana[row[2]])
                                elem.set('ana', row[2])

                                prev_ana = row[2]
                                check += 1
                                break

                        # В других случаях рассматриваем полноценные триграммы
                        else:
                            if row[0] == prev_ana and row[1] in parses and row[2] in line_parses[i + 1]:
                                elem.set('lemma', ana[row[1]])
                                elem.set('ana', row[1])

                                prev_ana = row[1]
                                check += 1
                                break

                # Фолбэк, если подходящей триграммы в золотом стандарте не нашлось
                if not check:
                    elem.set('lemma', ana[parses[0]])
                    elem.set('ana', parses[0])

                    # Фиксируем триграммы, на которых случился фолбэк
                    if i == 0:
                        logstring = "[\n" + str(line_tokens[i]) + " : " + str(parses) + ";\n" + str(line_tokens[
                            i + 1]) + " : " + str(list(line_parses[i + 1].keys())) + "\n]\n"
                    elif i + 1 == len(line_parses):
                        logstring = "[\n" + str(line_parses[i - 1]) + " : [" + str(
                            prev_ana) + "];\n" + str(line_tokens[i]) + " : " + str(parses) + "\n]\n"
                    else:
                        logstring = "[\n" + str(line_tokens[i - 1]) + " : [" + str(
                            prev_ana) + "];\n" + str(line_tokens[i]) + " : " + str(parses) + ";\n" + str(line_tokens[
                                        i + 1]) + " : " + str(list(line_parses[i + 1].keys())) + "\n]\n"

                    logmass.append(logstring)

                    prev_ana = parses[0]

        # Шагаем в выходную директорию
        os.chdir(otpt_dir)

        # Записываем в XML
        with open(file[:-3] + 'xml', mode='w', encoding='utf-8') as out:
            xml = etree.tostring(root, method='xml', encoding='utf-8')
            pretty = parseString(xml).toprettyxml(indent='  ', encoding='utf-8')
            out.write(pretty.decode())

        # Записываем лог-файл
        with open(file[:-4] + "_log_trg.txt", mode="w", encoding="utf-8") as log:
            for line in logmass:
                log.write(str(line) + "\n")

        # Возвращаемся во входную директорию - к файлам на очереди
        os.chdir(inpt_dir)
        f.close()

    gold_file.close()


if __name__ == '__main__':
    try:
        process(os.getcwd() + '\\inpt', os.getcwd() + '\\otpt', 'ALL_trigrams.csv')
    except FileNotFoundError:
        print('Error: source data directory missing.')
