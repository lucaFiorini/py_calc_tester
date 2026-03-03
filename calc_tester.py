from dataclasses import dataclass
from calc_parser import CellPosition,CalcParser
from testing import Result,TestCase,ExecutedTest,Result,Success,Fail
from typing import Callable

@dataclass(kw_only=True)
class BulkTester:
  parser : CalcParser
  cells : list[CellPosition]
  tests : list[
      TestCase[
        Callable[[CalcParser,CellPosition],Result]
      ]
    ]
  
  def run(self) -> list[ExecutedTest]:

    results : list[ExecutedTest] = []

    for test in self.tests:
      for cell in self.cells:
        res = test.func(self.parser,cell)
        match res:
          case Success(): pass
          case Fail(_): 
            results.append(ExecutedTest(test.definition, res))
            break
      
      results.append(ExecutedTest(test.definition, Success()))

    return results