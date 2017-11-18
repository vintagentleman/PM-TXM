import os
from lxml import etree
import tags


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

    parser = etree.XMLParser(huge_tree=True)
    tree = etree.parse(inpt, parser)
    text = tree.getroot()
    otpt_tree = etree.Element('text')

    for par in text:
        p = etree.SubElement(otpt_tree, 'p')

        for node in par:
            if node.tag == 'w':
                w = etree.SubElement(p, 'w')
                ana = format_parse(node.get('gr').split(';'))

                w.text = node.text
                w.set('lemma', node.get('lex'))
                w.set('ana', ana)

            elif node.tag == 'pc':
                pc = etree.SubElement(p, 'pc')

                pc.text = node.text
                tp = node.get('type')
                if tp:
                    pc.set('type', tp)

    inpt.close()
    os.chdir(otpt_dir)

    with open(file, mode='w', encoding='utf-8') as otpt:
        xml = etree.tostring(otpt_tree, method='xml', encoding='utf-8', xml_declaration=True, pretty_print=True)
        otpt.write(xml.decode())


if __name__ == '__main__':
    try:
        process(os.getcwd() + '\\gold', os.getcwd() + '\\otpt', 'LAW_PC.xml')
    except FileNotFoundError:
        print('Error: source data directory missing.')
