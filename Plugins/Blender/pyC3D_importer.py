import os
import sys

import bpy
from bpy import props, types
from bpy_extras import io_utils

from pyC3D import c3dFile, _internals


class _Marker(object):
    """
    Represents a marker in Blender for importing motion capture data.
    """

    def __init__(self, marker: _internals.Marker, parent:types.Object, frameRateConversion:float):
            """
            Initializes an instance of the pyC3D_importer class.

            Args:
                marker: The marker object.
                parent: The parent object.
                frameRateConversion: The frame rate conversion value.
            """
            super().__init__()
            self._marker = marker
            self._frameRateConversion = frameRateConversion
            name = self._marker.markerName().replace("-", "_").replace(":", "_").replace("*", "Untitled_")
            
            self._obj = self._createMocapMarker(name, parent)

            self._xCurve = self.makeOrGetFcurve(self._obj, "location", index=0)
            self._yCurve = self.makeOrGetFcurve(self._obj, "location", index=1)
            self._zCurve = self.makeOrGetFcurve(self._obj, "location", index=2)
            
            # Get all the translate attributes
            frameData = {frame: [pos.x(), pos.y(), pos.z()] for frame, pos in marker._data.items() if pos is not None}
            
            self.setPositionData(frameData)

            scale = 20
            self._obj.scale = [scale, scale, scale]

    def setPositionData(self, frameData: dict[int, list[float]]) -> None:
        """
        Sets the position data for each frame.

        Args:
            frameData (dict): A dictionary containing frame index as keys and position values as values.

        Returns:
            None
        """
        for frameIndex, frameValue in frameData.items():
            frame = self._frameRateConversion * frameIndex
            self._xCurve.keyframe_points.insert(frame, frameValue[0])
            self._yCurve.keyframe_points.insert(frame, frameValue[1])
            self._zCurve.keyframe_points.insert(frame, frameValue[2])

    def makeOrGetFcurve(self, obj:types.Object, dataPath:str, index:int=-1) -> bpy.types.FCurve:
        """
        Creates or retrieves an F-curve for the specified object, data path, and index.

        Args:
            obj: The object to create or retrieve the F-curve for.
            dataPath: The data path of the F-curve.
            index: The index of the F-curve. Defaults to -1.

        Returns:
            bpy.types.FCurve: The created or retrieved F-curve.
        """

        # freshly created objects don't have animation_data yet.
        if obj.animation_data is None:
            obj.animation_data_create()
        ad=obj.animation_data
        if ad.action is None:
            ad.action = bpy.data.actions.new(f"{obj.name}Action")

        for fc in ad.action.fcurves:
            if (fc.data_path != dataPath):
                continue
            if index<0 or index==fc.array_index:
                return fc
        # the action didn't have the fcurve we needed, yet
        return ad.action.fcurves.new(dataPath, index=index)

    def _createMocapMarker(self, markerName:str, parent:types.Object) -> types.Object:
        """
        Creates a mocap marker in Blender.

        Args:
            markerName: The name of the marker.
            parent: The parent object of the marker.

        Returns:
            The name and MObject of the created marker.
        """
        bpy.ops.object.empty_add(type='CUBE', location=(0, 0, 0))
        newMarker = bpy.context.active_object
        newMarker.name = markerName
        if parent is not None:
            newMarker.parent = parent
        return newMarker


class C3DImporter(types.Operator, io_utils.ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "c3d.importdata"  # important since its how bpy.ops.C3D.importData is constructed
    bl_label = "Import C3D Motion Data"

    # ImportHelper mix-in class uses this.
    filename_ext = ".c3d"

    filter_glob: props.StringProperty(
        default="*.c3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        try:
            fileData: c3dFile.C3DFile = c3dFile.C3DFile(self.filepath)
            sceneFrameRate = bpy.context.scene.render.fps

            frameRate = fileData.getSampleRate()
            frameRateConversion = (sceneFrameRate / frameRate)
            startFrame = frameRateConversion * fileData.getFrameStart()
            endFrame = frameRateConversion * fileData.getFrameEnd()

            bpy.context.scene.frame_start = int(startFrame)
            bpy.context.scene.frame_end = int(endFrame)

            fileName = os.path.splitext(os.path.basename(self.filepath))[0]
            fileName = fileName.replace("-", "_").replace(":", "_").replace("*", "Untitled_")

            root = bpy.data.objects.new("PLAIN_AXES", None)
            bpy.context.scene.collection.objects.link(root)
            root.name=f"C3DOpticalRoot_{fileName}"

            markers = [_Marker(markerName, root, frameRateConversion) for markerName in fileData.getMarkers()]
            
            scale = 0.02
            root.scale = [scale, scale, scale]
            
        except:
            sys.stderr.write("Failed to read file information\n")
            raise
        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(C3DImporter.bl_idname, text="C3D File Importer")


# Register and add to the "file selector" menu (required to use F3 search "C3D File Importer" for quick access).
def register():
    bpy.utils.register_class(C3DImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(C3DImporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.c3d.importdata('INVOKE_DEFAULT')
