import numpy as np
from fury import window, actor, ui
import itertools
import math

cell_radius = 1.0
cell_radius = 8.412710547954228
xc=yc=zc= -1.0
x_spacing= cell_radius*2
y_spacing= cell_radius*np.sqrt(3)
z_spacing= (cell_radius*2.0/3.0)*np.sqrt(6)
print("z_spacing=",z_spacing)

box_radius = 500.0
box_radius = 250.0
box_radius = 400.0
box_radius = 200.0
sphere_radius2 = box_radius * box_radius
eq_tri_yctr = math.tan(math.radians(30)) * cell_radius

xyz = np.empty((0,3))
colors = np.empty((0,4))
	
# spheroid axes
a = 15
a2 = a*a
c = 9
c = 15
c2 = c*c

# embolism centroid
x0_e = 50
x0_e = 200
y0_e = 50

x0_e = 0
y0_e = 0
z0_e = 0

# for z in np.arange(0.0, 2*cell_radius, z_spacing):
for z in np.arange(-box_radius, box_radius, z_spacing):
	zc += 1
	z_xoffset = (zc % 2) * cell_radius
	z_yoffset = (zc % 2) * eq_tri_yctr   # 0.5773502691896256
	zsq = z * z
	term3 = (z - z0_e) * (z - z0_e)
	# print("z_xoffset=",z_xoffset)
	# print("z_yoffset=",z_yoffset)
	for y in np.arange(-box_radius, box_radius, y_spacing):
		yc += 1
		y2 = y + z_yoffset 
		ysq = y2 * y2
		term2 = (y2 - y0_e) * (y2 - y0_e)
		# print('--------')
		for x in np.arange(-box_radius, box_radius, x_spacing):
			x2 = x + (yc%2) * cell_radius + z_xoffset
			xsq = x2 * x2
			term1 = (x2 - x0_e) * (x2 - x0_e)
			# print(x2,y2,z)
			if ( (z<0.0) and (xsq + ysq + zsq) < sphere_radius2):  # assume centered about origin
				xyz = np.append(xyz, np.array([[x2,y2,z]]), axis=0)
				# val = (xsq + ysq)/a2 + zsq/c2
				val = (term1 + term2)/a2 + term3/c2
				# print(val)
				if val < 15.0:
					colors = np.append(colors, np.array([[1,0,0, 1]]), axis=0)
				else:
					# colors = np.append(colors, np.array([[0,1,1, 1]]), axis=0)
					colors = np.append(colors, np.array([[0,1,1, 0.1]]), axis=0)
#	if (zc > 0):
#		break

ncells = len(xyz)
#colors = np.ones((ncells,4))  # white [0-2]; opaque [3]
#colors[:,0] = 0  # make them cyan

scene = window.Scene()
sphere_actor = actor.sphere(centers=xyz,
                            colors=colors,
                            radii=cell_radius)
scene.add(sphere_actor)
showm = window.ShowManager(scene,
                           size=(512, 512), reset_camera=True,
                           order_transparent=True)
showm.initialize()
showm.start()
# window.record(showm.scene, size=(900, 768), out_path="viz_timer.png")
