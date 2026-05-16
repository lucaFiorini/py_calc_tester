from abc import ABC

class _TestResult(ABC,float):
  def __float__(self):
    return float(self)
  
class Failure(_TestResult):
  def __new__(cls):
    return super().__new__(cls,False)

class Partial(_TestResult):
  def __new__(cls,val : float):
    if not (val > 0 and val < 1):
      raise ValueError("A Partial may only have a value between 1 and 0")
    return super().__new__(cls,val)

class Success(_TestResult):
  def __new__(cls):
    return super().__new__(cls,True)

class Invalidated(_TestResult):
  def __new__(cls):
    return super().__new__(cls,False)
  pass

type ValidTestResult = Success|Partial|Failure
type _IntoValidTestResult = float|ValidTestResult
type TestResult = Invalidated|ValidTestResult

def from_bool(b: bool):
  return Success() if b else Failure()

def from_ratio(successes: int|float,possibilities: int):
  if successes == possibilities: return Success()
  elif successes == 0: return Failure()
  else: return Partial(successes/possibilities)
  
def from_matchable_lists(list_1: list,list_2: list):
  matched = 0
  possible = max(len(list_1),len(list_2))
  for i in range(min(len(list_1),len(list_2))):
    if list_1[i] == list_2[i]:
      matched+=1
  return from_ratio(matched,possible)
    
def average(r1:_IntoValidTestResult, *results : _IntoValidTestResult) -> ValidTestResult: 
  res = [r1,*results]
  total = sum(res)
  return from_ratio(total,len(res))
  
def combine_min(r1:_IntoValidTestResult, *results: _IntoValidTestResult) -> ValidTestResult:
  res = [r1,*results]
  min_res = min(res)
  return from_ratio(min_res,len(res))