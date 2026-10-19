from collections import deque
class SafetyEngine:
 def __init__(self,capacity): self.capacity=capacity;self.hist=deque(maxlen=3)
 def evaluate(self,current,preds,doorway):
  self.hist.append(max(preds)>=self.capacity);persistent=sum(self.hist)>=2;ratio=max(preds)/self.capacity
  state='CRITICAL' if ratio>=1 else 'WARNING' if ratio>=.8 else 'SAFE';severe=state=='CRITICAL' and persistent and doorway=='HIGH_RISK'
  if severe:state='SEVERE'
  return {'state':state,'current':current,'capacity':self.capacity,'predictions':preds,'persistent_overload':persistent,'doorway_risk':doorway,'boarding_recommendation':state in ('CRITICAL','SEVERE'),'automatic_stop':False}
