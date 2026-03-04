import toml
import subprocess

from calc_tester import Test
from bs4 import BeautifulSoup
from calc_xml_parser import CalcParser

ATTACHMENTS = '{{ATTACHMENTS}}'.split(',')
SOLUTION_FILE_NAME = 'SOLUTION.calc'

if len(ATTACHMENTS) != 1:
    raise Exception('Questa domanda accetta solo un file Open Document Sheet (.ods)')

ATTACHMENT = ATTACHMENTS[0]

if not ATTACHMENT.endswith('.calc'):
  raise Exception('Formato del file incorretto')

if ATTACHMENT == SOLUTION_FILE_NAME:
  raise Exception('Nome del file non conesntito')

LIBREOFFICE_COMMAND = ['libreoffice','--convert-to','xhtml',ATTACHMENT]
subprocess.run(LIBREOFFICE_COMMAND,check=True,stderr=subprocess.DEVNULL)

(fname,extension) = ATTACHMENT.split('.')
output_file_name = f"{fname}.xhtml"

with open(output_file_name) as f:
  submission_parser = CalcParser(BeautifulSoup(f,features='lxml'))

try:
  with open(SOLUTION_FILE_NAME) as f:
    solution_parser = CalcParser(BeautifulSoup(f,features='lxml'))
except:
  raise Exception('Errore Interno: File di soluzione NON trovato')

tests = Test.model_validate(toml.loads("""{{TEST.testcode| e('py')}}"""))

#debug
print(tests)
results = tests.execute(submission_parser,solution_parser)

print(results)
print(results.get_got_score())
print(results.get_possible_score())
print(results.get_got_fraction())