import bpy

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


bl_info = {
	"name": "Toontown XSI Importer",
	"author": "chrismoliere29@gmail.com",
	"version": (1, 0, 0),
	"blender": (5, 1, 0),
	"location": "File > Import-Export",
	"description": "Toontown Online .XSI Importer",
	"category": "Import-Export"
}

if "loaded" in locals():
    import imp
    imp.reload(xsi_parser)
    imp.reload(xsi_importer)
else:
    from . import xsi_parser
    from . import xsi_importer

class ImportXSI(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.some_xsi"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Toontown XSI"

    # ImportHelper mix-in class uses this.
    filename_ext = ".xsi"

    filter_glob: StringProperty(
        default="*.xsi",
        options={'HIDDEN'},
        maxlen=255,
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    import_animations: BoolProperty(
        name="Import XSI",
        description="Import Toontown Online XSI",
        default=True,
    )


    def execute(self, context):
        filepath = self.filepath
        animProp = self.import_animations
        return xsi_importer.load(context, self.filepath, animProp)


    # Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportXSI.bl_idname, text="Toontown XSI Importer (.xsi)")

def register():
    bpy.utils.register_class(ImportXSI)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportXSI)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()