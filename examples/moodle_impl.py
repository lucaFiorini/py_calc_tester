import toml
import subprocess
import calc_tester

#from py_calc_tester.calc_tester import Test,TestResult
#from py_calc_tester.calc_xml_parser import CalcParser

from calc_tester import Test,TestResult,TestCase,TestSet,TestSetTemplate
from calc_xml_parser import CalcParser


from bs4 import BeautifulSoup

# Register Common testcases
calc_tester.TestSetRegistry.register(
  key="FREE LUNCH!",
  test=TestSetTemplate(
    tests=TestSet()
  )
)

ATTACHMENTS = '{{ATTACHMENTS}}'.split(',')
SOLUTION_FILE_NAME = 'SOLUTION.ods'

if len(ATTACHMENTS) != 1:
    raise Exception('Questa domanda accetta solo un file Open Document Sheet (.ods)')

ATTACHMENT = ATTACHMENTS[0]

if not ATTACHMENT.endswith('.ods'):
  raise Exception('Formato del file incorretto')

if ATTACHMENT == SOLUTION_FILE_NAME:
  raise Exception('Nome del file non conesntito')

LIBREOFFICE_COMMAND = lambda f: ['libreoffice','--convert-to','xhtml',f]

subprocess.run(LIBREOFFICE_COMMAND(ATTACHMENT),check=True,stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)

fname = ATTACHMENT.removesuffix('.ods')
output_file_name = f"{fname}.xhtml"

with open(output_file_name) as f:
  submission_parser = CalcParser(BeautifulSoup(f,features='lxml'))

try:
  subprocess.run(LIBREOFFICE_COMMAND(SOLUTION_FILE_NAME),check=True,stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
  SOLUTION_XHTML_RESULT = f"{SOLUTION_FILE_NAME.removesuffix('.ods')}.xhtml"

  with open(SOLUTION_XHTML_RESULT) as f:
    solution_parser = CalcParser(BeautifulSoup(f,features='lxml'))

except:
  raise Exception('Errore Interno: File di soluzione NON trovato')

tests = Test.model_validate(toml.loads("""{{TEST.extra| e('py')}}"""))
res = {}

res['got'] = ""
if tests.show_range:
  res['got'] += f"Range del test: {tests.range}\n"
  res['got'] += f"\n"

results = tests.execute(submission_parser,solution_parser)
for i,result in enumerate(results.test_results):

  match result.result:
    case TestResult.Passed: marker = '✅'
    case TestResult.Failed: marker = '❌'
    case TestResult.Invalidated: marker = '🚫'

  res['got'] += f"{marker} {result.possible_score}pt\t \t{result.test_name}\n"

res['got'] += '\n'
res['got'] += f"Risultato Sezione: \t [{results.get_got_score()}/{results.get_possible_score()}]`\n"
res['fraction'] = results.get_got_fraction()

import json
print(json.JSONEncoder().encode(res))
