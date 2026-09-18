-- Appended only to isolated sample-stretch source. Wrappers preserve candidate bodies.
local original_command=C.command
function C:command(sel,a)
 local before=self.job
 original_command(self,sel,a)
 if sel=='render' and not before and self.job then pd.send('rr-event','attempt',{self.track,self.job}) end
end
local original_loaded=C.copy_loaded
function C:copy_loaded(...)
 pd.send('rr-event','callback-enter',{self.track,self.destination})
 original_loaded(self,...)
 pd.send('rr-event','callback-return',{self.track,self.destination,self.loaded and 1 or 0,self.load_complete and 1 or 0})
end
local original_poll=C.poll
function C:poll(...)
 local pending=self.loaded and self.load_complete
 local destination=self.destination
 if pending then pd.send('rr-event','deferred-enter',{self.track,destination})end
 original_poll(self,...)
 if pending then
  pd.send('rr-event','deferred-return',{self.track,destination,self.loaded and 1 or 0,self.load_cancelled and 1 or 0})
  pd.send('rr-query','list',{destination})
 end
end
local original_finalize=C.finalize
function C:finalize(...)
 pd.send('rr-event','finalize-enter',{self.track,self.loaded and 1 or 0,self.load_complete and 1 or 0})
 original_finalize(self,...)
 pd.send('rr-event','finalize-return',{self.track})
end
-- Deterministic tests schedule a surviving driver clock before the candidate's
-- completion clock, without deleting anything during the synchronous callback.
local probed_loaded=C.copy_loaded
function C:copy_loaded(...)
 pd.send('rr-hook','list',{self.track,self.destination})
 return probed_loaded(self,...)
end
local original_load=C.load_copy
function C:load_copy(...)
 original_load(self,...)
 if self.loaded then pd.send('rr-event','import-request',{self.track,self.destination,self.result})end
end
