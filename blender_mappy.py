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

class MappyOp(bpy.types.Operator):
    bl_idname = 'mappy.go'
    bl_label = 'Map Image to All Selected'
    
    #this is the operator function that will be called on button press
    def execute(self, context):
        #default camera before finding the fspy one
        objCamera = bpy.data.cameras[0]
        #default blank image before finding the fspy one
        objImage = type('', (), {})()
        #default ratio before the image is foudn to calc from
        intRatioX = 1
        intRatioY = 1
        
        #Find the fspy camera that was imported by the fspy import plugin
        for obj in bpy.data.cameras:            
            for obj2 in obj.background_images:
                if obj2.source == 'IMAGE' and obj2.image and obj2.image.name and "fspy" in obj2.image.name:
                    objCamera = obj
                    objImage = obj2.image
                    self.report({'INFO'}, "fspy camera found: " + objCamera.name)
                    # use the image from the camera as the projection image
                    intX = bpy.data.images[obj2.image.name].size[0]
                    intY = bpy.data.images[obj2.image.name].size[1]
                    #calc the ratio for the camera uv project
                    if intX > intY:
                        intRatioX = intX/intY
                    else:
                        intRatioY = intY/intX 
                    self.report({'INFO'}, "fspy image found: " + obj2.image.name + " " + str(intX) + "," + str(intY))
                    self.report({'INFO'}, "ratio: " + str(intRatioX) + "," + str(intRatioY))
                    break
        
        # Get material if it exists, it shouldn't
        mat = bpy.data.materials.get("mappy_texture")
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="mappy_texture")
            mat.use_nodes = True
            mat.node_tree.nodes.remove( mat.node_tree.nodes['Principled BSDF'])
            nodeLinks = mat.node_tree.links
            nodeEmission = mat.node_tree.nodes.new(type='ShaderNodeEmission')
            nodeTexture = mat.node_tree.nodes.new(type='ShaderNodeTexImage')
            nodeTexture.image = objImage
            nodeOutput = mat.node_tree.nodes['Material Output']
            nodeLinks.new(nodeEmission.outputs[0], nodeOutput.inputs[0])
            nodeLinks.new(nodeTexture.outputs[0], nodeEmission.inputs[0])
        
        for obj in bpy.context.selected_objects:
            self.report({'INFO'}, "applying fspy settings to object: " + obj.name)
            objTarget = bpy.data.objects[obj.name]
            objTarget.modifiers.new("mappy_subsurf",type='SUBSURF')
            objTarget.modifiers["mappy_subsurf"].subdivision_type = 'SIMPLE'
            
            objTarget.modifiers.new("mappy_project",type='UV_PROJECT')
            objTarget.modifiers["mappy_project"].aspect_x = intRatioX
            objTarget.modifiers["mappy_project"].aspect_y = intRatioY
            # this assumes the projector image name is the same as the same as the projector image name
            objTarget.modifiers["mappy_project"].projectors[0].object = bpy.data.objects[objImage.name]
            # Assign material to object
            if objTarget.data.materials:
                # assign to 1st material slot
                objTarget.data.materials[0] = mat
            else:
                # no slots
                objTarget.data.materials.append(mat)
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
    