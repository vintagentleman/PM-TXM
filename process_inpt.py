import os
import csv
import glob
import json
import time
from collections import OrderedDict
from xml.dom.minidom import getDOMImplementation

from nltk import word_tokenize
from pymorphy2 import MorphAnalyzer


class Profiler:
    def __enter__(self):
        self._startTime = time.time()

    def __exit__(self, type, value, traceback):
        print('Elapsed time: {:.3f} sec'.format(time.time() - self._startTime))


class Processor:

    def __init__(self, inpt_dir, otpt_dir, gold_path, coding):
        self.inpt_dir = inpt_dir
        self.otpt_dir = otpt_dir
        os.makedirs(self.otpt_dir, exist_ok=True)

        gold_file = open(gold_path, mode='r', encoding='utf-8', newline='')
        self.gold_reader = list(row for row in csv.reader(gold_file, delimiter=';') if int(row[3]) > 3)

        self.coding = coding
        self.morph = MorphAnalyzer()
        self.impl = getDOMImplementation()

        self.tr = ('?', '!', ';', '(', ')', '[', ']', '//')
        self.nt = ("'", "''", '"', '``', '«', '»', '„', '“', '“', '”', '‘', '’', '%')
        self.abbr = json.load(open('abbr.json', mode='r', encoding='utf-8'))
        self.prep = json.load(open('prep.json', mode='r', encoding='utf-8'))
        self.conj = json.load(open('conj.json', mode='r', encoding='utf-8'))
        self.tags = json.load(open('tags_inpt.json', mode='r', encoding='utf-8'))

    def format_parses(self, parses):

        for i, parse in enumerate(parses):
            result = OrderedDict()

            if i > 1:
                prev_word = parses[i - 1][0].normal_form
            else:
                prev_word = ''

            for j, item in enumerate(parse):
                pos = self.tags.get(item.tag.POS, '_')

                if pos != '_':
                    anim = self.tags.get(item.tag.animacy, '_')
                    case = self.tags.get(item.tag.case, '_')
                    num = self.tags.get(item.tag.number, '_')
                    gen = self.tags.get(item.tag.gender, '_')
                    pers = self.tags.get(item.tag.person, '_')
                    asp = self.tags.get(item.tag.aspect, '_')

                    if pos in ('Nn', 'Pn'):
                        if case != 'Ac':
                            anim = '_'

                        if num == 'Pl':
                            gen = '_'

                    elif pos == 'Vb':
                        if pers == '_' and num == 'Pl':
                            gen = '_'

                    if all(gram == '_' for gram in (anim, case, num, gen, pers, asp)):
                        result[pos] = item.normal_form
                    else:
                        result[','.join((pos, anim, case, num, gen, pers, asp))] = item.normal_form

                # Знаки препинания, числа, иностранные слова и прочее
                else:
                    pos = self.tags.get(str(item.tag).split(',')[0], '_')

                    if pos == 'PM':
                        try:
                            next_word = parses[i + 1][0].normal_form
                            next_pair = '%s %s' % (parses[i + 1][0].normal_form, parses[i + 2][0].normal_form)

                        # Терминал, если 1) в конце предложения
                        except IndexError:
                            if item.normal_form in self.nt:
                                result['PM,Nt,_'] = item.normal_form
                            else:
                                result['PM,Tr,_'] = item.normal_form

                        else:
                            # Терминал, если 2) в списке, 3) перед союзами
                            if item.normal_form in self.tr or next_word in self.conj['Sg'] or next_pair in self.conj['Db']:
                                result['PM,Tr,_'] = item.normal_form
                            # Нетерминал, если в списке
                            elif item.normal_form in self.nt:
                                result['PM,Nt,_'] = item.normal_form
                            # Точка - нетерминал, если а) после односимвольного токена или б) часть сокращения
                            elif item.normal_form == '.' and len(prev_word) == 1 or prev_word + item.normal_form in self.abbr:
                                result['PM,Nt,_'] = item.normal_form
                            # If all else fails, признаём неоднозначность
                            else:
                                for tag in ('PM,Nt,Tr', 'PM,Nt,_', 'PM,Tr,_'):
                                    result[tag] = item.normal_form

                    else:
                        result[pos] = item.normal_form

            for item in result:

                if not item.startswith('PM') and prev_word in self.prep:
                    new = [pair for pair in result.items() if any(cs in pair[0] for cs in self.prep[prev_word])]
                    if new:
                        result = OrderedDict(new)
                    break

                if item.startswith(('Pn', 'Pd', 'Cj', 'Pp', 'Pc')):
                    # Если местоимение или местоимение-предикатив,
                    # то отсекаем существительные и прилагательные-предикативы
                    if item.startswith(('Pn', 'Pd')):
                        new = [pair for pair in result.items() if not pair[0].startswith(
                            ('Nn', 'Ap')
                        )]
                    # Если союз, предлог или частица,
                    # то отсекаем существительные, прилагательные, местоимения и междометия
                    else:
                        new = [pair for pair in result.items() if not pair[0].startswith(
                            ('Nn', 'Aj', 'Ap', 'Pn', 'Pd', 'Ij')
                        )]

                    result = OrderedDict(new)
                    break

            yield result

    def process(self):

        def generate_log(*pairs):
            s = '{\n'

            for pair in pairs:
                s += '    %s: %s,\n' % pair

            s += '};\n'

            return s

        os.chdir(self.inpt_dir)
        print('Please wait. Python is processing your data...')

        for file in glob.glob('*.txt'):
            fo = open(file, mode='r', encoding=self.coding)
            doc = self.impl.createDocument(None, 'text', None)
            root = doc.documentElement

            # Словарь для статистики
            stat = {
                'breaks on start': 0,
                'regular breaks': 0,
                'breaks on end': 0,
                'fallbacks': 0,
                'terminals': 0
            }
            # Массив для фолбэков
            log_list = []

            for i, line in enumerate(fo.readlines()):
                # Массив токенов
                line_tokens = word_tokenize(line)
                # Массив упорядоченных словарей вида {разбор: лемма}
                line_parses = list(self.format_parses([self.morph.parse(token) for token in line_tokens]))

                p = doc.createElement('p')
                p.setAttribute('n', str(i + 1))

                previous = ''

                for j, parse_odict in enumerate(line_parses):
                    parses = list(parse_odict)

                    if parses[0].startswith('PM'):
                        elem = doc.createElement('pc')
                    else:
                        elem = doc.createElement('w')

                    elem_text = doc.createTextNode(line_tokens[j])
                    elem.appendChild(elem_text)

                    for row in self.gold_reader:
                        # Если текущий элемент - однозначно терминальный ЗП, то искать с ним триграмму бессмысленно
                        if parses[0] == 'PM,Tr,_':
                            elem.setAttribute('ana', 'PM,Tr,_')
                            elem.setAttribute('lemma', parse_odict['PM,Tr,_'])
                            previous = 'PM,Tr,_'
                            stat['terminals'] += 1

                        else:
                            # Если находимся в абсолютном начале предложения/чанка, рассматриваем левые биграммы
                            # Фолбэк к pymorphy2, только если текущий элемент последний в предложении
                            if j == 0 or previous == 'PM,Tr,_':
                                if j + 1 != len(line_parses):
                                    if row[0] in parses and row[1] in line_parses[j + 1]:
                                        elem.setAttribute('ana', row[0])
                                        elem.setAttribute('lemma', parse_odict[row[0]])
                                        previous = row[0]
                                        stat['breaks on start'] += 1

                            # Если текущий элемент последний в предложении, рассматриваем правые биграммы
                            elif j + 1 == len(line_parses):
                                if previous == row[1] and row[2] in parses:
                                    elem.setAttribute('ana', row[2])
                                    elem.setAttribute('lemma', parse_odict[row[2]])
                                    previous = row[2]
                                    stat['breaks on end'] += 1

                            # В других случаях рассматриваем полноценные триграммы
                            else:
                                if row[0] == previous and row[1] in parses and row[2] in line_parses[j + 1]:
                                    elem.setAttribute('ana', row[1])
                                    elem.setAttribute('lemma', parse_odict[row[1]])
                                    previous = row[1]
                                    stat['regular breaks'] += 1

                        if elem.hasAttributes():
                            break

                    # Фолбэк, если подходящей триграммы в золотом стандарте не нашлось
                    if not elem.hasAttributes():
                        # Фиксируем триграммы, на которых случился фолбэк
                        if j == 0 and len(line_tokens) == 1:
                            log_data = generate_log(
                                (line_tokens[j], parses)
                            )
                        elif j == 0:
                            log_data = generate_log(
                                (line_tokens[j], parses),
                                (line_tokens[j + 1], list(line_parses[j + 1]))
                            )
                        elif j + 1 == len(line_parses):
                            log_data = generate_log(
                                (line_tokens[j - 1], previous),
                                (line_tokens[j], parses)
                            )
                        else:
                            log_data = generate_log(
                                (line_tokens[j - 1], previous),
                                (line_tokens[j], parses),
                                (line_tokens[j + 1], list(line_parses[j + 1]))
                            )
                        log_list.append(log_data)

                        elem.setAttribute('ana', parses[0])
                        elem.setAttribute('lemma', parse_odict[parses[0]])
                        previous = parses[0]
                        stat['fallbacks'] += 1

                    p.appendChild(elem)
                root.appendChild(p)

            # Шагаем в выходную директорию
            os.chdir(self.otpt_dir)

            # Записываем в XML
            with open(file[:-3] + 'xml', mode='w', encoding='utf-8') as out:
                xml = doc.toprettyxml(indent='  ', encoding='utf-8')
                out.write(xml.decode())

            # Записываем фолбэки в лог-файл
            with open(file[:-4] + '_log.txt', mode='w', encoding='utf-8') as log:
                for line in log_list:
                    log.write(line + '\n')

            # Выдаём статистику по файлу
            print(file)
            for key in stat:
                print('    %d %s' % (stat[key], key))

            # Возвращаемся во входную директорию - к следующим файлам
            os.chdir(self.inpt_dir)
            doc.unlink()
            fo.close()


if __name__ == '__main__':
    try:
        with Profiler():
            Processor(os.getcwd() + '\\inpt', os.getcwd() + '\\otpt', 'trigrams.csv', 'windows-1251').process()
    except FileNotFoundError:
        print('Error: source file missing.')
