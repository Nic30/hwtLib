from hwt.interfaces.std import Signal
from hwt.synthesizer.interfaceLevel.unit import Unit


class ExampleChild(Unit):
    def _declr(self):
        self.c = Signal()
        self.d = Signal()

    def _impl(self):
        self.d ** self.c
    
    
class UnusedSubunit(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        
        self.child = ExampleChild()
    
    def _impl(self):
        # self.child left unconnected -> error
        self.b ** self.a 
    

class UnusedSubunit2(Unit):
    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        
        self.child0 = ExampleChild()
        self.child1 = ExampleChild()
        self.child2 = ExampleChild()
    
    def _impl(self):
        # chain of children is left unconnected -> error
        self.b ** self.a 
        
        self.child1.c ** self.child0.d
        self.child2.c ** self.child1.d
        
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = UnusedSubunit2()
    # hwt.serializer.exceptions.SerializerException
    print(toRtl(u))        
