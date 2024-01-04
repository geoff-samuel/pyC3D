from __future__ import annotations

import os
import threading

from pyC3D import vector3, binaryFileReader, _internals, consts


class C3DFile(object):
    """ 
    Class to handle and deal with the reading in of C3D files, and allowing
    a easy API to access the marker data, and the parameters with the data
    """
    _c3dFileKeyValue_: int = 80

    def __init__(self, filePath:str|None=None) -> None:
        """ 
        Constructor, sets all the internal values to the default of 0 and if a file path is supplied, 
        will load the c3d file

        Args:
            filePath (str): the path of a c3d file to load in (OPTIONAL)
        """
        super().__init__()
        self._filePath: str = ""
        self._parameters:list[_internals.ParameterGroup] = []
        self._markers: list[_internals.Marker] = []
        self._header:_internals.Header = _internals.Header()

        if filePath is not None:
            self.loadFile(filePath)

    def reset(self) -> None:
        """ 
        resets all the internals values to their defaults
        """
        self._header.clear()
        self._parameters = []
        self._markers = []

    def loadFile(self, filePath:str) -> None:
        """ 
        Load the given c3d file into the object. Will read the headers and parameter sections of the 
        file, but will not read any of the actual data, as that is called on a frame basis.

        Args:
            filePath (str): the path of a c3d file to load in
        """
        self.reset()
        if os.path.exists(filePath) is False:
            raise FileNotFoundError(f"File '{filePath}' does not exist")
        self._filePath: str = filePath
        fileObj: binaryFileReader.BinaryFileReader = binaryFileReader.BinaryFileReader(filePath)
        self._readHeader(fileObj)
        self._readParameters(fileObj)
        self._readMarkers(fileObj)
        fileObj.closeFile()

    def _readProcessorType(self, handle:binaryFileReader.BinaryFileReader) -> None:
        """ 
        Internal method to read the processor type from the c3d file. This is not used at this point,
        but it can be used to determine the endianess of the file

        Args:
            handle (binaryFile): file handle object to the open c3d file
        """
        processorType: int = handle.readByte()
        newProc: str | None = {
                84: consts.ProcessorTypes.INTEL,
                85: consts.ProcessorTypes.DEC,
                86: consts.ProcessorTypes.MIPS}.get(processorType)
        self._header.processorType = newProc
        handle.setProcessorType(newProc)

    def _readHeader(self, handle:binaryFileReader.BinaryFileReader) -> None:
        """
        Internal Method to read the header of a c3d file and populate the object with the data

        Args:
            handle (binaryFile): file handle object to the open c3d file
        Raises:
            ValueError: If the file is not a valid c3d File
        """
        
        handle.seek(0)
        self._header.parameterBlock = handle.readByte()  # word 1
        
        # Get the Paramater Section....
        curPos: int = handle.tell()
        
        handle.seek((self._header.parameterBlock - 1) * 512)
        handle.readByte() # Not needed at this point, will re-read paramaters later
        handle.readByte() # Not needed at this point, will re-read paramaters later
        handle.readByte() # Not needed at this point, will re-read paramaters later
        self._readProcessorType(handle)
        
        handle.seek(curPos)
        if handle.readByte() != self._c3dFileKeyValue_:
            raise ValueError("Not a valid C3D file")
        self._header.markerCount = handle.readInt()  # word 2
        self._header.analogMesasurements = handle.readInt()  # word 3
        self._header.firstFrame = handle.readInt()  # word 4
        self._header.lastFrame = handle.readInt()  # word 5
        self._header.maxFrameGap = handle.readInt()  # word 6
        self._header.scaleFactor = handle.readFloat()  # word 7-8
        self._header.dataStart = handle.readInt()  # word 9
        self._header.sampleRate = handle.readInt()  # word 10
        self._header.frameRate = handle.readFloat()  # word 11-12
        # More can be added as needed

    def getParameterByGroupId(self, groupId:int) -> _internals.ParameterGroup | None:
        """
        Retrieves a parameter from the C3D file by its group ID.

        Parameters:
            groupId (int): The group ID of the parameter to retrieve.

        Returns:
            _internals.ParameterGroup | None: The parameter group with the specified group ID, or None if not found.
        """
        groupId = abs(groupId)
        for param in self._parameters:
            if param.groupId() == groupId:
                return param
        return None

    def _newParam(self, handle:binaryFileReader.BinaryFileReader, name:str, groupId:int) -> None:
        """ 
        Internal Method to create a new parameter set from the parameter section of the c3d file. 
        Will create the internal data structor for the new parameter

        Args:
            handle (binaryFile): file handle object to the open c3d file
            name (str): name of the new parameter
            groupId (int): number index of the parameter group
        """
        newParameter: _internals.ParameterGroup = _internals.ParameterGroup(name, groupId)
        newParameter.setDescription(self._readDescription(handle))
        self._parameters.append(newParameter)

    def _readDescription(self, handle:binaryFileReader.BinaryFileReader) -> str:
        """ 
        Internal method to read the a parameter description Current it does nothing with this data,
        but it can be stored.

        Args:
            handle (binaryFile): the c3d file to read
        """
        paramDescirptionLength: int = handle.readByte()
        if paramDescirptionLength == 0:
            return ""
        return handle.readStringFromByte(paramDescirptionLength)

    def _readParameters(self, handle:binaryFileReader.BinaryFileReader) -> None:
        """ 
        Internal method to read the entire parameter block of a c3d file

        Args:
            handle (binaryFile): the c3d file to read
        """
        handle.seek((self._header.parameterBlock - 1) * 512)
        handle.readByte() # Resvered (C3D spec)
        handle.readByte() # Resvered (C3D spec)
        self._header.paramaterBlockCount = handle.readByte()
        self._readProcessorType(handle)

        idx = 0
        while True:
            if self._readParamBlock(handle) is False:
                break
            idx += 1

    def _readParamBlock(self, handle:binaryFileReader.BinaryFileReader) -> bool:
        """ Internal method to read the a single parameter of a c3d file

            Args:
                handle (binaryFile) : the c3d file to read
        """
        value: object = None
        nameLength: int = abs(handle.readByte())
        if nameLength == 0:
            return False
        
        groupId: int = handle.readByte()
        groupName: str = handle.readStringFromByte(nameLength)
        
        currentFilePos: int = handle.tell()
        bytesToNextGroup: int = handle.readInt()
        if bytesToNextGroup == 0:
            return False
 
        parameterGroup: _internals.ParameterGroup | None = self.getParameterByGroupId(groupId)

        if parameterGroup is None:
            self._newParam(handle, groupName, groupId)
            return True

        parameter: _internals.Parameter = parameterGroup.addNewProperty(groupName)
        dataType: int = handle.readByte()
        dataDimensions: int = handle.readByte()
        
        # Its a string
        if dataType == -1:
            stringSize: int = handle.readByte()
            # Its a String
            if dataDimensions > 1:
                value = []
                arraySize: int = handle.readUnsignedByte()
                if arraySize == 0:
                    value = [""]
                
                for _ in range(arraySize):
                    try:
                        value.append(handle.readStringFromByte(stringSize).strip())
                    except:
                        value = ["UNABLE TO READ VALUE"]
            else:
                value = handle.readStringFromByte(stringSize).strip()
        # Its a scaler
        elif dataDimensions == 0:
            value = self._readPropertyValue(handle, dataType)
        else:
            value = []
            for _ in range(dataDimensions):
                value.append(self._readPropertyValue(handle, dataType))

        parameter.setDataType(dataType)
        parameter.setData(value)
        handle.seek(currentFilePos + bytesToNextGroup)
        return True

    def _readPropertyValue(self, handle:binaryFileReader.BinaryFileReader, propertyType:int) -> str | int | float:
        """ 
        Internal Method to read type of value from the c3d file.

        Support reading: bytes, int's and floats. The type is passed in by the propertyType arg.

        Args:
            handle (binaryFile): file handle object to the open c3d file
            propertyType (int): the type of value to read in, values are:
                                       -1 - String
                                        1 - Byte
                                        2 - Int
                                        4 - Float

        Returns:
                The read file data in the requested value

        Raises:
            ValueError: the property type is of an unknown value
        """
        propertyValue: str | int | float
        if propertyType == -1:
            nameLength: int = handle.readByte()
            propertyValue = handle.readStringFromByte(nameLength)
        elif propertyType == 1:
            propertyValue = handle.readByte()
        elif propertyType == 2:
            propertyValue = handle.readInt()
        elif propertyType == 4:
            propertyValue = handle.readFloat()
        else:
            raise ValueError(f"Unkown value given: {propertyType}")
        return propertyValue

    def _readMarkers(self, handle:binaryFileReader.BinaryFileReader) -> None:
        """
        Reads and processes marker data from the C3D file.

        Args:
            handle (binaryFileReader.BinaryFileReader): The file handle for reading binary data.

        Returns:
            None
        """
        pointGroup: _internals.ParameterGroup | None = self.getParameterGroup("POINT")
        if pointGroup is None:
            return
        
        markers:_internals.ParameterBase | None = pointGroup.getParameter("LABELS")
        markers2:_internals.ParameterBase | None = pointGroup.getParameter("LABELS2")

        # Check if the file has markers
        if markers is None:
            return 
        
        # Create the markers
        markerName: str
        for markerName in markers.data():
            newMarker: _internals.Marker = _internals.Marker(markerName)
            self._markers.append(newMarker)
        
        if markers2 is not None:
            for markerName in markers2.data():
                newMarker: _internals.Marker = _internals.Marker(markerName)
                self._markers.append(newMarker)
        
        if len(self._markers) != self.getMarkerCount():
            raise ValueError("Marker count does not match the number of markers in the file")
        
        startOfDataBlock:int = (self._header.dataStart - 1) * 512
        handle.seek(startOfDataBlock)
        pointScale: float = pointGroup.getParameter("SCALE").data()
        
        numberOfDataPoints = ((self._header.lastFrame - self._header.firstFrame) * self.getMarkerCount()) * 4

        if pointScale < 0:
            data = handle.bulkReadFloat(numberOfDataPoints)
        else:
            data = [value * pointScale for value in handle.bulkReadInt(numberOfDataPoints)]
        
        # Process marker data in parallel using multiple threads
        markerCount = self.getMarkerCount()
        threads = []
        for markerIdx, marker in enumerate(self._markers):
            thread = threading.Thread(target=self.processMarkerData, args=(marker, data, markerIdx, markerCount))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    @staticmethod
    def _quickVec(data):
        """
        Create a Vector3 object from the given data.

        Args:
            data (list): A list of three values representing the x, y, and z coordinates of the vector.

        Returns:
            Vector3: A Vector3 object representing the vector.

        """
        if data[0] == 0 and data[1] == 0 and data[2] == 0:
            return  None
        vec = vector3.Vector3.__new__(vector3.Vector3)
        vec._data = data
        return vec
        
    @classmethod
    def processMarkerData(cls, marker, data, markerIdx, markerCount):
        """
        Process marker data and assign it to the marker object.

        Args:
            marker (Marker): The marker object to assign the processed data to.
            data (list): The raw marker data.
            markerIdx (int): The index of the marker.
            markerCount (int): The total number of markers.

        Returns:
            None
        """
        # This method is used to process marker data and assign it to the marker object.
        # It takes in the marker object, raw marker data, marker index, and total number of markers as parameters.
        # It creates a dictionary of marker data for each frame, where the frame number is the key and the processed marker data is the value.
        # The processed marker data is obtained by calling the _quickVec method on a subset of the raw marker data.
        # Finally, the processed marker data is assigned to the marker object.
        markerData = {frame: cls._quickVec(data[idx + markerIdx * 4 : idx + markerIdx * 4 + 4]) for frame, idx in enumerate(range(0, len(data), markerCount * 4))}
        marker._data = markerData

    def readFrame(self, frameNumber:int) -> list[vector3.Vector3 | None]:
        """ 
        Read a single frame of data for each marker.

        Args:
            frameNumber (int): The frame to get the data from.

        Returns:
            A list of vector3 objects, one for each of the markers.

        Raises:
            ValueError: if the given frame is not within the frame range of the c3d file
        """
        if frameNumber < self._header.firstFrame or frameNumber > self._header.lastFrame:
            raise ValueError("Invalid Frame Number")
        return [marker.getPosition(frameNumber) for marker in self._markers]

    def iterFrame(self, start:int|None=None, end:int|None=None, iterJump:int=1):
        """
        Iterate through all the frames in the c3d file. Allows for specifying 
        the start and stop frame as well as frame skip number

        Args:
            start (int): The start frame to use (Optional)
            end (int): The end frame to use (Optional)
            iterJump (int): The number of frames to skip (Optional)

        Returns:
            a list of lists of vector3 objects, one for each of the markers at each frame
        """
        firstFrame: int = start or self._header.firstFrame
        lastFrame: int = end or (self._header.lastFrame + 1)
        for frame in range(firstFrame, lastFrame, iterJump):
            yield self.readFrame(frame)

    def getMarkerCount(self) -> int:
        """ 
        Get the marker count

        Returns:
            The number of markers in the c3d file as a int
        """
        return self._header.markerCount

    def getMarkersNames(self) -> list[str]:
        """ 
        Get a list of the markers names from the c3d file

        Returns:
            A list of marker names from the loaded c3d file.
        """
        return [marker.markerName() for marker in self._markers]

    def getMarkers(self) -> list[_internals.Marker]:
        """ Get a list of the markers from the c3d file"""
        return list(self._markers)

    def getMarker(self, markerName:str) -> _internals.Marker | None:
        """ Get a marker from the c3d file based on the marker name"""
        for marker in self._markers:
            if marker.markerName() == markerName:
                return marker
        return None

    def addMarker(self, markerName:str) -> _internals.Marker:
        """ Add a new marker to the c3d file with the given name"""
        newMarker: _internals.Marker = _internals.Marker(markerName)
        self._markers.append(newMarker)
        return newMarker

    def removeMarker(self, markerName:str) -> None:
        """ Remove a marker from the c3d file based on the marker name"""
        marker: _internals.Marker | None = self.getMarker(markerName)
        if marker is not None:
            self._markers.remove(marker)

    def getFrameStart(self) -> int:
        """ 
        Get the frame start of the c3d file

        Returns:
            The frame start as a int
        """
        return self._header.firstFrame

    def getFrameEnd(self) -> int:
        """ 
        Get the frame end of the c3d file

        Returns:
            The end start as a int
        """
        return self._header.lastFrame

    def getSampleRate(self) -> float:
        """ 
        Get the sample ratge of the c3d file

        Returns:
            The c3d file sameple rate as a float
        """
        return self._header.frameRate

    def getParameterGroupsNames(self) -> list[str]:
        """ 
        List all the parameters in the c3d

        Returns:
            a string list of all the parameters in the c3d file
        """
        return [param.name() for param in self._parameters]

    def getParameterGroups(self) -> list[_internals.ParameterGroup]:
        """ Get a list of the parameters in the c3d file"""
        return self._parameters

    def getParameterGroup(self, name:str) -> _internals.ParameterGroup | None:
        """ Get a parameter from the c3d file based on the parameter name"""
        for param in self._parameters:
            if param.name() == name:
                return param
        return None

    def getParametersInGroup(self, parameterGroupName:str) -> list[str]:
        """ 
        List all the properties in the given parameter.

        Args:
            parameter (str): The parameter that you want the properties of

        Returns:
            A list of properties within the parameters as strings
        """
        paramGrp: _internals.ParameterGroup | None = self.getParameterGroup(parameterGroupName)
        if paramGrp is None:
            raise ValueError("Parameter not found in file")
        return [param.name() for param in paramGrp.getParameters()]

    def getParameterDict(self) -> dict[str, object]:
        """ 
        Returns a copy of the internal parameter dict

        Returns:
            A two level nested dict of parameter, property & value key pairs
        """
        returnDict: dict[str, object] = {}
        for paramGrp in self._parameters:
            returnDict[paramGrp.name()] = dict([(param.name(), param.data()) for param in paramGrp.getParameters()])
        return returnDict

    def getParameter(self, parameterGroup:str, parameterProperty:str) -> _internals.ParameterBase:
        """ 
        Get the value of the property within the parameter. Can return a string, int, long or float 
        depending on what the value is

        Args:
            parameter (str): The parameter that you want the properties of
            pramProperty (str): The property from the parameter

        Returns:
            A list of properties within the parameter as strings
        """
        paramGrp: _internals.ParameterGroup | None = self.getParameterGroup(parameterGroup)
        if paramGrp is None:
            raise AttributeError("Parameter group %r not found" % parameterGroup)
        parameter: _internals.ParameterGroup | None = paramGrp.getParameter(parameterProperty)
        if parameter is None:
            raise AttributeError("Property %r not found in Group %s" % (parameterProperty, parameterGroup))
        return parameter

    def getParameterValue(self, parameterGroup:str, parameterProperty:str) -> object:
        """ 
        Get the value of the property within the parameter. Can return a string, int, long or float 
        depending on what the value is

        Args:
            parameter (str): The parameter that you want the properties of
            pramProperty (str): The property from the parameter

        Returns:
            A list of properties within the parameter as strings
        """
        return self.getParameter(parameterGroup, parameterProperty).data()
    
