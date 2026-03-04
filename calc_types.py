from __future__ import annotations
from pydantic import BaseModel
type coord = tuple[int,int]
type cellValue = int|float|str

def string_to_col_num(s : str) -> int:
  c_offset = 0
  A_val = ord('A')
  Z_val = ord('Z')
  alphabet_len =  Z_val - A_val
  total : int = 0
  for c in reversed(s):
    total += ((ord(c.upper()) - A_val) + 1) * (alphabet_len ** c_offset)
    c_offset+=1
  
  return total

class CellPosition(BaseModel):
  col: str
  row: int 

  def to_coord(self) -> coord:
    return (
      string_to_col_num(self.col) - 1,
      self.row - 1,
    )
  
  def __str__(self):
    return f"{self.col}{self.row}"
  
  @staticmethod
  def From_Coord(c: coord) -> CellPosition:
    col_num = c[0] + 1
    col_str = ''
    A_val = ord('A')
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        col_str = chr(A_val + remainder) + col_str
    return CellPosition(col=col_str, row=c[1] + 1)

  @staticmethod
  def Range_From_String(s: str)-> list[CellPosition]:
    (a,b) = s.split(':')
    return(CellPosition.Range(CellPosition.From_String(a), CellPosition.From_String(b)))
    
  @staticmethod
  def Range(a: CellPosition, b: CellPosition) -> list[CellPosition]:
    a_coord = a.to_coord()
    b_coord = b.to_coord()
    col_start = min(a_coord[0], b_coord[0])
    col_end   = max(a_coord[0], b_coord[0])
    row_start = min(a_coord[1], b_coord[1])
    row_end   = max(a_coord[1], b_coord[1])
    return [
      CellPosition.From_Coord((col, row))
      for row in range(row_start, row_end + 1)
      for col in range(col_start, col_end + 1)
    ]
  
  @staticmethod
  def From_String(s: str) -> CellPosition:
    col = ''
    row = ''
    for c in s:
        if c.isalpha():
            col += c.upper()
        else:
            row += c
    return CellPosition(col=col, row=int(row))