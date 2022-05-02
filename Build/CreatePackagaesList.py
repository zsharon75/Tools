from asyncio.windows_events import NULL
from email.mime import base
from pathlib import Path
import getopt, glob, os, sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
import re
import logging

# Set the source folder
defaultSrcPath = ''
#'Set the destination folder 
defaultDstPath = ''


class BaseInfo(object):
    def __init__(self, id, version, file_path):
        self.id = id
        self.version = version
        self.file_path = file_path

class PackInfo(BaseInfo):
    def __init__(self, id, version, file_path, targetFramework):
        super(PackInfo, self).__init__(id, version, file_path)
        self.targetFramework = targetFramework

class ReferenceInfo(BaseInfo):
    def __init__(self, id, version, file_path, hintPath):
        super(ReferenceInfo, self).__init__(id, version, file_path)
        self.hintPath = hintPath

#typedef... 
PackInfoElement = OrderedDict[str, PackInfo]
PackInfoDict = OrderedDict[str, PackInfoElement]   # moduleName -> { version -> }
ReferenceInfoElement = OrderedDict[str,ReferenceInfo]
ReferenceInfoDict = OrderedDict[str,  ReferenceInfoElement]

def scanPackages(src_path: str):
    os.chdir(src_path) 
    packFilesList = []
    projFilesList = []

    for file in Path(src_path).rglob('*.*'):
        if file.name == 'packages.config':
            packFilesList.append(str(file))
        elif file.suffix == '.csproj':
            projFilesList.append(str(file))
        else:
            continue

    return packFilesList, projFilesList

def extractPackList(packFilesList: list):
    packInfoDict = {}
    for file in packFilesList:
        extractFromPackFile(file, packInfoDict)
    return packInfoDict

def extractProjList(projFilesList: list):
    refInfoDict = {}
    for file in projFilesList:
        extractFromCSProjFile(file, refInfoDict)
    return refInfoDict


def dumpToFiles(packInfoDict: PackInfoDict, refInfoDict: ReferenceInfoDict):
    
    script_dir = os.path.dirname(__file__)
    #dump PackInfo
    f = open(f"{script_dir}\\packInfo.txt", "w")
    logging.info(f'pack-file: {f.name}')
    f.write('Name, Version, TargetFramework, file_path\n')
    orderPackDict = dict(sorted(packInfoDict.items()))
    for key in orderPackDict:
        pie = orderPackDict[key]
        for version in pie:
            pi = pie[version]
            f.write(f'{pi.id}, {pi.version}, {pi.targetFramework}, {pi.file_path}\n')
    f.close()
    #dump ReferenceInfo
    f = open(f"{script_dir}\\referenceInfo.txt", "w")
    logging.info(f'ref-file: {f.name}')
    f.write('Name, Version, HintPath, file_path\n')
    orderRefDict = dict(sorted(refInfoDict.items()))
    for key in orderRefDict:
        rie = orderRefDict[key]
        for version in rie:
            ri = rie[version]
            f.write(f'{ri.id}, {ri.version}, {ri.hintPath}, {ri.file_path}\n')
    f.close()
    

# <?xml version="1.0" encoding="utf-8"?>
# <packages>
#   <package id="Microsoft.SqlServer.Types" version="12.0.5000.0" targetFramework="net45" />
#   <package id="Newtonsoft.Json" version="12.0.3" targetFramework="net462" />
#   <package id="ProjNET" version="2.0.0" targetFramework="net462" />
# </packages>
def extractFromPackFile(pack_path: str, packInfoDict: PackInfoDict):
    logging.info(f'file: {pack_path} - starting...')
    tree = ET.parse(pack_path)
    root = tree.getroot()
    for pack in root.iter('package'):
        packName = pack.attrib['id']
        version = pack.attrib['version']
        targetFramework = pack.attrib['targetFramework']  if('targetFramework' in pack.attrib) else 'N/A'
        if packName not in packInfoDict:
            packInfoDict[packName] = PackInfoElement()
        pie = packInfoDict[packName]
        if version not in pie:
            pi = PackInfo(packName, version, pack_path, targetFramework)
            pie[version] = pi
            logging.debug(f'{packName}, {version}, {targetFramework} - file: {pack_path}')
    return packInfoDict

def getNamespace(element: str):
    m = re.match('\{.*\}', element.tag)
    return m.group(0) if m else ''


# extractFromCSProjFile
#
# Format 1:
#     <Reference Include="netstandard, Version=2.0.0.0, Culture=neutral, PublicKeyToken=cc7b13ffcd2ddd51">
#       <HintPath>..\packages\ProjNET.2.0.0\lib\netstandard2.0\ProjNET.dll</HintPath>
#     </Reference>
#
# Format 2:
#   <Reference Name = "System" AssemblyName = "System" HintPath = "C:\WINDOWS\Microsoft.NET\Framework\v1.1.4322\System.dll" />
#
def extractFromCSProjFile(csproj_path: str, refInfoDict: ReferenceInfoDict):
    logging.info(f'file: {csproj_path} - starting...')
    tree = ET.parse(csproj_path)
    root = tree.getroot()
    ns = getNamespace(root)
    for ref in root.iter(f'{ns}Reference'):
        version = 'N/A'     
        if('Include' in ref.attrib):
            refName = ref.attrib['Include']
            if ',' in refName:
                tokens = refName.split(',')
                refName = tokens[0]
                if("Version" in tokens[1]):
                    vTokens = tokens[1].split('=')
                    version = vTokens[1]
        elif('Name' in ref.attrib):
            refName = ref.attrib['Name']
        if('HintPath' in ref.attrib):
            hintPath = ref.attrib['HintPath']
        else:
            hpe = ref.find(f'{ns}HintPath')
            hintPath = hpe.text if hpe is not None else ''
        if refName not in refInfoDict:
            refInfoDict[refName] = ReferenceInfoElement()
        rie = refInfoDict[refName]
        if version not in rie:
            ri = ReferenceInfo(refName, version, csproj_path, hintPath)
            rie[version] = ri
            logging.debug(f'{refName}, {version}, {hintPath} - file: {csproj_path}')
    return refInfoDict

def main(argv): 
    try:
        srcPath = ''
        
        script_dir = os.path.dirname(__file__)
        logging.basicConfig(
            filemode='w',
            filename=f'{script_dir}\\CreatePackagesList.log', 
            encoding='utf-8', 
            level=logging.DEBUG,
            format='%(asctime)s.%(msecs)03d [%(levelname)s] %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        
        opts, args = getopt.getopt(argv,"h:i:o:",["sourceFolder="])
        for opt,value in opts:
            if opt == '-h':
                print('CreatePackagesList.py -i <sourceFolder>')
                pass
            elif opt in ('-i', '-sourceFolder'):
                srcPath = value
                pass

        if not srcPath and defaultSrcPath: srcPath = defaultSrcPath

        logging.info(f'srcPath: {srcPath}')

        packFilesList, projFilesList = scanPackages(srcPath)
        print(f'main - Found \'{len(packFilesList)}\' packages files - and \'{len(projFilesList)}\' project files... ')
        logging.info(f'Found \'{len(packFilesList)}\' packages files - and \'{len(projFilesList)}\' project files... ')
        packInfoDict = extractPackList(packFilesList)
        print(f'main - found Total \'{len(packInfoDict.keys())}\' packages...')
        logging.info(f'found Total \'{len(packInfoDict.keys())}\' packages...')
        refInfoDict = extractProjList(projFilesList)
        print(f'main - found Total \'{len(refInfoDict.keys())}\' references...')
        logging.info(f'found Total \'{len(refInfoDict.keys())}\' references...')
        dumpToFiles(packInfoDict, refInfoDict)
        print(f'main - dump to files done...')
        logging.info(f'dump to files done...')

    except getopt.GetoptError as e:
        print('CreatePackagesList.py -i <sourceFolder>')
        logging.error(e, exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f'CreatePackagesList.py - ERROR - {e}')
        logging.error(e, exc_info=True)
        sys.exit(2)

# Call to run program
main(sys.argv[1:])