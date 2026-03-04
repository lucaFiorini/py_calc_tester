from .calc_types import CellPosition, cellValue
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from bs4.element import Tag

@dataclass
class CalcParser:
  file : BeautifulSoup
  table_tag : Tag = field(init=False)
  table_cell_elems : list[list[Tag]] = field(init=False)

  def __post_init__(self)->None:

    tables = self.file.find_all('table')
    assert len(tables) != 0, "The table is empty"
    assert len(tables) < 2, "Only one table is supported"
    
    self.table_cell_elems = []

    self.table_tag = tables[0]
    rows = self.table_tag.find_all('tr',recursive=False)

    for row in rows:
      self.table_cell_elems.append(row.find_all('td',recursive=False))

  def get_cell_data(self, position: CellPosition) -> Tag|None:
    (col,row) = position.to_coord()

    table_height = len(self.table_cell_elems)
    table_width = len(self.table_cell_elems[0]) if(len(self.table_cell_elems) > 0) else 0
   
    if row >= table_height or  col >= table_width: return None
    return self.table_cell_elems[row][col]

  def get_cell_value(self, position: CellPosition) -> cellValue|None:
    cell = self.get_cell_data(position)
    if cell == None or cell.text == "": return None
    if cell.has_attr('sdval'): 
      v = str(cell.attrs['sdval'])
    else:
      v = str(cell.text) 
    try: return int(v)
    except:
      try: return float(v) 
      except: return v

  def get_bgcolor(self, position: CellPosition) -> str|None:
    cell = self.get_cell_data(position)
    if cell == None or not cell.has_attr('bgcolor'): return None
    return str(cell.attrs["bgcolor"])
  
  def get_cell_formula(self, position: CellPosition) -> str|None:
    cell = self.get_cell_data(position)
    if cell is None: 
      return None
    if cell.has_attr('data-sheets-formula'):
      return str(cell['data-sheets-formula'])
    else:
      return None
    
  def is_bold(self,position: CellPosition) -> bool:
    cell = self.get_cell_data(position)
    if cell is None:
      return False
    return cell.find('b') is not None
