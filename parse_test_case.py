from typing import Any

import toml
from calc_types import cellValue,CellPosition
from calc_parser import CalcParser
from pydantic import BaseModel,ValidationError

class TestSet(BaseModel):
  cells             : list[CellPosition]
  
  values            : list[cellValue]|None  = None
  is_formula        : bool|None       = None
  is_formula_group  : bool|None       = None
  has_bgcolor       : bool|None       = None
  bgcolor           : str|None        = None
  
  def model_post_init(self, context: Any) -> None:
    assert self.values is None or len(self.cells) == len(self.values)
    assert len(self.cells) > 0
    
    return super().model_post_init(context)
  
  def execute(self,parser : CalcParser) -> bool:        
    
    if self.values is not None:
      for cell_val,value in zip(map(lambda cell_pos: parser.get_cell_value(cell_pos) , self.cells),values):
        if cell_val != value:
          return False
        
    if self.is_formula is not None:
      for formula in map(lambda cell_pos: parser.get_cell_formula(cell_pos), self.cells):
        if formula == None:
          return False
        
    if self.is_formula_group is not None:
      initial_formula = parser.get_cell_formula(self.cells[0])
      for cell_formlua in map(lambda cell: parser.get_cell_formula(cell),self.cells):
        if cell_formlua != initial_formula:
          return False
        
    if self.has_bgcolor is not None:
      ...
    if self.bgcolor is not None:
      ...
      
    return True

  
class SubCase(TestSet):
  name : str
  weight : float

class TestData(BaseModel):
  data      : CalcParser
  required  : TestSet
  subcases  : list[SubCase] = []
  
  
  

with open('example.toml') as f:
  data = toml.load(f)
  for values in data['subcases']:
    try:
      print(SubCase.model_validate(values))
    except (TypeError, ValidationError) as err:
      print(err)