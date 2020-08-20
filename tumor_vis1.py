
from pyMCDS_cells import pyMCDS_cells
import numpy as np
from fury import window, actor, ui

#mcds = pyMCDS_cells('output00000001.xml','data')
mcds = pyMCDS_cells('output00000001.xml','.')  # 23123 cells
print('time=',mcds.get_time())

print(mcds.data['discrete_cells'].keys())
#Out[7]: dict_keys(['ID', 'position_x', 'position_y', 'position_z', 'total_volume', 'cell_type', 'cycle_model', 'current_phase', 'elapsed_time_in_phase', 'nuclear_volume', 'cytoplasmic_volume', 'fluid_fraction', 'calcified_fraction', 'orientation_x', 'orientation_y', 'orientation_z', 'polarity', 'migration_speed', 'motility_vector_x', 'motility_vector_y', 'motility_vector_z', 'migration_bias', 'motility_bias_direction_x', 'motility_bias_direction_y', 'motility_bias_direction_z', 'persistence_time', 'motility_reserved', 'oncoprotein', 'elastic_coefficient', 'kill_rate', 'attachment_lifetime', 'attachment_rate'])

# http://www.mathcancer.org/blog/paraview-for-physicell-part-1/

# The following lines assign an integer to represent
# a color, defined in a Color Map.
# sval = 0   # immune cells are yellow?
# if val[5,idx] == 1:  # [5]=cell_type
#   sval = 1   # lime green
# if (val[6,idx] == 6) or (val[6,idx] == 7):
#   sval = 0
# if val[7,idx] == 100:  # [7]=current_phase
#   sval = 3   # apoptotic: red
# if val[7,idx] > 100 and val[7,idx] < 104:
#   sval = 2   # necrotic: brownish

ncells = len(mcds.data['discrete_cells']['ID'])
print('num cells = ',ncells)

#xyz = np.empty((ncells,3))
xyz = np.zeros((ncells,3))
xyz[:,0] = mcds.data['discrete_cells']['position_x']
xyz[:,1] = mcds.data['discrete_cells']['position_y']
xyz[:,2] = mcds.data['discrete_cells']['position_z']
#xyz = np.random.rand((ncells,3))
#xyz[:,]

# sphere V = 4/3 * pi * r^3
# r3 = V * 0.75 / pi
# r = np.cbrt(r3)
cell_radii = mcds.data['discrete_cells']['total_volume'] * 0.75 / np.pi
cell_radii = np.cbrt(cell_radii)

cell_type = mcds.data['discrete_cells']['cell_type']
print(cell_type)
#cd8 = np.where(cell_type == 3.0)
#print('# cd8, macrophage, neutrophil = ',len(cd8[0]), len(macrophage[0]), len(neutrophil[0]) )

# Loop over all output files and store times and counts of cell types
#num_cd8 = np.zeros(n)
#num_neut = np.zeros(n)

cell_type = mcds.data['discrete_cells']['cell_type']
print('cell_type min, max= ',cell_type.min(),cell_type.max())

scene = window.Scene()

# https://fury.gl/latest/reference/fury.actor.html?highlight=sphere#fury.actor.sphere
colors = (1,0,0)
#sphere_actor = actor.sphere(centers=xyz, colors=colors, radii=1.0)
sphere_actor = actor.sphere(centers=xyz, colors=colors, radii=cell_radii)
scene.add(sphere_actor)
showm = window.ShowManager(scene,
                           size=(800, 800), reset_camera=True,
                           order_transparent=False)
showm.initialize()
showm.start()

## window.record(showm.scene, size=(900, 768), out_path="viz_timer.png")