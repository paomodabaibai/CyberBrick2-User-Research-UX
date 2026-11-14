from pathlib import Path
import trimesh,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[2]
m=trimesh.load_mesh(P/'01_研究参考/robot-battle-reference/Otto-V9/3Dprint/OttoDIY_body_V9.stl')
m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]))
fig,axs=plt.subplots(2,3,figsize=(12,8))
for ax,z in zip(axs.flat,[-37,-30,-23,-16,-9,-2]):
 s=trimesh.intersections.mesh_plane(m,plane_origin=[0,0,z],plane_normal=[0,0,1])
 for line in s: ax.plot(line[:,0],line[:,1],color='blue')
 ax.set(xlim=(-40,40),ylim=(-40,40),title=f'Z={z}; X front, Y left');ax.set_aspect('equal');ax.grid()
fig.savefig(Path(__file__).with_name('旧身体水平剖面.png'),dpi=130)
