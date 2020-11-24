from fury import actor, ui, window
from pyMCDS_cells import pyMCDS_cells
from vtk.util import numpy_support


import numpy as np


def argviz(thr_1, thr_2, centers, axis):
    cond1 = thr_1 <= centers[:, axis]
    cond2 = centers[:, axis] <= thr_2
    return cond1 & cond2


def build_label(text, font_size=14, bold=False):
    label = ui.TextBlock2D()
    label.message = text
    label.font_size = font_size
    label.font_family = 'Arial'
    label.justification = 'left'
    label.bold = bold
    label.italic = False
    label.shadow = False
    label.actor.GetTextProperty().SetBackgroundColor(0, 0, 0)
    label.actor.GetTextProperty().SetBackgroundOpacity(0.0)
    label.color = (1, 1, 1)
    return label


def change_clipping_plane_x(slider):
    global ind_x, xyz
    values = slider._values
    r1, r2 = values
    ind_x = argviz(r1, r2, xyz, 0)
    update_opacities()


def change_clipping_plane_y(slider):
    global ind_y, xyz
    values = slider._values
    r1, r2 = values
    ind_y = argviz(r1, r2, xyz, 1)
    update_opacities()


def change_clipping_plane_z(slider):
    global ind_z, xyz
    values = slider._values
    r1, r2 = values
    ind_z = argviz(r1, r2, xyz, 2)
    update_opacities()


def update_opacities(verts_per_sph=4):
    global ind_x, ind_y, ind_z, spheres_actor
    mapper = spheres_actor.GetMapper()
    pnt_data = mapper.GetInput().GetPointData()
    pnt_arrays = pnt_data.GetNumberOfArrays()
    colors_array = None
    for i in range(pnt_arrays):
        if pnt_data.GetArray(i).GetName() == 'colors':
            colors_array = pnt_data.GetArray(i)
    spheres_colors = numpy_support.vtk_to_numpy(colors_array)
    opacities = []
    vis = [255] * verts_per_sph
    inv = [0] * verts_per_sph
    inds = ind_x | ind_y | ind_z
    for i, ind in enumerate(inds):
        if ind:
            opacities.extend(vis)
        else:
            opacities.extend(inv)
    opacities = np.array(opacities)
    opacities = np.ascontiguousarray(opacities)
    spheres_colors[:, 3] = opacities
    colors_array.Modified()


def win_callback(obj, event):
    global size
    global panel
    if size != obj.GetSize():
        size_old = size
        size = obj.GetSize()
        size_change = [size[0] - size_old[0], 0]
        panel.re_align(size_change)


if __name__ == '__main__':
    mcds = pyMCDS_cells('output00000001.xml', '.')  # 23123 cells
    print('time=', mcds.get_time())

    print(mcds.data['discrete_cells'].keys())

    ncells = len(mcds.data['discrete_cells']['ID'])

    global xyz
    xyz = np.zeros((ncells, 3))
    xyz[:, 0] = mcds.data['discrete_cells']['position_x']
    xyz[:, 1] = mcds.data['discrete_cells']['position_y']
    xyz[:, 2] = mcds.data['discrete_cells']['position_z']
    #xyz = xyz[:1000]

    np.random.seed(42)
    rgb = np.random.rand(xyz.shape[0], 3)
    colors = np.ones((xyz.shape[0], 4))
    colors[:, :-1] = rgb

    min_xyz = np.min(xyz, axis=0)
    max_xyz = np.max(xyz, axis=0)

    cell_radii = mcds.data['discrete_cells']['total_volume'] * .75 / np.pi
    cell_radii = np.cbrt(cell_radii)
    #cell_radii = cell_radii[:1000]

    cell_type = mcds.data['discrete_cells']['cell_type']
    print(cell_type)

    cell_type = mcds.data['discrete_cells']['cell_type']
    print('cell_type min, max= ', cell_type.min(), cell_type.max())

    scene = window.Scene()

    fake_sphere = \
        """
        if(opacity == 0)
            discard;
        float len = length(point);
        float radius = 1.;
        if(len > radius)
            discard;
        vec3 normalizedPoint = normalize(vec3(point.xy, sqrt(1. - len)));
        vec3 direction = normalize(vec3(1., 1., 1.));
        float df_1 = max(0, dot(direction, normalizedPoint));
        float sf_1 = pow(df_1, 24);
        fragOutput0 = vec4(max(df_1 * color, sf_1 * vec3(1)), 1);
        """

    global spheres_actor
    spheres_actor = actor.billboard(xyz, colors, scales=cell_radii,
                                    fs_impl=fake_sphere)
    scene.add(spheres_actor)

    show_m = window.ShowManager(scene, reset_camera=False,
                                order_transparent=True, max_peels=0)
    show_m.initialize()

    global panel
    panel = ui.Panel2D((256, 144), position=(40, 5), color=(1, 1, 1),
                       opacity=.1, align='right')

    thr_x1 = np.percentile(xyz[:, 0], 50)
    thr_x2 = max_xyz[0]
    global ind_x
    ind_x = argviz(thr_x1, thr_x2, xyz, 0)
    slider_clipping_plane_label_x = build_label('X Clipping Plane')
    slider_clipping_plane_thrs_x = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=5, length=115,
        initial_values=(thr_x1, thr_x2), min_value=min_xyz[0],
        max_value=max_xyz[0], font_size=12, text_template="{value:.0f}")

    thr_y1 = np.percentile(xyz[:, 1], 50)
    thr_y2 = max_xyz[1]
    global ind_y
    ind_y = argviz(thr_y1, thr_y2, xyz, 1)
    slider_clipping_plane_label_y = build_label('Y Clipping Plane')
    slider_clipping_plane_thrs_y = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=5, length=115,
        initial_values=(thr_y1, thr_y2), min_value=min_xyz[1],
        max_value=max_xyz[1], font_size=12, text_template="{value:.0f}")

    thr_z1 = np.percentile(xyz[:, 2], 50)
    thr_z2 = max_xyz[2]
    global ind_z
    ind_z = argviz(thr_z1, thr_z2, xyz, 2)
    slider_clipping_plane_label_z = build_label('Z Clipping Plane')
    slider_clipping_plane_thrs_z = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=5, length=115,
        initial_values=(thr_z1, thr_z2), min_value=min_xyz[2],
        max_value=max_xyz[2], font_size=12, text_template="{value:.0f}")

    update_opacities()

    slider_clipping_plane_thrs_x.on_change = change_clipping_plane_x
    slider_clipping_plane_thrs_y.on_change = change_clipping_plane_y
    slider_clipping_plane_thrs_z.on_change = change_clipping_plane_z

    panel.add_element(slider_clipping_plane_label_x, (.01, .85))
    panel.add_element(slider_clipping_plane_thrs_x, (.48, .85))
    panel.add_element(slider_clipping_plane_label_y, (.01, .55))
    panel.add_element(slider_clipping_plane_thrs_y, (.48, .55))
    panel.add_element(slider_clipping_plane_label_z, (.01, .25))
    panel.add_element(slider_clipping_plane_thrs_z, (.48, .25))

    scene.add(panel)

    global size
    size = scene.GetSize()

    show_m.add_window_callback(win_callback)

    show_m.start()
