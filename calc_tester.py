from typing import Any

from calc_types import cellValue,CellPosition
from calc_xml_parser import CalcParser
from pydantic import BaseModel,Field,PrivateAttr

class TestSet(BaseModel):
  match_values       : list[cellValue]|None  = None
  is_formula         : bool|None             = None
  is_bold            : bool|None             = None
  no_formula_drift   : bool                  = False
  has_bgcolor        : bool|None             = None
  match_bgcolor      : str|None              = None

  def execute(self, parser : CalcParser, cells : list[CellPosition]):
      cell_values = [parser.get_cell_data(cell) for cell in cells]
      cell_formulas = [parser.get_cell_formula(cell) for cell in cells]
      bgcolors = [parser.get_bgcolor(cell) for cell in cells]

      assert len(cell_values) == len(cells)

      if self.match_values is not None:
        for cell_value,value in zip(cell_values, self.match_values):
          if cell_value != value:
            return False
          
      if self.is_formula is not None:
        for formula in cell_formulas:
          if self.is_formula == (formula is None):
            return False
          
      if self.no_formula_drift:
        initial_formula = cell_formulas[0]
        for cell_formlua in cell_formulas[1:]:
          if cell_formlua != initial_formula:
            return False
          
      if self.has_bgcolor is not None:
        for color in bgcolors:
          if self.has_bgcolor == (color is None):
            return False

      if self.match_bgcolor is not None:
        for color in bgcolors:
          if color == self.match_bgcolor:
            return False
          
      return True

class TestResult(BaseModel):
  test_name : str
  possible_score : int
  passed : bool

  def model_post_init(self, context: Any) -> None:
    assert self.possible_score != 0
    assert self.passed <= self.possible_score
    return super().model_post_init(context)
  
class Case(BaseModel):
  name : str
  weight : int
  tests : TestSet

class Test(BaseModel):
  range : str
  cases  : list[Case] = Field(default_factory=lambda: list())

  _cells : list[CellPosition] = PrivateAttr(default_factory=lambda: list())

  def model_post_init(self, context: Any) -> None:
    self._cells = CellPosition.Range_From_String(self.range)

    for subcase in self.cases:
       if subcase.tests.match_values is not None:
        assert len(subcase.tests.match_values) == len(self._cells)

    assert len(self._cells) > 0
    
    return super().model_post_init(context)
  
  def execute(self,parser: CalcParser) -> TestResultList:
    return TestResultList(test_results = [
        TestResult (
          test_name=test_case.name,
          possible_score=test_case.weight,
          passed=test_case.tests.execute(parser,self._cells)
        )
        for test_case in self.cases
      ]
    )
  
class TestResultList(BaseModel):
  test_results : list[TestResult]

  def get_possible_score(self) -> int:
    acc = 0
    for test_result in self.test_results:
      acc+=test_result.possible_score
    return acc
  
  def get_got_score(self) -> int:
    acc = 0
    for test_result in self.test_results:
      if test_result.passed:
        acc+=test_result.possible_score
    return acc

  def get_got_fraction(self) -> float:
    return self.get_possible_score() / self.get_got_score()
  