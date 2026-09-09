"""Tiny writer for reproducible test/demo patches; components are hand-maintained Pd."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Patch:
 def __init__(self,w=1100,h=800): self.lines=[f'#N canvas 80 80 {w} {h} 12;']; self.links=[]; self.n=0
 def obj(self,x,y,s,kind='obj'):
  i=self.n; self.n+=1; self.lines.append(f'#X {kind} {x} {y} {s};'); return i
 def msg(self,x,y,s): return self.obj(x,y,s,'msg')
 def text(self,x,y,s): return self.obj(x,y,s,'text')
 def c(self,a,b,o=0,i=0): self.links.append(f'#X connect {a} {o} {b} {i};')
 def save(self,p): (ROOT/p).write_text('\n'.join(self.lines+self.links)+'\n')
