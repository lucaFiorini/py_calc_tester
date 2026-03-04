import toml
import subprocess

from calc_tester import Test
from bs4 import BeautifulSoup
from calc_xml_parser import CalcParser

ATTACHMENTS = '{{ATTACHMENTS}}'.split(',')
if len(ATTACHMENTS) != 1:
    raise Exception('Questa domanda accetta solo un file Open Document Sheet (.ods), per favore elimina gli altri')

ATTACHMENT = ATTACHMENTS[0]

LIBREOFFICE_COMMAND = ['libreoffice','--convert-to','xhtml',ATTACHMENT]
subprocess.run(LIBREOFFICE_COMMAND,check=True,stderr=subprocess.DEVNULL)

(fname,extension) = ATTACHMENT.split('.')
output_file_name = f"{fname}.xhtml"

with open(output_file_name) as f:
  parser = CalcParser(BeautifulSoup(f,features="lxml"))

tests = Test.model_validate(toml.loads("""{{TEST.testcode| e('py')}}"""))
#debug
print(tests)
results = tests.execute(parser)

print(results)
print(results.get_got_score())
print(results.get_possible_score())
print(results.get_got_fraction())