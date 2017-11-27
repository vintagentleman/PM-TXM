import os
import re
from lxml import etree
import tags
import conj


def format_text(s):
    # Стандартизируем отступы
    s = re.sub(r' {4}\s+', '    ', s)

    # Неоднозначные ЗП: точка, запятая, двоеточие, тире
    # Учитываются сочетания ЗП слева типа (крайний случай) ..."),
    # а также повторения самого знака (до трёх)
    s = re.sub(r' {4}([.?!]{0,3}[(")[\]]{0,2}[.,:-]{1,3})(?=[\n\r])', '    <pc ana="Nt,Tr">\\1</pc>', s)

    # Однозначно терминальные ЗП: вопросительный и восклицательный знаки, точка с запятой и скобки
    # Могут быть заключены в кавычки; сами могут вступать в комбинации (длиной до трёх символов)
    s = re.sub(r' {4}("?[?!;()[\]]{1,3}"?)(?=[\n\r])', '    <pc ana="Tr,_">\\1</pc>', s)

    # Единственный однозначно нетерминальный ЗП - кавычка
    s = re.sub(r' {4}(")(?=[\n\r])', '    <pc ana="Nt,_">\\1</pc>', s)

    # Сокращения и прочее
    s = re.sub(r' {4}((в|вв|г|др|пр)\.)(?=[\n\r])', '    <w lex="\\1" gr="S,inan,|gender,|case,|number">\\1</w>', s)
    s = re.sub(r' {4}(т\. ?к\.)(?=[\n\r])', '    <w lex="\\1" gr="CONJ">\\1</w>', s)
    s = re.sub(r' {4}(\w\s*\))', '    <w lex="\\1" gr="NONLEX">\\1</w>', s)

    # Всё, что осталось, оформляем как glyph
    s = re.sub(r' {4}(?!<)(.+)', '    <g>\\1</g>', s)

    return s


def format_tag(ps, ts):
    for t in ps:
        if t in ts:
            return ts[t]

    return '_'


def format_parse(pt):
    ana = []

    for parse in pt:
        p_set = parse.split(',')
        pos = format_tag(p_set, tags.gold_pos)

        animacy = format_tag(p_set, tags.gold_animacy)
        case = format_tag(p_set, tags.gold_case)
        number = format_tag(p_set, tags.gold_number)
        gender = format_tag(p_set, tags.gold_gender)
        person = format_tag(p_set, tags.gold_person)
        aspect = format_tag(p_set, tags.gold_aspect)

        if pos == 'Nn':

            if case != 'Ac':
                animacy = '_'

            if number == 'Pl':
                gender = '_'

        elif pos == 'Vb':

            if 'inf' in p_set:
                pos = 'If'
            elif 'partcp' in p_set:
                if 'plen' in p_set:
                    pos = 'Pt'
                else:
                    pos = 'Vp'
            elif 'ger' in p_set:
                pos = 'Dp'

            if person == '_' and number == 'Pl':
                gender = '_'

        elif pos == 'Aj':

            if 'brev' in p_set:
                pos = 'Ap'

            if number == 'Pl':
                gender = '_'

        elif pos == 'Pn':

            if number == 'Pl':
                gender = '_'

        elif pos == 'Nu':

            if 'comp' in p_set:
                pos = 'Cm'

        if all(grammeme == '_' for grammeme in (animacy, case, number, gender, person, aspect)):
            ana += [pos]
        else:
            ana += [','.join((pos, animacy, case, number, gender, person, aspect))]

    return ';'.join(ana)


def process(inpt_dir, otpt_dir, file):
    os.makedirs(otpt_dir, exist_ok=True)
    os.chdir(inpt_dir)
    inpt = open(file, mode='r', encoding='utf-8')
    print('Please wait. Python is processing your data...')

    text = format_text(inpt.read())

    parser = etree.XMLParser(huge_tree=True)
    root = etree.fromstring(text, parser)
    otpt_tree = etree.Element('text')
    glyph_log = ''

    for i, par in enumerate(root):
        p = etree.SubElement(otpt_tree, 'p')
        p.set('n', str(i + 1))

        for j, node in enumerate(par):
            try:
                next_node = par[j + 1]
                next_pair = (par[j + 1], par[j + 2])

                if node.tag == 'pc':
                    pc = etree.SubElement(p, 'pc')
                    pc.text = node.text

                    # Если следующий узел - союз из списка Арины, то это терминал
                    if (next_node.get('gr') == 'CONJ' and next_node.get('lex') in conj.sing
                            or (next_pair[0].get('lex'), next_pair[1].get('lex')) in conj.doub):
                        pc.set('ana', 'Tr,_')
                    # If all else fails, признаём неоднозначность
                    else:
                        pc.set('ana', node.get('ana'))

            # Если возбуждается исключение, то мы дошли до (пред)последнего узла
            # Если это знак препинания, то это определённо терминал
            except IndexError:
                if node.tag == 'pc':
                    pc = etree.SubElement(p, 'pc')
                    pc.text = node.text
                    pc.set('ana', 'Tr,_')

            finally:
                if node.tag == 'w':
                    w = etree.SubElement(p, 'w')
                    ana = format_parse(node.get('gr').split(';'))

                    w.text = node.text
                    w.set('lemma', node.get('lex'))
                    w.set('ana', ana)

                elif node.tag == 'g':
                    g = etree.SubElement(p, 'g')
                    g.text = node.text

                    # Висячие символы попутно фиксируем
                    glyph_log += '%d\t%s\n' % (i + 1, g.text)

    inpt.close()
    os.chdir(otpt_dir)

    with open(file, mode='w', encoding='utf-8') as otpt:
        xml = etree.tostring(otpt_tree, method='xml', encoding='utf-8', xml_declaration=True, pretty_print=True)
        otpt.write(xml.decode())

    with open('glyph_log.csv', mode='w', encoding='utf-8') as log:
        log.write(glyph_log)


if __name__ == '__main__':
    try:
        process(os.getcwd() + '\\gold', os.getcwd() + '\\otpt', 'LAW.xml')
    except FileNotFoundError:
        print('Error: source data directory missing.')
