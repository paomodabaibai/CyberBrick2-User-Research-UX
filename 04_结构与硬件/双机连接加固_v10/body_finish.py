"""Fill inherited rear engraving flush; keep original connector cutouts."""
import trimesh

def block(bounds):
    lo,hi=bounds
    m=trimesh.creation.box(extents=[b-a for a,b in zip(lo,hi)])
    m.apply_translation([(a+b)/2 for a,b in zip(lo,hi)])
    return m

def remove_rear_engraving(body):
    # Original rear face X=-34.5, engraved floor X=-34.1.
    patch=block(([-34.5,-18.2,-36.4],[-34.0,19.8,-29.7]))
    # Preserve v05 switch opening rather than refilling its overlapping corner.
    switch=block(([-44,-36.5,-31],[-22,-2.5,-8]))
    patch=trimesh.boolean.difference([patch,switch],engine='manifold')
    return trimesh.boolean.union([body,patch],engine='manifold')
