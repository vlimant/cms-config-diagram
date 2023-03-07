#! /usr/bin/env python

INVERT=False
INCLUDEES=True

import FWCore.ParameterSet.Config as cms
import os, re, sys, random
import optparse


#return (t== "MixedLayerPairsESProducer" or t == "PixelLayerTripletsESProducer" or t == "PixelLessLayerPairsESProducer" or  t=="TobTecLayerPairsESProducer"  or t== "SeedingLayersESProducer")
def islayerES(t):
    return (t.find("MixedLayerPairsESProducer")!=-1 or t.find("PixelLayerTripletsESProducer")!=-1 or t.find("PixelLessLayerPairsESProducer")!=-1 or  t.find("TobTecLayerPairsESProducer")!=-1  or t.find("SeedingLayersESProducer")!=-1)


def var(i,st, something):
    print("%s %s = %s" % (i,st,something.value()))
    

class ModuleExplained:
    nameList = []

def listObject(item,i):
    list=[]
    #print item.__str__()
    if (hasattr(item,"label") and i!=0):
        #print item.label()
        list.append(item.label())
        return list
    else:
        if (hasattr(item,"_seq")):
            #print "descending _seq:"
            if (hasattr(item._seq,"_right")):
                list.extend(listObject(item._seq._right,i+1))
            else:
                list.append(item.label())
            if(hasattr(item._seq,"_left")):
                list.extend(listObject(item._seq._left,i+1))
            else:
                list.append(item.label())                
            return list
        else:
            #print "descending :"
            if (hasattr(item,"label")):
                list.append(item.label())
                return list
            else:
                if (hasattr(item,"_right")):
                    list.extend(listObject(item._right,i+1))
                else:
                    print( item,"does not have a _right")
                if (hasattr(item,"_left")):
                    list.extend(listObject(item._left,i+1))
                else:
                    print( item,"does not have a _left")
                return list
    return list

def listObjectInSequence(sequence):
    l=listObject(sequence,0)
    l.reverse()
    #print l
    return l

def everyModuleInSequence(sequence):
    list=[]
    for item in listObjectInSequence(sequence):
        list.extend(listObjectInSequence(getattr(process,item)))
    if (sequence.label() in list):
        list.remove(sequence.label())
    return list

    
def alreadyExplained(l):
    if l in ModuleExplained.nameList:
        #for m in ModuleExplained.nameList:
        #if (m == l):
        #print "%s alredy explained above" % (l)
        return True
    else:
        ModuleExplained.nameList += [ l ]
        return False

DeclaredModules = {}
DeclaredDeps = []

InputModules = set()
OutputModules = set()

def declareSelf(me, myself):
    DeclaredModules[me] = myself

def declareDep(me, what, why=None):
    #if not DeclaredModules.has_key(what): DeclaredModules[what] = None
    if not what in DeclaredModules.keys(): DeclaredModules[what] = None
    DeclaredDeps.append( (me,what,why) )

#def splitAll(str,patterns):
#    listofitems=[]
#    for pat in patterns:
        
    
def makeGraphViz(modules,deps,file):
    dot = open(file,'w');
    dot.write("digraph G { \n")
    dot.write("fontsize=3\n")
    dot.write("rankdir=LR\n")
    #dot.write("nodesep=0.1\n")
    dot.write("nodesep=1\nranksep=2\n")
    dot.write("ranksep=2\n")
    #dot.write("rankdir=TB\nranksep=2\n")
    #dot.write("rankdir=LR\nranksep=3\n")
    dot.write("concentrate=true\n")
#dot.write("ranksep=equally\n")

    #dot.write("page='10,10'\n")

    #dot.write("esep=3\n")
    #dot.write("len=3\n")
    #dot.write("mode=KK\n")
    #dot.write("maxiter=200000\n")
    
    subG = { 'Input' : InputModules,
             'Output' : OutputModules
         }
    alreadyInserted = set()
    for subG_l,subG_set in list(subG.items())+[('process',None)]:
        if subG_set is not None:
            dot.write("subgraph %s {\nlabel = %s\n"%(subG_l, subG_l))
            dot.write("style=filled\n")
            #dot.write("cluter=true\n")
            dot.write("color=lightgrey\n")
        for (ml,obj) in modules.items():
            if (ml==""): continue
            ## skip modules not in the subgraph
            if subG_set is not None and ml not in subG_set: continue
            if ml in alreadyInserted: continue
            alreadyInserted.add(ml)
            label=ml
            if obj != None: label = '%s\\n%s' % (ml, obj.type_())
            shape='rect'
            color='fillcolor=white'
            style='filled'

            if 'DummyModuleProbablyAnInput' in label:
                shape='folder'
                color='fillcolor=grey color=black'

            dot.write("%s [ shape=%s style=\"%s\" %s label=\"%s\" URL=\"#%s\"]\n" % (ml,shape,style,color,label,ml))
        #closing the subgraph
        if subG_set is not None:
            dot.write("}\n")
    UsedColors=["green","blue","red","orange","crimson","violet","peru","purple","gray","navy","blue3","red3"]
    for mod,dep,why in deps:
        To=""
        From=""
        #Label="label=''"
        Label=""
        Style="style=bold"
        Color="color=%s"%(UsedColors[random.randint(0,UsedColors.__len__()-1)],)
        if why != None:
            if (why =="ES"):
                Style="style=dashed"
            else:
                Label="label='%s'," % (why,)
                
        if (INVERT):
            From=dep
            To=mod
        else:
            From=mod
            To=dep
                
        dot.write("%s -> %s [%s %s, %s]\n" % (From,To,Label,Style,Color) )

    if (False):
        #make clusters within the diagram
        #dot.write("subgraph localreco1{ siStripClusters;siPixelClusters; }\n")
        #dot.write("subgraph localreco2{  }\n")
    
        nsub=-1
        for sk in process.sequences_().keys():
            doSubGraph=False
            itemsInSequence=listObjectInSequence(getattr(process,sk))
            for item in itemsInSequence:
                #check that the sequence contains a module explained
                if (item in ModuleExplained.nameList):
                    doSubGraph=True
                    break
            #check that all module in the sequence contain a module explained
            all=everyModuleInSequence(getattr(process,sk))
            #print sk,"contains module:",all
            for item in all:
                #check that the sequence contains a module explained
                if (item in ModuleExplained.nameList):
                    doSubGraph=True
                    break

            if (not doSubGraph):
                continue

            print( sk,"maybe be considered for clustering",all)
            
            nsub=nsub+1
            dot.write("subgraph cluster_%s{\n"%(sk,))
            dot.write('label="%s";\n'%(sk,))
            dot.write('colo=lightgrey;\n')
            dot.write('style=filled; \n')
            

            #dot.write('color=%s;\n'%(UsedColors[random.randint(0,UsedColors.__len__()-1)]))             #the color could interfere with the arrows
            #write the cluster content
            for item in itemsInSequence:
                #item can be a module name
                if (item in ModuleExplained.nameList):
                    dot.write("%s;\n"%(item,))
                else:
                    # or a sequence name
                    allForItem=everyModuleInSequence(getattr(process,item))
                    if (allForItem.__len__()<=1):
                        continue
                    print( allForItem)
                    for checkitem in allForItem:
                        if (checkitem in ModuleExplained.nameList):
                            dot.write("%s;\n"%(item,))
                            break
                        

            #write clusters arrows
            if (itemsInSequence.__len__()!=1):
                for iItem in range(0,itemsInSequence.__len__()-1):
                    FROM=itemsInSequence[iItem]
                    TO=itemsInSequence[iItem+1]
                    #if (FROM in process.sequences_.keys() or TO in process.sequences_.keys()):
                        
                    if ((not FROM in ModuleExplained.nameList) and (not TO in ModuleExplained.nameList)):
                        dot.write("%s -> %s [style=filled] \n"%(itemsInSequence[iItem],itemsInSequence[iItem+1]))

            #sub graph closing
            dot.write("}\n")
            
            #for what in process.sequences_()[sk].__str__().split("*"):
            #        if (what.find("+")!=-1 or what.find(")")!=-1 or what.find("(")!=-1):
            #            #a sub sequence
            #            print what,'contains sub modules'
            #            #for subwhat in what.split("+"):
            #            #    dot.write("%s;\n"%(subwhat,))
            #        else:
            #            dot.write("%s;\n"%(what,))
            #    #sub graph closing
            #    dot.write("}\n")

    #master closing
    dot.write("}\n");    
    dot.close()

def tryLink(match):
    lbl = match.group(2)
    #if DeclaredModules.has_key(lbl) and DeclaredModules[lbl] != None:
    if lbl in DeclaredModules.keys() and DeclaredModules[lbl] != None:
        return "%s<a href=\'#%s\'>%s</a>%s" % (match.group(1), lbl, lbl, match.group(3))
    else:
        isEs=isAPossibleESObject(lbl)
        if (isEs[0]):
            #print "MAKING A LINK USING",isEs[1][0]
            return "%s<a href=\'#%s\'>%s</a>%s" % (match.group(1), isEs[1][0], lbl, match.group(3))
        else: return match.group(0)
    
def pyWithLink(x):
    str = x.dumpPython()
    str = re.sub(r'(cms.(?:untracked.InputTag|untracked.string|InputTag|string|vstring)\(.)(\w+)(.*?\))', tryLink, str)
    # replace the module class name to a link to LXR ?
    className=str.split(',')[0].split('"')[1]
    rel=os.environ['CMSSW_VERSION']
    shortRel='_'.join(rel.split('_')[0:4])
    #print shortRel
    #LXRLink='<a href="http://cmslxr.fnal.gov/lxr/ident?v=%s&i=%s">%s</a>'%(shortRel,className,className)
    LXRLink='<a href="https://cmssdt.cern.ch/lxr/ident?v+%s&_i=%s">%s</a>'%(shortRel,className,className)
    #GHLink='<a href="https://github.com/cms-sw/cmssw/search?q=%s>%s</a>'%(className,className)
    str=str.replace('%s'%(className,),LXRLink)
    return str

def feedsThoseModules(m,deps):
    #look for all modules that depend on this one
    linksToFed=""
    for mod,dep,why in deps:
        if (dep==m):
            linksToFed+=("<a href=\'#%s\'>%s</a>, "%(mod,mod))
    if (linksToFed!=""):
        linksToFed="Is used by "+linksToFed
    return linksToFed
    #return "moreInformationHere\n"

def makeHTML(modules,deps,file='generalTracks.html'):
    dFile=file.replace(".html",".dot")
    pFile=file.replace(".html",".png")
    #mFile=file.replace(".html","_outputNodes.py")
    makeGraphViz(modules,deps,dFile)

    G="dot"
    #G="neato"
    
    os.system(G+" -Tpng -o "+pFile+" < "+dFile)

    html = open(file,'w')
    html.write("""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">""");
    html.write('<head>  <title>Configuration Organigram in %s</title>\n'%(os.environ['CMSSW_VERSION']),)
    html.write("""    <style type='text/css'>
        </style>
</head>
<body> <h1>Graphical Representation of Configuration</h1>""");
    html.write("<br><hr><br>")
    html.write("""
<align='center'><img src="""+pFile+""" usemap="#G" />""");
    map = os.popen(G+" -Tcmapx < "+dFile, "r");
    topShift=-400
    leftShift=400
    theTextForBackLinks=""
    #create the back links to the areas
    for l in map.readlines():
        html.write(l)
        if (l.find("area")!=-1):
            #print(l)
            spl=l.split(" ")
            #tag='map'+spl[2].split("=")[1].replace('"','').replace('#','')
            #tag='map'+spl[3].split("=")[1].replace('"','').replace('#','')
            tag='map'+[it for it in spl if it.startswith('href=')][0].split("=")[1].replace('"','').replace('#','')
            #tag='map'+[it for it in spl if it.startswith('id=')][0].split("=")[1].replace('"','').replace('#','')
            #print(spl)
            #coord=spl[5].split("=")[1].replace('"','')
            #coord=spl[-1].split("=")[1].replace('"','')
            coord=[it for it in spl if it.startswith('coords=')][0].split("=")[1].replace('"','')
            coords = coord.split(",")[:2]
            #print(coords)
            #top=topShift+int(coord.split(",")[1])
            top=topShift+int(coords[1])
            #left=leftShift+int(coord.split(",")[0])
            left=leftShift+int(coords[0])
            ## the below is an anchor for #map<name of module>
            theTextForBackLinks+="<span style='VISIBILITY:visible;FLOAT:none;position:absolute;top:%dpx;left:%dpx;z-index:2'><a id='%s'></a></span>\n"%(top,left,tag)
    map.close()
    html.write("<div>\n")
    html.write(theTextForBackLinks)
    html.write("</div>\n")               
    for (ml,obj) in modules.items():
        if obj == None: continue
        #moduleList.write('\t"keep *_'+ml+'_*_*",\n')
        #print "I am looking at: ",ml
        html.write("""<h3><a href="%s" name="%s" id="%s">%s</a></h3>%s<pre>%s</pre>""" % ('#map'+ml,ml,ml,ml,feedsThoseModules(ml,deps),pyWithLink(obj)))

    html.write("configuration used\n")
    #if cfg!='':
    #    cfgFile=open(cfg+'.py','r')
    #    for line in cfgFile:
    #        html.write(line.replace('\n','<BR>'))
    #    cfgFile.close()
    html.write("<br><hr><br>")

    html.write("""
</body>
</html>""")
    html.close();
    #moduleList.write(']\n')
    #moduleList.close()

def listAllInputParameters(module):
    listOfInput={}
    for parameterName in module.parameters_().keys():
        cmsParameter = getattr(module,parameterName)
        parameterType = cmsParameter.pythonTypeName()
        ## we do not want strings to define possible input : which means no ESproducer possible here
        #if (parameterType == 'cms.string' or parameterType == 'cms.untracked.string'):
        #    #print "parameter:",parameterName,"is a string:"
        #    #one exception though
        #    if (parameterName=="alias"):
        #        print( "alias is a string, not an input")
        #    else:
        #        listOfInput[cmsParameter.value()]=parameterName
        #el
        if (parameterType == 'cms.InputTag' or parameterType == 'cms.untracked.InputTag'):
            #print "parameter:",parameterName,"is an inputtag:"
            src_ = cmsParameter.moduleLabel
            if src_ and (not '%' in src_):
                listOfInput[src_]=parameterName
        elif (parameterType == 'cms.VInputTag'):
            #print "parameter:",parameterName,"is a vector of inputtag:"
            for i in cmsParameter:
                src_=i.moduleLabel if hasattr(i,"moduleLabel") else i
                src_=src_.split(":")[0]
                if src_ and (not '%' in src_):
                    listOfInput[src_]=parameterName

        elif (parameterType == 'cms.PSet' or parameterType == 'cms.untracked.PSet'):
            listOfInput.update(listAllInputParameters(cmsParameter))
        elif (parameterType == 'cms.VPSet' or parameterType == 'cms.untracked.VPSet'):
            for pset in cmsParameter:
                listOfInput.update(listAllInputParameters(pset))
    return listOfInput



def isAPossibleESObject(name):
    possibleEses=[]
    for esProd in process.es_producers_().keys():
        if (esProd == name):
            possibleEses.append(esProd)
        else:
            es=getattr(process,esProd)
            if (hasattr(es,"ComponentName")):
                if (es.ComponentName.value() == name):
                    possibleEses.append(esProd)
        #else:
            #print esProd,"has no component name"
            #print es

    return [possibleEses.__len__()!=0,possibleEses]
            

def p(l,i="",dummy=False):
    global globalAllModule
    if ( l != ""):
        if (alreadyExplained(l)):
            return

        if (l=='rawDataCollector' or l =='source' or dummy):
            print("declaring dummy module",l)
            x=cms.EDProducer("DummyModuleProbablyAnInput")
            declareSelf(l,x)
            InputModules.add(l)
            return
        
        if (not hasattr(process,l)):
            ## this is likely a product from the input file
            print("ERROR There is no module ",l," in the proces")
            x=cms.EDProducer("DummyModuleProbablyAnInput")
            declareSelf(l,x)
            InputModules.add(l)
            return

        x = getattr(process,l)
        declareSelf(l,x)
        if x.type_().endswith('TableProducer'):
            OutputModules.add(l)

        listOfInput = listAllInputParameters(x)
        #print l,"seems to depend on",listOfInput
        #loop this list and find whether this is a ed module or not
        for possibleInput in listOfInput.keys():
            #print(possibleInput,"is a possible input to",l)
            if (possibleInput==l):
                continue
            isInSchedule=(possibleInput in globalAllModule)
            isInProcess=hasattr(process,possibleInput) and possibleInput in (list(process.producers_().keys())+list(process.filters_().keys()))
            isAnInputTag=True ##to be updated later on to be able to parse ESProducer dependency
            #if (isInProcess and (possibleInput in (list(process.producers_().keys())+list(process.filters_().keys())))):
            if (isAnInputTag):
                declareDep(l,possibleInput)
                p(possibleInput,i+"    ",(not isInSchedule) or (not isInProcess))
                #elif (possibleInput =='rawDataCollector' or possibleInput =='source'):
                #    declareDep(l,possibleInput)
                #    p(possibleInput,i+"    ")
            else:
                #print possibleInput,'is said to be a possibleInput'
                if (INCLUDEES):
                    possibleES=isAPossibleESObject(possibleInput)
                    if (possibleES[0]):
                        if (possibleES[1].__len__()==1):
                            #no confusion on the ES object producer
                            if (possibleES[1][0]!=l):
                                #not himself
                                esName=possibleES[1][0]
                                #print esName,'is the es object it depends on'
                                declareDep(l,esName,"ES")
                                p(esName,i+"    ")
                        else:
                            #possible confusion on the es producer, because there is more than one.
                            if (listOfInput[possibleInput] == 'MeasurementTrackerName'):
                                #print 'we have a dependency on a measurement tracker with label ""'
                                declareDep(l,'MeasurementTracker',"ES")
                                p('MeasurementTracker',i+"    ")
                            else:
                                print( 'ERROR: will not be able to determine the orign of empty string parameter for module',l,'parameter name',listOfInput[possibleInput])
                        
                #else:
                    #print l,"cannot really depend on",possibleInput,"because it's not a producer a filter or an es object"
                #print x.parameters_()
            
            


def allModules(process):
    return list(process.schedule.moduleNames())
    #list all possible modules
    allPossibleModules=(list(process.filters_().keys())+list(process.producers_().keys())+list(process.analyzers_().keys()))

    inSchedule=[]
    #check that scehdule is defined if ever that crashes
    for m in allPossibleModules:
        pattern=m+'[*+,)]'
        match=re.search(pattern,process.schedule.__str__())
        if match:
            inSchedule.append(m)
        #index=process.schedule.__str__().find(m)
        #if (index!=-1):
        #    nextChar=process.schedule.__str__()[index+m.__len__():index+m.__len__()+1]
        #    if m=='towerMaker':
        #        print m,index,nextChar,process.schedule.__str__()[index:index+20]
        #        pattern=m+'[*+,)]'
        #        match=re.search(pattern,process.schedule.__str__())
        #        if match:
        #            print match.groups()
        #                
        #    if (nextChar == '+' or nextChar == '*' or  nextChar == ')' or nextChar == ','):
        #        inSchedule.append(m)
    print("found",len(allPossibleModules),"possible modules, and",len(inSchedule),"in schedule")
    return inSchedule



def allModulesByType(process,types):
    all=allModules(process)
    selected=[]
    for m in all:
        module=getattr(process,m)
        if module._TypedParameterizable__type in types:
            selected.append(m)
    return selected



def explainOnlyCertainModules(endUserModules):

    for endUserModule in endUserModules:
        print("-------")
        print( "doing the dependencies for",endUserModule        )
        p(endUserModule)

    print("+++++++++++++++++++++++++++")
    global globalAllModule
    #allMod=allModules(process)
    allMod=globalAllModule

    uselessMod=[]
    for m in allMod:
        if m not in ModuleExplained.nameList:
            #print( 'module',m,'does not seem to have been included anywhere')
            uselessMod.append(m)
    print("+++++++++++++++++++++++++++")
    global options
    if options.dumpCfg!="":

        if not options.fullDump:
            dump=open(options.dumpCfg,'w')
            initialCfg=open(options.cfg,'r')
            for line in initialCfg:
                dump.write(line)
            dump.write('\n')
            dump.write('process.dummyModule = cms.EDProducer("DummyModule")\n')
            initialCfg.close()
        
        process.dummyModule = cms.EDProducer("DummyModule")
        for m in uselessMod:
            if hasattr(process,m):
               #print "removing",m
               mod=getattr(process,m)
               try:
                   process.reconstruction_step.replace(mod,
                                                       process.dummyModule)
                   if not options.fullDump:
                       dump.write('process.reconstruction_step.replace(process.%s,process.dummyModule)\n'%(m,))
                   
               except:
                   print( "tried but cannot remove",m)
            else:
                print( "cannot remove",m)
        if options.fullDump:
            dump=open(options.dumpCfg,'w')
            dump.write(process.dumpPython())
        dump.close()

def explainAllModulesWith(expL):
    for endUserModule in allModules(process):
        for exp in expL:
            if (endUserModule.find(exp)!=-1):
                print( "-------")
                print( "doing the dependencies for",endUserModule        )
                p(endUserModule)
                break

def explainAllModules():
    for endUserModule in allModules(process):
        print( "-------")
        print("doing the dependencies for",endUserModule        )
        p(endUserModule)

productRECODoesNotCareAbout=["edmTriggerResults","triggerTriggerEvent","L1AcceptBunchCrossings","L1TriggerScalerss","Level1TriggerScalerss","LumiScalerss"]

def explainFromOutputDefinition():
    global globalAllModule
    #allMod=allModules(process)
    allMod=globalAllModule

    #do the output module business, to explain what gets written out.
    for outName in process.outputModules_().keys():
        allModuleToExplain=[]
        fakePSet=cms.EDProducer("DummyModule")
        nInput=0
        nUnexplained=0
        for s in getattr(process,outName).outputCommands.value():
            if (s.find('keep')!=-1):
                #print s
                detail=s.replace('keep','').replace(' ','').split('_')
                if (detail.__len__()==4):
                    spl=s.replace('keep','').replace(' ','').split('_')
                    dependency=spl[1]
                    object=spl[0]
                    if (object!="*" and dependency=="*"):
                        #if (object=="ZDCRecHitsSorted"):
                        #    allModuleToExplain.append("zdcreco")
                        #    continue
                        if (object in productRECODoesNotCareAbout):
                            print( "we don't care about",object)
                            continue
                        #elif (object=="recoMETs" or object=="recoCaloMETs"):
                        #    for m in allModulesByType(process,["METProducer"]):
                        #        allModuleToExplain.append(m)
                        #    continue
                        elif (object=="BIDULE"):
                            for m in allModulesByType(process,["BIDULEProducer"]):
                                allModuleToExplain.append(m)
                            continue
                        else:
                            print( "requesting a specific product without module name",spl[0],"need specific treatment")
                            setattr(fakePSet,("unexplainedKeep%d"%(nUnexplained)),cms.string(s))
                            nUnexplained=nUnexplained+1
                            continue
                    #print "++++++++"
                    #print "from the output module, needing",dependency
                    if (dependency.find("*")!=-1):
                        if (object=="ZDCDataFramesSorted"):
                            allModuleToExplain.append("hcalDigis")
                            continue
                        elif (object=="EcalRecHitsSorted"):
                            allModuleToExplain.append("reducedEcalRecHitsEE")
                            allModuleToExplain.append("reducedEcalRecHitsEB")
                            continue
                        else:
                            if (dependency.find("*")==dependency.__len__()-1):
                                dependency=dependency[0:dependency.__len__()-1]
                                for m in allMod:
                                    if (m.find(dependency)==0):
                                        #this works well do far
                                        #print "from regexp:",spl[1],"found",m
                                        allModuleToExplain.append(m)
                                continue
                            else:
                                print( 'need a regexp for',spl)
                                setattr(fakePSet,("unexplainedKeep%d"%(nUnexplained)),cms.string(s))
                                nUnexplained=nUnexplained+1
                                continue
                            
                    #wo got there with a module name: validity check in done in this function
                    allModuleToExplain.append(dependency)

                    
        for m in allModuleToExplain:
            #print m
            if (not (m in allMod)):
                #boh, this is not necessary
                print( 'module',m,'is required for output but not in the schedule. SKIPPING DESCRIPTION')
            else:
                if (not m in ModuleExplained.nameList):
                    declareDep(outName,m)
                    setattr(fakePSet,("inputLabel%d"%(nInput)),cms.InputTag(m))
                    print( "------")
                    print( "doing the dependencies for",m)
                    p(m)
                    nInput=nInput+1
                
        declareSelf(outName,fakePSet)
    ####final check on useless module
    print( "+++++++++++++++++++++++++++")
    print( "+++++++++++++++++++++++++++")
    print( "+++++++++++++++++++++++++++")
    dropCommand=""
    for m in allMod:
        if m not in ModuleExplained.nameList:
            print( 'module',m,'does not seem to have been included anywhere')
            dropCommand+="process.reconstruction_step.remove(process.%s)\n"%(m,)
    print( "+++++++++++++++++++++++++++")
    print( "+++++++++++++++++++++++++++")
    print( dropCommand)
    print( "+++++++++++++++++++++++++++")
    print( "+++++++++++++++++++++++++++")
    

def skipThoseModule(listOfModules):
    for m in listOfModules:
        alreadyExplained(m)




if __name__ == "__main__":

    print("---------------------------------------------------------")
    print("     dumping configuration description")
    print("---------------------------------------------------------")

    usage="--list"
    parser = optparse.OptionParser(usage)

    parser.add_option("--useES",
                      default=False,
                      action="store_true",
                      help="include the ES producer dependencies in the graph"
                  )
    parser.add_option("--spec",
                      default="All",
                      choices=["JetsOnly","Muons","GeneralTracks","FromOutputModule","Module","All"],
                      help="specify what part of the configuration to produce the dependency for"
                  )
    parser.add_option("--cfg",
                      default=None,
                      help="the cmsRun python configuration to parse the module dependency from"
                  )
    parser.add_option("--modules",
                      default="",
                      help="coma separated list of the modules that have to be explained (and all upstream ones), in case of using --spec Module"
                  )

    parser.add_option("--skipmodules",
                      default="")

    parser.add_option("--dumpCfg",
                      default="")

    parser.add_option("--fullDump",
                      default=False,
                      action="store_true"
                  )

    parser.add_option("--inputDefinition",
                      default="",
                      help="poperly formatted input branch documentation files")

    parser.add_option("--outputDefinition",
                      default="",
                      help="poperly formatted output branch documentation files")


    (options,args)=parser.parse_args()
    spec=options.spec
    ICNLUDEES=options.useES

    if options.cfg!=None:
        print("loading configuration from ",options.cfg)
        cfg=options.cfg.replace('.py','')
        #find it also in the directory it lives in
        if (cfg.find("/")!=-1):
            path, f = os.path.split(cfg)
            sys.path.append(path)
            cfg=f
        ns=__import__(cfg)
        process = ns.process


    globalAllModule=allModules(process)


    print("specification is",spec)

    if (spec=="JetsOnly"):
        ### do jets only
        skipThoseModule(["generalTracks","particleFlowBlock"])
        explainAllModulesWith(["Jets","jets","JetI"])
    elif(spec=="Muons"):
        ### do muons only
        skipThoseModule(["generalTracks"])
        explainOnlyCertainModules(["muons"])
    elif (spec=="GeneralTracks"):
        ### tracking
        explainOnlyCertainModules(["generalTracks"])
    elif (spec=="FromOutputModule"):
        ### from the output module definition
        print("looking from the output module definition")
        explainFromOutputDefinition()
    elif (spec=="Module"):
        if options.skipmodules!="":
            skipThoseModule(options.skipmodules.split(","))
        explainOnlyCertainModules(options.modules.split(","))
    elif (spec=="All"):
        #everything or customise your need here
        if options.outputDefinition:
            moduleInOutput = set()
            with open(options.outputDefinition,'r') as output_EDMDumpEventContent:
                for line in output_EDMDumpEventContent.readlines():
                    BN=line.split()[-1]
                    if not '_' in BN: continue
                    T,M,L,P = BN.split('_')
                    moduleInOutput.add( M.replace('"',''))
            print(len(moduleInOutput),"modules in output to be explained")
            explainOnlyCertainModules( list(moduleInOutput) )
        else:
            explainAllModules()


    name='confDiag'+spec+'.html'

    INVERT=True
    makeHTML(DeclaredModules,DeclaredDeps,name)
    #nameR='reconstructionReverse'+spec+options.label+'.html'
    #INVERT=False
    #makeHTML(DeclaredModules,DeclaredDeps,nameR)
