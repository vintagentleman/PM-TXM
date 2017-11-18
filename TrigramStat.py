import xml.etree.ElementTree as ET

class Trigram(object):
    def __init__(self, trigr, stat):
        self.trigr = trigr
        self.stat = stat
    def __repr__(self):
        return "%s;%s" % (self.trigr, self.stat)

def gettrigrames(file): #gettrigrames("LAW_PC.xml")
    tree=ET.parse(file)
    root=tree.getroot()
    testset=[]
    trgset=[]
    for n in range(100): #пробегаемся по всем предложениям в файле (пока по сотке)
        ts=""
        for elem in root[n]: #заменить потом на sentence!!!!! вытаскиваем все характеристики слов 
            if elem.tag=="w":
                ana=elem.get("ana")
                ts+=str(ana)+" "
            else: #и теги пунктуации
                if not elem.get("type")==None:
                    ts+=str(elem.tag)+","+str(elem.get("type")+ " ")
                else:
                    ts+=str(elem.tag)+" "
        splts=ts.split()
        for i in range(len(splts)-3): #вытаскиваем из предложения все возможные триграммы
            lim=i+3
            if splts[i]=="pc,Tr" or splts[i+1]=="pc,Tr": #удаляем нехорошие
                #print(splts[i:lim])
                continue
            else:
                trgline=str(splts[i:lim]).replace("'", "").replace("[", "").replace("]", "")   
                if trgline in testset:
                    #print(trgline)
                    testset.append(trgline)
                    stat=testset.count(trgline)
                    trigram=Trigram(trgline, stat)
                    flt=Trigram(trgline, stat-1)
                    #print(flt)
                    #print(trgset)
                    #if str(flt) in trgset: <----------вот тут короче вся хрень начинается
                    #потому что если просто написать trgset.remove(flt) (ну и ниже добавлять триграммы соответственно)
                    #то он радостно сообщит тебе, что нет там такого элемента (хотя он есть ><)
                        #print("lll")
                    trgset.remove(str(flt)) 
                else:
                    #print("trigram")
                    trigram=Trigram(trgline, 1)
                    testset.append(trgline)
                trgset.append(str(trigram))
    trgset.sort(key=lambda x: -int(x[x.index(";")+1:])) #и поэтому приходится делать так (постарайся не сильно шокироваться)
    return trgset

