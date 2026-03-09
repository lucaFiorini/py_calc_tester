from dataclasses import dataclass
from typing import Annotated, Any, Callable, ClassVar, assert_never

from .calc_types import cellValue,CellPosition
from .calc_xml_parser import CalcParser
from pydantic import BaseModel,Field,PrivateAttr, BeforeValidator, TypeAdapter
from bs4 import Tag
from enum import Enum

class TestSet(BaseModel):
  match_values               : list[cellValue]|None = None
  match_solution_values      : bool                 = False

  is_formula                 : bool|None            = None
  no_formula_drift           : bool                 = False

  is_bold                    : bool|None            = None

  has_bgcolor                : bool|None            = None
  match_bgcolor              : str |None            = None
  match_solution_bgcolor     : bool                 = False

  def execute(self, submission : CalcParser, solution: CalcParser, cells : list[CellPosition]):
    submission_values = [submission.get_cell_value(cell) for cell in cells]
    solution_values = [solution.get_cell_value(cell) for cell in cells]
    cell_formulas = [submission.get_cell_formula(cell) for cell in cells]
    
    submission_bgcolors = [submission.get_bgcolor(cell) for cell in cells]
    solution_bgcolors = [solution.get_bgcolor(cell) for cell in cells]
    
    raw_submission_cell_data = [submission.get_cell_data(cell) for cell in cells]
    raw_solution_cell_data = [solution.get_cell_data(cell) for cell in cells]

    assert len(submission_values) == len(cells)

    return (
      self.handle_match_values(submission_values) and 
      self.handle_match_solution_values(submission_values,solution_values) and

      self.handle_is_formula(cell_formulas) and 
      self.handle_no_formula_drift(cell_formulas) and

      self.handle_is_bold(raw_submission_cell_data) and

      self.handle_has_bgcolor(submission_bgcolors) and
      self.handle_match_bgcolor(submission_bgcolors) and
      self.handle_match_solution_bgcolor(submission_bgcolors,solution_bgcolors)
    )
  
  def handle_match_values(self,cell_values : list[cellValue|None]) -> bool:
    if self.match_values is not None:
      return cell_values == self.match_values
    return True
  def handle_match_solution_values(self,submission_values : list[cellValue|None], solution_cells : list[cellValue|None]) -> bool:
    if self.match_solution_values:
      return submission_values == solution_cells
    return True

  def handle_is_formula(self,cell_formulas : list[str|None]) -> bool:
    if self.is_formula is not None:
      for formula in cell_formulas:
        if self.is_formula != (formula is not None):
          return False
    return True
  def handle_no_formula_drift(self,cell_formulas: list[str|None]) -> bool: 
    if self.no_formula_drift:
      initial_formula = cell_formulas[0]
      for cell_formlua in cell_formulas[1:]:
        if cell_formlua != initial_formula:
          return False
    return True
  
  def handle_is_bold(self,cell_data : list[Tag|None]) -> bool:
    if self.is_bold is not None:
      for cell in cell_data:
        if cell is None:
          if self.is_bold:
            return False
        else: 
          if self.is_bold != (cell.find('b') is not None):
            return False
    return True
          
  def handle_has_bgcolor(self,submission_bgcolors : list[str|None]) -> bool:
    if self.has_bgcolor is not None:
      for color in submission_bgcolors:
        if self.has_bgcolor != (color is not None):
          return False
    return True
  def handle_match_bgcolor(self,submission_bgcolors : list[str|None]) -> bool:
    if self.match_bgcolor is not None:
      for color in submission_bgcolors:
        if color != self.match_bgcolor:
          return False
    return True
  def handle_match_solution_bgcolor(self, submission_bgcolors : list[str|None], solution_bgcolors : list[str|None]):
    if self.match_solution_bgcolor:
      return submission_bgcolors == solution_bgcolors
    return True

class TestResult(Enum): 
  Invalidated = None
  Failed = False 
  Passed = True

@dataclass
class TestResultInfo:
  test_name : str
  possible_score : int
  result : TestResult

  def __post_init__(self) -> None:
    assert self.possible_score != 0
class TestCase(BaseModel):
  name    : str
  tests   : TestSet
  weight  : int        = 1

def format_key(key : str) -> str:
  return key.replace('-',' ').replace('_',' ').capitalize()

class TestSetRegistry:
  _REGISTRY : ClassVar[dict[str,TestSetTemplate]] = {}
  
  @staticmethod
  def register(key : str, test : TestSetTemplate) -> None:
    if key in TestSetRegistry._REGISTRY:
      raise ValueError('Test already registered')
    TestSetRegistry._REGISTRY[key] = test

class TestSetTemplate(BaseModel):
  default_name : str|None = None
  tests : TestSet

  
class RegisteredTestSetReference(BaseModel):
  key     : str       = Field(alias="from_preset")
  weight  : int       = 1
  
  def model_post_init(self, context: Any) -> None:
    if self.key not in TestSetRegistry._REGISTRY:
      raise ValueError('Key not located in the registry')      
    return super().model_post_init(context)
  
  def get_name(self) -> str:
    default_name = TestSetRegistry._REGISTRY[self.key].default_name
    if default_name is None:
      return format_key(self.key)
    else:
      return default_name
    
  def get_test_case(self) -> TestCase:
    return TestCase(
      name=self.get_name(),
      weight=self.weight,
      tests=TestSetRegistry._REGISTRY[self.key].tests
    )

TESTCASE_MAYBE_REF_VALIDATOR : TypeAdapter[TestCase|RegisteredTestSetReference] = TypeAdapter(TestCase|RegisteredTestSetReference)
def validate_testcsae_maybe_ref(val : dict[str,Any]) -> TestCase:
  parsed_val = TESTCASE_MAYBE_REF_VALIDATOR.validate_python(val)
  match parsed_val:
    case TestCase(): return parsed_val
    case RegisteredTestSetReference(): return parsed_val.get_test_case()
    case _: assert_never(parsed_val)

TestCaseOrRef = Annotated[TestCase, BeforeValidator(validate_testcsae_maybe_ref)]

class Test(BaseModel):
  range         : str
  show_range    : bool = False
  
  prerequisite  : TestCaseOrRef|None  = None
  cases         : list[TestCaseOrRef] = Field(default_factory=lambda: list())

  _cells : list[CellPosition] = PrivateAttr(default_factory=lambda: list())

  def model_post_init(self, context: Any) -> None:
    self._cells = CellPosition.Range_From_String(self.range)

    for subcase in self.cases:
       if subcase.tests.match_values is not None:
        assert len(subcase.tests.match_values) == len(self._cells)

    assert len(self._cells) > 0
    
    return super().model_post_init(context)
  

  def execute(self,submission: CalcParser, solution : CalcParser) -> 'TestResultList':
    
    def assess_all_subcases(case_result : Callable[[TestCase],TestResult]):
      return [
        TestResultInfo (
          test_name=test_case.name,
          possible_score=test_case.weight,
          result=case_result(test_case)
        )
        for test_case in self.cases
      ]
    
    if self.prerequisite is not None:
      
      prerequisite_result = TestResultInfo (
          test_name=f"(Prerequisito) {self.prerequisite.name}",
          possible_score=self.prerequisite.weight,
          result=TestResult(self.prerequisite.tests.execute(submission, solution, self._cells))
        )
      
      if prerequisite_result.result.value:
        return TestResultList(
          test_results = (
            [prerequisite_result] + 
            assess_all_subcases(lambda case: TestResult(case.tests.execute(submission, solution, self._cells)))
          )
        )
      else:
        return TestResultList(
          test_results = (
            [prerequisite_result] +
            assess_all_subcases(lambda _: TestResult.Invalidated)
          )
        )
      
    return TestResultList(
      test_results = assess_all_subcases(lambda case: TestResult(case.tests.execute(submission, solution, self._cells))))
  

@dataclass
class TestResultList:
  test_results : list[TestResultInfo]

  def get_possible_score(self) -> int:
    acc = 0
    for test_result in self.test_results:
      acc+=test_result.possible_score
    return acc
  
  def get_got_score(self) -> int:
    acc = 0
    for test_result in self.test_results:
      if test_result.result.value:
        acc+=test_result.possible_score
    return acc

  def get_got_fraction(self) -> float:
    return self.get_got_score() / self.get_possible_score()
  