bl_info = {
    "name": "Mappy for FSpy",
    "author": "Anthony Aragues",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "n > Mappy > Mesh > New Object",
    "description": "Automates the Blender side of a FSpy workflow for all selected objects",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy
from mathutils import Vector

class MappyOp(bpy.types.Operator):
    bl_idname = 'mappy.go'
    bl_label = 'Map Image to All Selected'
    
    #this is the operator function that will be called on button press
    def execute(self, context):
        arrPerspectives=[]
        
        #Find the fspy camera that was imported by the fspy import plugin
        for objCamera in bpy.data.cameras:            
            for objImage in objCamera.background_images:
                if objImage.source == 'IMAGE' and objImage.image and objImage.image.name and "fspy" in objImage.image.name:
                    self.report({'INFO'}, "fspy camera found: " + objCamera.name)
                    objPerspective={'camera':{}, 'image':{}, 'ratioX':1, 'ratioY':1, 'material':{} }
                    objPerspective['camera']=objCamera
                    objPerspective['image']=objImage.image
                    #self.report({'INFO'}, "fspy camera found: " + objCamera.name)
                    # use the image from the camera as the projection image
                    intX = bpy.data.images[objPerspective['image'].name].size[0]
                    intY = bpy.data.images[objPerspective['image'].name].size[1]
                    #calc the ratio for the camera uv project
                    if intX > intY:
                        objPerspective['ratioX'] = intX/intY
                    else:
                        objPerspective['ratioY'] = intY/intX 
                    #self.report({'INFO'}, "fspy image found: " + objPerspective['image'].name + " " + str(intX) + "," + str(intY))
                    #self.report({'INFO'}, "ratio: " + str(objPerspective['ratioX']) + "," + str(objPerspective['ratioY']))
                    #add the perspective to the collection
                    arrPerspectives.append(objPerspective)
                    break
        
        # create the material to match each perspective
        for intIndex,objPerspective in enumerate(arrPerspectives):
            # does it already exist for some reason? it shouldn't, doesnt hurt to check first
            objMaterial = bpy.data.materials.get(objPerspective['image'].name+"_texture")
            if objMaterial is None:
                # create material
                objMaterial = bpy.data.materials.new(name=objPerspective['image'].name+"_texture")
                objMaterial.use_nodes = True
                objMaterial.node_tree.nodes.remove( objMaterial.node_tree.nodes['Principled BSDF'])
                nodeLinks = objMaterial.node_tree.links
                nodeEmission = objMaterial.node_tree.nodes.new(type='ShaderNodeEmission')
                nodeTexture = objMaterial.node_tree.nodes.new(type='ShaderNodeTexImage')
                nodeTexture.image = objPerspective['image']
                nodeOutput = objMaterial.node_tree.nodes['Material Output']
                nodeLinks.new(nodeEmission.outputs[0], nodeOutput.inputs[0])
                nodeLinks.new(nodeTexture.outputs[0], nodeEmission.inputs[0])
            arrPerspectives[intIndex]['material']=objMaterial

        #per selected object operations
        for obj in bpy.context.selected_objects:
            self.report({'INFO'}, "applying fspy settings to object: " + obj.name)
            objTarget = bpy.data.objects[obj.name]
            #just in case non meshes are also selected
            #self.report({'INFO'}, objTarget.type)
            if objTarget.type == 'MESH':
                # add the subrface modifier
                objModifier=objTarget.modifiers.get("mappy_subsurf")
                if objModifier is None:
                    objTarget.modifiers.new("mappy_subsurf",type='SUBSURF')
                    objTarget.modifiers["mappy_subsurf"].subdivision_type = 'SIMPLE'
                # per perspective
                for intPerspective,objPerspective in enumerate(arrPerspectives):
                    # TIL I want multiple projectors in 1 modifier not 3 modifiers
                    objModifier=objTarget.modifiers.get("mappy_project")
                    if objModifier is None:
                        # add the uv project modifier per object + perspective
                        objTarget.modifiers.new("mappy_project",type='UV_PROJECT')
                        # add the ratio settings per projector
                        objTarget.modifiers["mappy_project"].aspect_x = objPerspective['ratioX']
                        objTarget.modifiers["mappy_project"].aspect_y = objPerspective['ratioY']
                        # set uv projection image
                        objTarget.modifiers["mappy_project"].projectors[0].object = bpy.data.objects[objPerspective['image'].name]
                    else:
                        # add image/perspctives as new projectors in the modifier
                        objModifier.projector_count = intPerspective + 1
                        objModifier.projectors[intPerspective].object = bpy.data.objects[objPerspective['image'].name]
                        
                    #create the material slots
                    self.report({'INFO'}, "applying material" + str(objPerspective['material'].name) + "to: " + objTarget.name )
                    # Assign material to object
                    # bpy.ops.object.material_slot_add()
                    # bpy.ops.object.material_slot_assign()
                    # 
                    
                    # loop through points in polygons + cameras to determine which camera is facing most directly, least shear, assign texture from that cameras projection
                    objCamera=bpy.data.objects[objPerspective['image'].name]
                    for objPolygon in objTarget.data.polygons:
                        intMin=None
                        intMax=0
                        intTotal=0
                        intDistance=0
                        for intPoint in objPolygon.vertices:# this only works because the image name is the same as the camer parent object that has the location.
                            objPoint=objTarget.data.vertices[intPoint]
                            intPointDistance2Camera=(objCamera.location-objPoint.co).length
                            intTotal = intPointDistance2Camera+intTotal
                            if intPointDistance2Camera > intMax:
                                intMax = intPointDistance2Camera
                            if intMin == None or intMin < intMin:
                                intMin = intPointDistance2Camera
                            # update the average distance
                            intDistance = intTotal / (intPoint+1)
                        self.report({'INFO'}, "camera to polygon sheer: "+ str(intMax-intMin) + 'average distance: '+ str(intDistance) )
                    if objTarget.data.materials:
                        # assign to 1st material slot
                        objTarget.data.materials[0] = objPerspective['material']
                    else:
                        # no slots
                        objTarget.data.materials.append(objPerspective['material'])
        return {"FINISHED"}


class MappyPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Mappy"
    bl_category = "Mappy"
    bl_idname = "Mappy_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        #start with first camera found
        row = layout.row()
        row.label(text="Mappy is intended to be the 3rd step in an FSpy workflow")
        row = layout.row()
        row.label(text="1. Import an FSpy project with the fspy import addon")
        row = layout.row()
        row.label(text="2. Model your objects to fit the image")
        row = layout.row()
        row.label(text="3. Use this addon to project / taxture map onto the selected objects")
        layout.operator("mappy.go",text = 'Map fspy image to all selected')
                                
def register():
    bpy.utils.register_class(MappyOp)
    bpy.utils.register_class(MappyPanel)


def unregister():
    bpy.utils.unregister_class(MappyOp)
    bpy.utils.unregister_class(MappyPanel)


if __name__ == "__main__":
    register()
    