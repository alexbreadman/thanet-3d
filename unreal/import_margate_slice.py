"""Import the Margate slice into Unreal and light it. Run inside the UE editor:

    Window > Developer Tools > Output Log >  cmd dropdown: Python
    then:  exec(open(r"<path-to-this-file>").read())

or headless:
    UnrealEditor-Cmd.exe <project.uproject> -run=pythonscript -script="<this file>"

Expects terrain.glb / buildings.glb / roads.glb in assets/geo/margate-slice/
(sibling of this file's folder, or set SLICE_DIR below).
Scene scale: glTF metres -> UE cm handled by the importer. Slice is ~1.5 km.
"""
import unreal
from pathlib import Path

SLICE_DIR = Path(__file__).resolve().parent.parent / "assets/geo/margate-slice"
DEST = "/Game/Thanet/MargateSlice"

# ---------------------------------------------------------------- import glbs
tasks = []
for name in ("terrain", "buildings", "roads"):
    src = SLICE_DIR / f"{name}.glb"
    if not src.exists():
        unreal.log_warning(f"missing {src}")
        continue
    t = unreal.AssetImportTask()
    t.filename = str(src)
    t.destination_path = f"{DEST}/{name}"
    t.automated = True
    t.save = True
    t.replace_existing = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

# ------------------------------------------------- place everything at origin
actors = unreal.EditorActorSubsystem()
placed = 0
registry = unreal.AssetRegistryHelpers.get_asset_registry()
for asset in registry.get_assets_by_path(unreal.Name(DEST), recursive=True):
    if asset.asset_class_path.asset_name == "StaticMesh":
        mesh = asset.get_asset()
        a = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0))
        a.set_actor_label(str(asset.asset_name))
        placed += 1
unreal.log(f"placed {placed} meshes")

# ------------------------------------------------------------------- lighting
def spawn(cls, label, **props):
    a = actors.spawn_actor_from_class(cls, unreal.Vector(0, 0, 5000))
    a.set_actor_label(label)
    return a

sun = spawn(unreal.DirectionalLight, "Sun")
sun.set_actor_rotation(unreal.Rotator(-40, 35, 0), False)
sun.directional_light_component.set_intensity(8.0)
sun.directional_light_component.set_editor_property(
    "atmosphere_sun_light", True)
spawn(unreal.SkyAtmosphere, "SkyAtmosphere")
sky = spawn(unreal.SkyLight, "SkyLight")
sky.sky_light_component.set_editor_property("real_time_capture", True)
fog = spawn(unreal.ExponentialHeightFog, "Fog")
fog.component.set_editor_property("fog_density", 0.008)

# --------------------------------------------------------------- screenshots
# UE axes after glTF import: X = gltf x (east), Y = gltf -z (north... UE Y is
# right/south-ish depending on conversion). If the view is mirrored, negate Y.
les = unreal.UnrealEditorSubsystem()
shots = [
    ("ue_harbour",  unreal.Vector(115000, 145000, 9000),
     unreal.Rotator(-15, -125, 0)),
    ("ue_overview", unreal.Vector(190000, -25000, 62000),
     unreal.Rotator(-25, 140, 0)),
]
for name, loc, rot in shots:
    les.set_level_viewport_camera_info(loc, rot)
    unreal.AutomationLibrary.take_high_res_screenshot(
        1600, 900, f"{name}.png")
unreal.log("done — screenshots land in <Project>/Saved/Screenshots/")
