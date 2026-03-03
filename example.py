from calc_parser import CellPosition, CalcParser
from calc_tester import BulkTester

from bs4 import BeautifulSoup

from testing import Success, TestCase, Fail, TestDefinition

if __name__ == '__main__':
  with open('test.xhtml') as f:
    parser = CalcParser(BeautifulSoup(f,"html.parser"))    
    
  BulkTester(
    parser=parser,
    cells=CellPosition.Range_From_String("A22:A32"),
    tests=[
      TestCase(
        TestDefinition("Funzione",0.5),
        lambda parser,cell: Success() if parser.get_cell_formula(cell) != None else Fail("Non è una formula")
      ),
      TestCase(
        TestDefinition("Funzione",0.5),
        lambda parser,cell: Success() if parser.get_cell_formula(cell) != None else Fail("Non è una formula")
      )
    ]
  ).run()
  
