import toml
import subprocess
import json

#from py_calc_tester.calc_tester import Test,TestResult
#from py_calc_tester.calc_xml_parser import CalcParser

from calc_tester import Test,TestSetTemplate,TestSetRegistry
from test_result import Success,Failure,Partial,Invalidated
from calc_xml_parser import CalcParser

from typing import Any
from bs4 import BeautifulSoup

# Register Common testcases
templates = toml.loads("""{{QUESTION.globalextra}}""")
for key in templates:
  TestSetRegistry.register(
    key=key,
    template=TestSetTemplate.model_validate(templates[key])
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

tests = json.loads("""{{TESTCASES | json_encode | e('py')}}""")

test_summaries : list[dict[str,str]] = []
total_result : float = 0

for test in tests:
  test = Test.model_validate(toml.loads(test['testcode']))
  res = {}

  res['description'] = '[NON DEFINITA]' if test.description is None else test.description
  res['out'] = ""
  if test.show_range:
    res['range'] = f"{test.range}"
  else:
    res['range'] = f"NASCOSTO"

  case_results = test.execute(submission_parser,solution_parser)
  for i,result in enumerate(case_results.test_results):

    match result.status:
      case Success(): marker = '✅'
      case Partial(): marker = '🟡'
      case Failure(): marker = '❌'
      case Invalidated(): marker = '🚫'

    res['out'] += f"{marker} {result.possible_score}pt\t \t{result.test_name}\n"

  res['out'] += '\n'
  res['ottenuto'] = f"[{case_results.get_got_score()}/{case_results.get_possible_score()}]\n"
  total_result += case_results.get_got_fraction() / len(tests)

  test_summaries.append(res)

results_table : list[list[str]] = []

header = ["#N","Descrizione","Range","Casi","Ottenuto"]
results_table.append(header)

cols = ['description','range','out','ottenuto']
for i,summary in enumerate(test_summaries):
  results_table.append([str(i+1)])
  for col in cols:
    results_table[-1].append(summary[col])
    
print(
  json.dumps(
    {
      "testresults": results_table,
      "epiloguehtml":f"<h3>Voto finale: {round(total_result*10,1)}</h3>", 
      "fraction":total_result
    }
  )
)