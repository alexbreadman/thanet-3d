"""Build the Isle of Thanet level in Unreal from the web tile kit.

Run inside the UE editor (any 5.3+):
  Output Log -> switch the console dropdown from Cmd to Python -> paste:
      exec(open(r"C:/thanet-unreal-kit/import_thanet.py").read())
  (adjust the path to wherever the kit folder sits)

Imports every tile GLB (LOD0 where present, else LOD1), places them at the
origin (coordinates are baked into the meshes), adds sun/sky/fog/water and a
PlayerStart 250 m over Margate harbour. Press Play and fly: WASD + mouse,
E/Q up/down. First import takes a few minutes for ~500 meshes.
"""
import json
import unreal
from pathlib import Path

KIT = Path(__file__).resolve().parent
TILES = KIT / "tiles"
DEST = "/Game/Thanet"

index = json.loads((TILES / "index.json").read_text())

# ---------------------------------------------------------------- import
tasks = []
for t in index["tiles"]:
    name = f"t{t['x']}_{t['y']}.glb"
    src = TILES / "lod0" / name
    if not src.exists():
        src = TILES / "lod1" / name
    if not src.exists():
        continue
    task = unreal.AssetImportTask()
    task.filename = str(src)
    task.destination_path = f"{DEST}/tiles"
    task.automated = True
    task.save = False
    task.replace_existing = True
    tasks.append(task)
unreal.log(f"importing {len(tasks)} tiles…")
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

# ----------------------------------------------------------------- place
actors = unreal.EditorActorSubsystem()
registry = unreal.AssetRegistryHelpers.get_asset_registry()
placed = 0
for asset in registry.get_assets_by_path(unreal.Name(f"{DEST}/tiles"),
                                         recursive=True):
    if asset.asset_class_path.asset_name == "StaticMesh":
        a = actors.spawn_actor_from_object(asset.get_asset(),
                                           unreal.Vector(0, 0, 0))
        a.set_actor_label(str(asset.asset_name))
        placed += 1
unreal.log(f"placed {placed} tile meshes")

# -------------------------------------------------------------- lighting
def spawn(cls, label, loc=unreal.Vector(0, 0, 5000)):
    a = actors.spawn_actor_from_class(cls, loc)
    a.set_actor_label(label)
    return a

sun = spawn(unreal.DirectionalLight, "Sun")
sun.set_actor_rotation(unreal.Rotator(-42, 30, 0), False)
sun.directional_light_component.set_intensity(7.0)
sun.directional_light_component.set_editor_property("atmosphere_sun_light",
                                                    True)
spawn(unreal.SkyAtmosphere, "SkyAtmosphere")
sky = spawn(unreal.SkyLight, "SkyLight")
sky.sky_light_component.set_editor_property("real_time_capture", True)
fog = spawn(unreal.ExponentialHeightFog, "Fog")
fog.component.set_editor_property("fog_density", 0.006)

# water: a huge flat plane at ODN water level (glTF metres -> UE cm)
water_z = index["water_level"] * 100
plane = actors.spawn_actor_from_object(
    unreal.load_asset("/Engine/BasicShapes/Plane"),
    unreal.Vector(1000000, 500000, water_z))
plane.set_actor_scale3d(unreal.Vector(2000, 2000, 1))
plane.set_actor_label("Water")
mat = unreal.load_asset("/Engine/EngineMaterials/WorldGridMaterial")
try:
    mid = plane.static_mesh_component.create_dynamic_material_instance(0, mat)
except Exception:
    pass

# ---------------------------------------- player start over Margate harbour
# glTF x=east, z=-north (metres); UE x=x*100, y=-z*100, z=y*100 (cm)
harbour_e, harbour_n, height = 13050, 9400, 250
spawn(unreal.PlayerStart, "StartOverMargate",
      unreal.Vector(harbour_e * 100, harbour_n * 100, height * 100))

unreal.log("done — press Play (Alt+P) and fly: WASD + mouse, E/Q for up/down")
