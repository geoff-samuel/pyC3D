from __future__ import annotations

import copy

from pyC3D import vector3


class ParameterDataTypes(object):
    """The data types of the parameters in a c3d file"""

    String = -1
    Byte = 1
    Interger = 2
    FloatingPoint = 4

    @classmethod
    def getTypeFromData(cls, inputData: object) -> int:
        """Gets the type of data from the input data"""
        if isinstance(inputData, list) or isinstance(inputData, tuple):
            types = list(set([type(data) for data in inputData]))
            if int in types and float in types:
                return cls.FloatingPoint
            if len(inputData) == 0:
                raise ValueError("No data in list")
            inputData = inputData[0]

        if isinstance(inputData, str):
            return cls.String
        elif isinstance(inputData, int):
            if inputData < 255:
                return cls.Byte
            return cls.Interger
        elif isinstance(inputData, float):
            return cls.FloatingPoint
        else:
            raise ValueError(f"{type(inputData)} is not a supported type in the c3d format")

    @classmethod
    def dataTypeCheck(cls, inputData: object, inputType: int) -> bool:
        """Checks if the input data is compatible with the input type"""
        try:
            expectedData: int = cls.getTypeFromData(inputData)
            if expectedData == cls.Byte and inputType == cls.Interger:
                return True
            return expectedData == inputType
        except ValueError:
            return False


class Header(object):
    """The header of a c3d file"""

    def __init__(self) -> None:
        """Creates a new header"""
        self.parameterBlock: int = 0
        self.markerCount: int = 0
        self.analogMesasurements: int = 0
        self.firstFrame: int = 0
        self.lastFrame: int = 0
        self.maxFrameGap: int = 0
        self.scaleFactor: float = 0.0
        self.dataStart: int = 0
        self.sampleRate: int = 0
        self.frameRate: float = 0.0

        self.paramaterBlockCount: int = 0
        self.processorType: str | None = None

    def clear(self) -> None:
        """Clears the header"""
        self.parameterBlock = 0
        self.markerCount = 0
        self.analogMesasurements = 0
        self.firstFrame = 0
        self.lastFrame = 0
        self.maxFrameGap = 0
        self.scaleFactor = 0.0
        self.dataStart = 0
        self.sampleRate = 0
        self.frameRate = 0.0

        self.paramaterBlockCount = 0
        self.processorType = None 


class ParameterBase(object):
    """The base class for parameters and parameter groups"""

    def __init__(
        self, 
        name: str, 
        description: str | None = None, 
        locked: bool = False
    ) -> None:
        """
        Creates a new parameter base.

        Args:
            name (str): The name of the parameter.
            description (str, optional): The description of the parameter. Defaults to None.
            locked (bool, optional): Indicates if the parameter is locked. Defaults to False.
        """
        super(ParameterBase, self).__init__()
        self._name: str = name
        self._description: str = description or ""
        self._locked: bool = locked

    def name(self) -> str:
        """Returns the name of the parameter"""
        return self._name

    def setName(self, newName: str) -> None:
        """Sets the name of the parameter"""
        self._name = newName

    def description(self) -> str:
        """Returns the description of the parameter. If the description is None it will be an empty string"""
        return self._description

    def setDescription(self, newValue: str) -> None:
        """Sets the description of the parameter. If the description is None it will be set to an empty string"""
        self._description = newValue or ""
    def locked(self) -> bool:
        """Returns True if the parameter is locked. If the parameter is locked it cannot be changed"""
        return self._locked

    def setLocked(self, newValue: bool) -> None:
        """Sets the locked state of the parameter. If the parameter is locked it cannot be changed"""
        self._locked = newValue


class Parameter(ParameterBase):
    """A parameter in a c3d file"""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        locked: bool = False,
        dataType: int | None = None,
        data: object = None,
    ) -> None:
        """
        Creates a new parameter.

        Args:
            name (str): The name of the parameter.
            description (str, optional): The description of the parameter. Defaults to None.
            locked (bool, optional): Indicates if the parameter is locked. Defaults to False.
            dataType (int, optional): The data type of the parameter. Defaults to None.
            data (object, optional): The data associated with the parameter. Defaults to None.
        """
        super(Parameter, self).__init__(name, description=description, locked=locked)
        self._data: object = data
        self._dataType: int | None = dataType
        self._dimensions: tuple[int, int] = (0, 0)

    def dataType(self) -> int | None:
        """Returns the data type of the parameter. If None the data is not set"""
        return self._dataType

    def setDataType(self, newValue: int) -> None:
        """Sets the data type of the parameter. If the data is not None the data will be checked for compatibility"""
        if self._data is not None:
            if not ParameterDataTypes.dataTypeCheck(self._data, newValue):
                raise ValueError(
                    "New Type is not compatible with current data. Try .clear() to clear data"
                )
        self._dataType = newValue

    def data(self) -> object:
        """Returns a copy of the data. This is to prevent the data from being changed without using the .setData() method"""
        return copy.deepcopy(self._data)

    def setData(self, newData: object) -> None:
        """Sets the data of the parameter. The data will be checked for compatibility with the current data type"""
        if self._dataType is None:
            raise ValueError("Cannot set new data with no dataType set")
        if not ParameterDataTypes.dataTypeCheck(newData, self._dataType):
            raise ValueError(
                f"New Data is not compatible with current data Type. (data: {type(newData)}, dataType: {type(self._dataType)})"
            )
        self._data = newData

    def clear(self) -> None:
        """Clears the data and data type"""
        self._data = None

    def __repr__(self) -> str:
        """Returns a string representation of the Parameter object"""
        return f"Parameter(name='{self.name()}', description='{self.description()}', locked={self.locked()})"    


class ParameterGroup(ParameterBase):
    """A group of parameters in a c3d file"""

    def __init__(
        self,
        name: str,
        groupId: int,
        description: str | None = None,
        locked: bool = False,
    ) -> None:
        """
        Initializes a new parameter group.

        Args:
            name (str): The name of the parameter group.
            groupId (int): The ID of the parameter group. If positive, the group will be locked.
            description (str, optional): The description of the parameter group. Defaults to None.
            locked (bool, optional): Indicates whether the parameter group is locked. Defaults to False.
        """
        super(ParameterGroup, self).__init__(
            name, description=description, locked=locked
        )
        self._parameters: list[ParameterBase] = []

        if groupId > 0:
            self._locked = True

        self._groupId: int = abs(groupId)

    def groupId(self) -> int:
        """Returns the group id. This will be negative if the group is locked"""
        return self._groupId

    def setGroupId(self, newData: int) -> None:
        """Sets the group id. This will be converted to a negative number if positive"""
        self._groupId = abs(newData)

    def getParameter(self, name: str) -> ParameterBase | None:
        """Returns the parameter with the given name or None if not found"""
        for param in self._parameters:
            if param.name() == name:
                return param
        return None

    def getParameters(self) -> list[ParameterBase]:
        """Returns a list of all parameters in the group"""
        return self._parameters

    def addParameter(self, newParameterObj: ParameterBase) -> None:
        """Adds the given parameter to the group"""
        self._parameters.append(newParameterObj)

    def addNewProperty(self, name: str) -> Parameter:
        """Adds a new property to the group and returns it"""
        newPram: Parameter = Parameter(name)
        self.addParameter(newPram)
        return newPram

    def removePrameter(self, prameterObj: ParameterBase) -> None:
        """Removes the given parameter from the group"""
        return self._parameters.remove(prameterObj)

    def removePrameterByName(self, name: str) -> bool:
        """Removes the parameter with the given name and returns True if it was found and removed. Returns False if the parameter was not found"""
        param: ParameterBase | None = self.getParameter(name)
        if param is not None:
            self._parameters.remove(param)
            return True
        return False

    def __repr__(self) -> str:
        """Returns a string representation of the Parameter object"""
        return f"ParameterGroup(name='{self.name()}', groupId='{self.groupId()}', description='{self.description()}', locked={self.locked()})"    



class Marker(object):
    """A marker in a c3d file"""

    def __init__(self, markerName: str) -> None:
        """Creates a new marker with the given name"""
        self._markerName: str = markerName
        self._data: dict[str, object | vector3.Vector3] = {}

    def markerName(self) -> str:
        """Returns the name of the marker"""
        return self._markerName

    def setMarkerName(self, newName: str) -> None:
        """Sets the name of the marker"""
        self._markerName = newName

    def getPosition(self, frameNumber: int) -> vector3.Vector3 | None:
        """Returns the position of the marker at the given frame number"""
        return self._data.get(frameNumber)

    def setPosition(self, frameNumber: int, positionAtFrame: vector3.Vector3) -> None:
        """Sets the position of the marker at the given frame number"""
        self._data[frameNumber] = positionAtFrame

    def _sortKeys(self) -> list[str]:
        """Sorts the keys in the dictionary and returns them as a list"""
        keys: list[str] = self._data.keys()
        keys.sort()
        return keys

    def getFirstFrame(self):
        """Returns the first frame number for the markers data"""
        return self._sortKeys()[0]

    def getLastFrame(self):
        """Returns the last frame number for the markers data"""
        return self._sortKeys()[-1]
