import json
import re
import subprocess
from PyPDF2 import PdfFileReader, PdfFileWriter

def main():
    with open('contents.json') as f:
        contents = json.load(f)
    with open('papers/common/preamble.tex') as f:
        preamble = f.read()
    toc = ''

    # Build articles
    totalPages = 0
    for part in contents['parts']:
        toc += '\\\\tocsection{{{}}}\n'.format(part['name'])

        for article in part['articles']:
            toc += '\\\\tocitem{{{}}}{{{}}}{{{}}}\n'.format(
                article['title'], article['author'], totalPages + 1
            )

            fn = article['fileName']
            print('Building {}.tex ...'.format(fn))

            # Set page number
            with open('papers/common/preamble.tex', mode='w') as f:
                f.write(preamble + 
                    '\n\\AtBeginDocument{{\\setcounter{{page}}{{{}}}}}\n'.format(totalPages + 1))

            # Run latexmk
            cwd = 'papers/{}/'.format(fn)
            proc = subprocess.Popen([
                'latexmk', '-interaction=nonstopmode', '-pdf', '-xelatex', fn + '.tex'
            ], cwd=cwd, stdout=subprocess.DEVNULL)
            proc.wait(timeout=60)

            # Restore page number
            with open('papers/common/preamble.tex', mode='w') as f:
                f.write(preamble)
                
            if (proc.returncode != 0):
                print('============')
                print('{}.tex failed to build.'.format(fn))
                print('============')
                exit(1)
            
            # Read pdf to get the number of pages
            with open('papers/{0}/{0}.pdf'.format(fn), 'rb') as f:
                reader = PdfFileReader(f)
                totalPages += reader.numPages

            if (totalPages % 2 == 1): totalPages += 1

    # Make TOC
    with open('parts/front/front.tex', 'r') as f:
        front = f.read()
    with open('parts/front/front.tex', 'w') as f:
        f.write(re.sub(r'%\s*!\s*TOC', toc, front))
    
    proc = subprocess.Popen([
        'latexmk', '-interaction=nonstopmode', '-pdf', '-xelatex', 'front.tex'
    ], cwd='parts/front', stdout=subprocess.DEVNULL)
    proc.wait(timeout=60)

    with open('parts/front/front.tex', mode='w') as f:
        f.write(front)
                
    if (proc.returncode != 0):
        print('============')
        print('front.tex failed to build.')
        print('============')
        exit(1)
    
    # Merge all PDF files
    writer = PdfFileWriter()
    frontPages = 0

    reader = PdfFileReader(open('parts/front/front.pdf', 'rb'))
    writer.appendPagesFromReader(reader)
    if (reader.numPages % 2 == 1):
        writer.addBlankPage()
    frontPages = reader.numPages + reader.numPages % 2
    
    for part in contents['parts']:
        for article in part['articles']:
            fn = article['fileName']

            reader = PdfFileReader(open('papers/{0}/{0}.pdf'.format(fn), 'rb'))
            writer.appendPagesFromReader(reader)
            if (reader.numPages % 2 == 1):
                writer.addBlankPage()
            
    with open('hesi.pdf', 'wb') as f:
        writer.write(f)

    print('============')
    print('Output written to {} ({} + {} pages)'.format(
        'hesi.pdf', frontPages, totalPages
    ))
    print('============')
            
if __name__ == "__main__":
    main()
