bl_info = {
    "name": "Match Area Light",
    "author": "Anthony Aragues",
    "version": (1, 2),
    "blender": (2, 90, 0),
    "location": "n > Lights",
    "description": "Rapidly create area lights to match size and orientation of selected faces",
    "warning": "",
    "doc_url": "",
    "category": "Lighting",
}

# This example assumes we have a mesh object in edit-mode

import bpy, bmesh
from mathutils import Vector, Matrix

'''
import bpy
import bmesh
context = bpy.context

ob = context.edit_object
mw = ob.matrix_world
me = ob.data
bm = bmesh.from_edit_mesh(me)

faces = [f for f in bm.faces if f.select]

while faces:
    f = faces.pop()
    light = bpy.data.lights.new(
            f"Face{f.index}",
            type='AREA',
            )
    light.size = 1
    light_ob = bpy.data.objects.new(
            f"Face{f.index}",
            light,
            )
    M = mw.normalized() @ f.normal.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    M.translation = mw @ f.calc_center_median()
    light_ob.matrix_world = M
    context.collection.objects.link(light_ob)
'''


def fnGetScale(objFace):
    intMinX = None
    intMinY = None
    intMinZ = None
    intMaxX = None
    intMaxY = None
    intMaxZ = None
    for objVert in objFace.verts:
        #coordinates per point per face of selected object
        arrCo=objVert.co.to_tuple()
        if intMinX == None or arrCo[0] < intMinX:
            intMinX=arrCo[0]
        if intMaxX == None or arrCo[0] > intMaxX:
            intMaxX=arrCo[0]
        if intMinY == None or arrCo[1] < intMinY:
            intMinY=arrCo[1]
        if intMaxY == None or arrCo[1] > intMaxY:
            intMaxY=arrCo[1]
        if intMinZ == None or arrCo[2] < intMinZ:
            intMinZ=arrCo[2]
        if intMaxZ == None or arrCo[2] > intMaxZ:
            intMaxZ=arrCo[2]
    return {"x":intMaxX-intMinX,"y":intMaxY-intMinY,"z":intMaxZ-intMinZ}

class LightsOp(bpy.types.Operator):
    bl_idname = 'lights.go'
    bl_label = 'Map Area Light to All Selected'
    
    #this is the operator function that will be called on button press
    def execute(self, context):

        # Get the active mesh
        obj = context.edit_object
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.editmode_toggle()
        objMesh = bmesh.from_edit_mesh(obj.data)
        #create the lights
        arrLights=[]
        for objFace in objMesh.faces:
            if objFace.select == True:
                objLight={'location':{}, 'direction':{}, 'matrix':{}, 'scale':{'x':0,'y':0,'z':0}}
                objCenter= objFace.calc_center_median()
                objLight['location']=objCenter.to_tuple()
                objLight['direction']=objFace.normal
                intMinX = None
                intMinY = None
                intMinZ = None
                intMaxX = None
                intMaxY = None
                intMaxZ = None
                for objVert in objFace.verts:
                    #coordinates per point per face of selected object
                    arrCo=objVert.co.to_tuple()
                    if intMinX == None or arrCo[0] < intMinX:
                        intMinX=arrCo[0]
                    if intMaxX == None or arrCo[0] > intMaxX:
                        intMaxX=arrCo[0]
                    if intMinY == None or arrCo[1] < intMinY:
                        intMinY=arrCo[1]
                    if intMaxY == None or arrCo[1] > intMaxY:
                        intMaxY=arrCo[1]
                    if intMinZ == None or arrCo[2] < intMinZ:
                        intMinZ=arrCo[2]
                    if intMaxZ == None or arrCo[2] > intMaxZ:
                        intMaxZ=arrCo[2]
                objLight['scale']['x'] = intMaxX-intMinX
                objLight['scale']['y'] = intMaxY-intMinY
                objLight['scale']['z'] = intMaxZ-intMinZ
                objMatrix=obj.matrix_world.normalized() @ objFace.normal.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
                objMatrix.translation = obj.matrix_world @ objFace.calc_center_median()
                objLight['matrix']=objMatrix
                print(objLight)
                arrLights.append(objLight)
                
        bpy.ops.object.editmode_toggle()
        for intLight,objLight in enumerate(arrLights):
            objNewLight=bpy.ops.object.light_add(type='AREA', radius=1, align='WORLD', location=objLight['location'])
            #  set the rotation the light in the direction of the normal
            context.object.matrix_world=objLight['matrix']
            #bpy.context.object.rotation_mode = 'QUATERNION'
            #bpy.context.object.rotation_quaternion = objLight['direction'].to_track_quat('Z','Y')
            #bpy.context.object.scale( objLight['scale']['x'],objLight['scale']['y'],objLight['scale']['z'] )
            bpy.ops.transform.resize(value=(objLight['scale']['x']/1, objLight['scale']['y']/1, objLight['scale']['z']/1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), 
            orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        return {"FINISHED"}
                                
class LightsPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Light"
    bl_category = "Lights"
    bl_idname = "Light_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        #start with first camera found
        row = layout.row()
        row.label(text="Create area lights from faces")
        row = layout.row()
        row.label(text="1. Selected faces in edit mode")
        row = layout.row()
        row.label(text="2. Run the tool")
        layout.operator("lights.go",text = 'Create area lights')
                                
def register():
    bpy.utils.register_class(LightsOp)
    bpy.utils.register_class(LightsPanel)


def unregister():
    bpy.utils.unregister_class(LightsOp)
    bpy.utils.unregister_class(LightsPanel)

if __name__ == "__main__":
    register()
