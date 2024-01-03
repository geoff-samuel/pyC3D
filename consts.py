
class DataTypes:
    
    class _DataType(object):
        def __init__(self, name:str, size:int, fmt:str) -> None:
            self.name:str = name
            self.size:int = size
            self.fmt:str = fmt
    
    FLOAT:_DataType = _DataType("Float", 4, 'f')
    LONG:_DataType = _DataType("Long", 4, 'l')
    INT:_DataType = _DataType("Int", 2, 'h')
    

class ProcessorTypes:
    DEC:str = "DEC"
    INTEL:str = "Intel"
    MIPS:str = "MIPS"



    
