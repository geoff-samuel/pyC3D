from __future__ import annotations

import typing
import struct
import functools

from pyC3D import consts


class BinaryFileReader(object):
    """ BinaryFileReader is a class to help ease the reading of binary data from a file
        With easy method to read Bytes, Ints, Longs, Floats and Strings
    """

    def __init__(self, filePath: str|None=None):
        """ Constructor

            Args:
                filePath (str): the path of a the file to load in (OPTIONAL)
        """
        self._handle:typing.BinaryIO|None = None
        self._filePath:str|None = None
        self._processorType:str | None = None
        self._pos = 0
        if filePath is not None:
            self.openFile(filePath)

    def openFile(self, filePath:str) -> None:
        """ Open the give file for reading

            Args:
                filePath (str): the path of a the file to load in (OPTIONAL)
        """
        self._filePath = filePath
        self._pos = 0
        with open(filePath, "rb") as handle:
            self._data = handle.read()
        self._handle = open(filePath, "rb")

    def closeFile(self) -> None:
        """ Close the current file
        """
        if self._handle is not None:
            self._handle.close()

    def seek(self, seekPos:int) -> None:
        """ To go the position in the file

            Args:
                seekPos (int): the amount of bytes to go to in the file
        """
        if self._handle is None:
            raise IOError("No file is open")
        self._handle.seek(seekPos)

    def tell(self) -> int:
        """ Get the current reader position in the file

            Returns:
                an Int of the amount of bytes the reader is currently in the file
        """
        if self._handle is None:
            raise IOError("No file is open")
        return self._handle.tell()

    def readStringFromByte(self, length:int) -> str:
        """ Method read a set length string from a binary file

            Args:
                length (int)        : the length of the string to read in

            Returns:
                    A string from the c3d file, the length of which matches in
                    the input length
        """
        data = self.readBytes(length)
        return data.decode()

    def readBytes(self, length:int) -> bytes:
        try:
            return self._handle.read(length)
        except AttributeError:
            raise IOError("No file is open")

    def readByte(self) -> int:
        """ Method read a single byte from a binary file

            Returns:
                    The byte value
        """
        return struct.unpack('b', self.readBytes(1))[0]

    def readUnsignedByte(self) -> int:
        """ Method read a single byte from a binary file

            Returns:
                    The byte value
        """
        return struct.unpack('B', self.readBytes(1))[0]

    def readInt(self) -> int:
        """ Method read a single int from a binary file

            Returns:
                    The int value
        """
        return self._readBasedOnProcessorType(self.readBytes(2), consts.DataTypes.INT, self._processorType)

    def readLong(self) -> int:
        """ 
        Method read a single long int from a binary file

        Returns:
            The long int value
        """
        return self._readBasedOnProcessorType(self.readBytes(4), consts.DataTypes.LONG, self._processorType)

    def readFloat(self) -> float:
        """ 
        Method read a single float from a binary file
        
        Returns:
            The float value
        """
        return self._readBasedOnProcessorType(self.readBytes(4), consts.DataTypes.FLOAT, self._processorType)

    def setProcessorType(self, processorType:str|None) -> None:
        """ Set the processor type

            Args:
                processorType (str): the processor type
        """
        self._processorType = processorType
        
    @staticmethod
    @functools.cache
    def _readBasedOnProcessorType(data: bytes, dataType: int, processorType: str | None) -> int | float:
        """ Read the data based on the processor type and the given dataType (int, long, float)"""
        if processorType == consts.ProcessorTypes.INTEL or processorType is None:
            return struct.unpack(f"<{dataType.fmt}", data)[0]
        elif processorType == consts.ProcessorTypes.DEC:
            return struct.unpack(f">{dataType.fmt}", bytes(reversed(data)))[0]
        elif processorType == consts.ProcessorTypes.MIPS:
            return struct.unpack(f"<{dataType.fmt}", data[1:] + data[:1])[0]
        else:
            raise ValueError("Unsupported processor type")

    def bulkReadFloat(self, total) -> list[float]:
        return struct.unpack(f"<{total}f", self.readBytes(consts.DataTypes.FLOAT.size * total))

    def bulkReadInt(self, total) -> list[int]:
        return struct.unpack(f"<{total}h", self.readBytes(consts.DataTypes.INT.size * total))



