##Converts a list of multi-page TIFF files (or other images) into PDF files (supporting multi-page).
# Pre-requisites:
# - Python 3.x - see: https://www.python.org/downloads/
# - Pillow (fork of PIL) - see: https://pillow.readthedocs.io/en/stable/installation.html

from queue import Empty
from PIL import Image, ImageSequence
import getopt, glob, os, sys

# Set the source folder
defaultSrcPath = ''
#'Set the destination folder
defaultDstPath = ''

def tiff_to_pdf(src_path: str, pdf_path: str) -> str:
 
    if not os.path.exists(src_path): raise Exception(f'{src_path} does not find.')
    image = Image.open(src_path)

    images = []
    for i, page in enumerate(ImageSequence.Iterator(image)):
        page = page.convert("RGB")
        images.append(page)
    if len(images) == 1:
        images[0].save(pdf_path)
    else:
        images[0].save(pdf_path, save_all=True,append_images=images[1:])
    return pdf_path

def convertFiles(srcPath: str, dstPath: str):
    print('convertFiles - srcPath: ' + srcPath)
    print('convertFiles - dstPath: ' + dstPath)

    if not srcPath: raise Exception('Empty source path given.')
    if not dstPath: raise Exception('Empty destination path given.')
    if not os.path.exists(srcPath): raise Exception(f'{srcPath} does not find.')
    
    os.chdir(srcPath)                                          #Changes working directory to where-ever the .tif files are
    filesList = glob.glob('*.tif')                                  #Gathers all of the .tif files from working directory
    filesList.extend(glob.glob('*.tiff'))
    filesList.extend(glob.glob('*.jpeg'))
    filesList.extend(glob.glob('*.jpg'))

    k = 0 #count number (for percentge complete)

    for fileName in filesList:                                     #for each file (j) in the list of .tif files....
        k += 1  #this is just for the percentage of files complete
        try:
            progress = round(float(k)/float(len(filesList))*float(100), 2)
            if not os.path.exists(dstPath): os.makedirs(dstPath)
            #strippedFilePath = tiffFilePath.strip('.tif')
            strippedFilename = os.path.splitext(os.path.basename(fileName))[0]
            pdfFilePath = os.path.join(os.path.normpath(dstPath), f'{strippedFilename}.pdf')
            print('convertFiles - Converting file: ' + fileName + " - to pdf: " + pdfFilePath + " - completed (%): " +  str(progress))
            tiff_to_pdf(fileName, pdfFilePath)

        except Exception as e:
            print("convertFiles ERROR to convert file: " + fileName)
            print(e)
            pass

def main(argv): 
    try:
        srcPath = ''
        dstPath = ''

        opts, args = getopt.getopt(argv,"h:i:o:",["sourceFolder=","outputFolder="])
        for opt,value in opts:
            if opt == '-h':
                print('convertImagesToPDF.py -i <sourceFolder> -o <outputFolder>')
                pass
            elif opt in ('-i', '-sourceFolder'):
                srcPath = value
                pass
            elif opt in ('-o', '-outputFolder'):
                dstPath = value
                pass

        if not srcPath and defaultSrcPath: srcPath = defaultSrcPath
        if not dstPath and defaultDstPath: dstPath = defaultDstPath

        convertFiles(srcPath, dstPath)
    except getopt.GetoptError:
        print('convertImagesToPDF.py -i <sourceFolder> -o <outputFolder>')
        sys.exit(1)
    except Exception as e:
        print(f'convertImagesToPDF.py - ERROR - {e.args}')
        sys.exit(2)

# Call to run program
main(sys.argv[1:])