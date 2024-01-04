import sys
import os

from maya.api import OpenMaya, OpenMayaAnim
from maya import OpenMayaMPx, cmds, mel
from pyC3D import c3dFile


class _MayaMarker(object):
    """
    Represents a marker in Maya for importing motion capture data.
    """

    def __init__(self, marker, parent, frameRateConversion):
        super().__init__()
        self._marker = marker
        self._frameRateConversion = frameRateConversion
        name = self._marker.markerName().replace("-", "_").replace(":", "_").replace("*", "Untitled_")
        
        self._name, self._mObject = self._createMocapMarker(name, parent)
        
        # Get all the translate attributes
        self._translateX = self._createAnimCurveForAttribute("translateX")
        transXData = {frame: pos.x() for frame, pos in marker._data.items() if pos is not None}

        self._translateY = self._createAnimCurveForAttribute("translateY")
        transYData = {frame: pos.y() for frame, pos in marker._data.items() if pos is not None}
        
        self._translateZ = self._createAnimCurveForAttribute("translateZ")
        transZData = {frame: pos.z() for frame, pos in marker._data.items() if pos is not None}
        
        self.setPositionData(transXData, transYData, transZData)

    def _createAnimCurveForAttribute(self, attribute:str) -> OpenMayaAnim.MFnAnimCurve:
        """
        Creates an animation curve for the given attribute.

        Args:
            attribute: The name of the attribute.

        Returns:
            The created animation curve.
        """
        node = OpenMaya.MFnDependencyNode(self._mObject)
        plug = node.findPlug(node.attribute(attribute), True)
        animCurve = OpenMayaAnim.MFnAnimCurve()
        animCurve.create(plug, OpenMayaAnim.MFnAnimCurve.kAnimCurveTL)
        return animCurve

    def setPositionData(self, xDict, yDict, zDict):
        """
        Sets the position data for the marker.

        Args:
            xDict: A dictionary containing the X position data for each frame.
            yDict: A dictionary containing the Y position data for each frame.
            zDict: A dictionary containing the Z position data for each frame.
        """
        for curve, data in zip([self._translateX, self._translateY, self._translateZ], [xDict, yDict, zDict]):
            timeArray = OpenMaya.MTimeArray()
            valueArray = OpenMaya.MDoubleArray()
            for key, value in data.items():
                timeArray.append(OpenMaya.MTime(self._frameRateConversion * key, OpenMaya.MTime.uiUnit()))
                valueArray.append(value)
            # Add the keys to the animCurve.
            curve.addKeys(
                timeArray,
                valueArray,
                OpenMayaAnim.MFnAnimCurve.kTangentGlobal,
                OpenMayaAnim.MFnAnimCurve.kTangentGlobal,
                False,
            )

    def _createMocapMarker(self, markerName, parent):
        """
        Creates a mocap marker in Maya.

        Args:
            markerName: The name of the marker.
            parent: The parent object of the marker.

        Returns:
            The name and MObject of the created marker.
        """
        tempName, mObject = self.createCube()
        cmds.rename(tempName, markerName)
        cmds.parent(markerName, parent)
        return markerName, mObject

    @staticmethod
    def createCube(scale:float=10)  -> tuple[str, OpenMaya.MObject]:
        """
        Creates a cube in Maya.

        Args:
            scale: The scale of the cube.

        Returns:
            The name and MObject of the created cube.
        """
        temp = cmds.curve(d=1,
                            p=[
                                (1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, 1, 1) , (1, 1, 1),
                                (1, -1, 1), (1, -1, -1), (-1, -1, -1), (-1, -1, 1) , (1, -1, 1),
                                (1, -1, -1), (1, -1, 1), (1, 1, 1) , (1, 1, -1), (1, -1, -1),
                                (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)
                            ]
                        )
        cmds.setAttr(f"{temp}.scaleX", scale)
        cmds.setAttr(f"{temp}.scaleY", scale)
        cmds.setAttr(f"{temp}.scaleZ", scale)
        
        selection = OpenMaya.MSelectionList()
        selection.add(temp)
        return temp, selection.getDependNode(0)
    

# Node definition
class C3D_file_translator(OpenMayaMPx.MPxFileTranslator):
    NAME: str = "C3D"

    def haveWriteMethod(self) -> bool:
        # The plugin does not write files
        return False

    def haveReadMethod(self):
        return True

    def filter(self):
        return "*.c3d"

    def defaultExtension(self):
        return "c3d"

    def writer(self, fileObject, optionString, accessMode):
        raise IOError("This plugin does not write files")

    def reader(self, fileObject, optionString, accessMode):
        try:
            fileData: c3dFile.C3DFile = c3dFile.C3DFile(fileObject.fullName())
            sceneFrameRate = mel.eval('currentTimeUnitToFPS')

            frameRate = fileData.getSampleRate()
            frameRateConversion = (sceneFrameRate / frameRate)
            startFrame = frameRateConversion * fileData.getFrameStart()
            endFrame = frameRateConversion * fileData.getFrameEnd()

            cmds.playbackOptions(minTime=startFrame, maxTime=endFrame)

            fileName = os.path.splitext(os.path.basename(fileObject.fullName()))[0]
            fileName = fileName.replace("-", "_").replace(":", "_").replace("*", "Untitled_")

            root = cmds.spaceLocator(p=[0, 0, 0], name=f"C3DOpticalRoot_{fileName}")[0]

            markers = [_MayaMarker(markerName, root, frameRateConversion) for markerName in fileData.getMarkers()]
            
            scale = 0.02
            cmds.setAttr(f"{root}.scaleX", scale)
            cmds.setAttr(f"{root}.scaleY", scale)
            cmds.setAttr(f"{root}.scaleZ", scale) 
        except:
            sys.stderr.write("Failed to read file information\n")
            raise

def translatorCreator():
    "Create an instance of the translator"
    return OpenMayaMPx.asMPxPtr(C3D_file_translator())


def initializePlugin(mobject: OpenMaya.MObject):
    "Initialize the script plug-in"
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerFileTranslator(
            C3D_file_translator.NAME, None, translatorCreator
        )
    except:
        sys.stderr.write(f"Failed to register translator: {C3D_file_translator.NAME}")
        raise


def uninitializePlugin(mobject: OpenMaya.MObject):
    "Uninitialize the script plug-in"
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterFileTranslator(C3D_file_translator.NAME)
    except:
        sys.stderr.write(f"Failed to deregister translator: {C3D_file_translator.NAME}")
        raise
