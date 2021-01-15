from fury import actor, ui, window
from pyMCDS_cells import pyMCDS_cells


import numpy as np
import vtk


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
    global low_ranges, high_ranges
    values = slider._values
    r1, r2 = values
    low_ranges[0] = r1
    high_ranges[0] = r2


def change_clipping_plane_y(slider):
    global low_ranges, high_ranges
    values = slider._values
    r1, r2 = values
    low_ranges[1] = r1
    high_ranges[1] = r2


def change_clipping_plane_z(slider):
    global low_ranges, high_ranges
    values = slider._values
    r1, r2 = values
    low_ranges[2] = r1
    high_ranges[2] = r2


@vtk.calldata_type(vtk.VTK_OBJECT)
def vtk_shader_callback(caller, event, calldata=None):
    global low_ranges, high_ranges
    if calldata is not None:
        calldata.SetUniform3f('lowRanges', low_ranges)
        calldata.SetUniform3f('highRanges', high_ranges)


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

    centers = np.zeros((ncells, 3))
    centers[:, 0] = mcds.data['discrete_cells']['position_x']
    centers[:, 1] = mcds.data['discrete_cells']['position_y']
    centers[:, 2] = mcds.data['discrete_cells']['position_z']

    np.random.seed(42)
    colors = np.random.rand(centers.shape[0], 3)

    radius = mcds.data['discrete_cells']['total_volume'] * .75 / np.pi
    radius = np.cbrt(radius)

    cell_type = mcds.data['discrete_cells']['cell_type']
    print(cell_type)

    cell_type = mcds.data['discrete_cells']['cell_type']
    print('cell_type min, max= ', cell_type.min(), cell_type.max())

    scene = window.Scene()

    range_centers = \
        """        
        uniform vec3 lowRanges;
        uniform vec3 highRanges;
        
        bool isVisible(vec3 center)
        {
            bool xValidation = lowRanges.x <= center.x && 
                               center.x <= highRanges.x;
            bool yValidation = lowRanges.y <= center.y && 
                               center.y <= highRanges.y;
            bool zValidation = lowRanges.z <= center.z && 
                               center.z <= highRanges.z;
            return xValidation && yValidation && zValidation;
        }
        """

    fake_sphere = \
        """
        if(!isVisible(centerVertexMCVSOutput))
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

    spheres_actor = actor.billboard(centers, colors, scales=radius,
                                    fs_dec=range_centers, fs_impl=fake_sphere)

    scene.add(spheres_actor)

    min_centers = np.min(centers, axis=0)
    max_centers = np.max(centers, axis=0)

    global low_ranges, high_ranges
    low_ranges = np.percentile(centers, 50, axis=0)
    high_ranges = max_centers

    spheres_mapper = spheres_actor.GetMapper()
    spheres_mapper.AddObserver(vtk.vtkCommand.UpdateShaderEvent,
                               vtk_shader_callback)

    show_m = window.ShowManager(scene, reset_camera=False,
                                order_transparent=True)
    show_m.initialize()

    panel = ui.Panel2D((256, 144), position=(40, 5), color=(1, 1, 1),
                       opacity=.1, align='right')

    slider_clipping_plane_label_x = build_label('X Clipping Plane')
    slider_clipping_plane_thrs_x = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=5, length=115,
        initial_values=(low_ranges[0], high_ranges[0]),
        min_value=min_centers[0], max_value=max_centers[0], font_size=12,
        text_template="{value:.0f}")

    slider_clipping_plane_label_y = build_label('Y Clipping Plane')
    slider_clipping_plane_thrs_y = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=5, length=115,
        initial_values=(low_ranges[1], high_ranges[1]),
        min_value=min_centers[1], max_value=max_centers[1], font_size=12,
        text_template="{value:.0f}")

    slider_clipping_plane_label_z = build_label('Z Clipping Plane')
    slider_clipping_plane_thrs_z = ui.LineDoubleSlider2D(
        line_width=3, outer_radius=5, length=115,
        initial_values=(low_ranges[2], high_ranges[2]),
        min_value=min_centers[2], max_value=max_centers[2], font_size=12,
        text_template="{value:.0f}")

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
