#
# last update : 2024.03.14
# what this code to:
# using gmsh,
# 1. draw rectangular
# 2. in the rectangular area, add circle and center point at (x,y) given
# 3. add vertical & horizontal reference line for result collecting nodes
#

import gmsh, sys
from math import sin, cos, pi

def vertice_box(B, H):
    # (0,0) is G.C of box
    return [(B/2, H/2), (B/2, -H/2), (-B/2, -H/2), (-B/2, H/2)]

def gmsh_mesh_option():
    gmsh.option.setNumber("Mesh.RecombineAll", 0)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 5)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 8)

def add_point(model, xypnt):
    return [model.occ.addPoint(x, y, 0, 0) for x, y in xypnt]

def add_circle(model, xypnt, dia):
    circle = [model.occ.addCircle(x, y, 0, dia/2) for x, y in xypnt]
    return [model.occ.addCurveLoop(circle)]

def add_pointInCurve(model, point, curve):
    # https://gmsh.info/doc/cookbook/geometry/embed-point.html
    return model.occ.fragment([(0, point)], [(1, curve)], removeObject=True, removeTool=True)[0]

def add_curveloop(model, point):
    return [model.occ.addCurveLoop([model.occ.addLine(point[i-1], point[i]) for i in range(len(point))])]

def add_line_x(model, H, xlist):
    # only for rectangular shape
    output = []
    eps = 0.0
    for x in xlist:
        xypnt = [(x, H/2-eps), (x, -H/2+eps)]
        pnt = add_point(model, xypnt)
        lineAB = model.occ.addLine(pnt[0], pnt[1])
        output.append(lineAB)
    return output

def add_line_y(model, B, ylist):
    # only for rectangular shape
    output = []
    eps = 0.0
    for y in ylist:
        xypnt = [(-B/2+eps, y), (B/2-eps, y)]
        pnt = add_point(model, xypnt)
        lineAB = model.occ.addLine(pnt[0], pnt[1])
        output.append(lineAB)
    return output

def add_pilecenter_point(model, point):
    output = []
    for pnt in point:
        center_pnt = add_point(model, [pnt])
        output += center_pnt
    return output

def point_on_circle(num, point, dia):
    angle_rot = pi / num * 2
    angle = list(map(lambda x: angle_rot*x, range(num)))
    output = []
    for x, y in point:
        circle = list(map(lambda i: (x+dia/2*cos(i), y+dia/2*sin(i)), angle))
        output += circle
    return output

def apply_pilecircle_point(model, inner, dia):
    point, surface = [], []
    for p in inner:
        center_p = add_point(model, [p])
        # outer circle 16 points
        peri1 = point_on_circle(16, [p], dia)
        peri1_p = add_point(model, peri1)
        # add loop, add surface
        loop = add_curveloop(model, peri1_p)
        s = [model.occ.addPlaneSurface(loop)]
        # inner circle 8 points
        peri2 = point_on_circle(8, [p], dia)
        peri2_p = add_point(model, peri2)
        # store
        temp = []; temp += center_p, peri1_p, peri2_p
        point.append(temp)
        surface += s
    return point, surface

def apply_circle(model, inner, dia):
    point, surface = [], []
    for p in inner:
        center_p = add_point(model, [p])
        loop = add_circle(model, [p], dia)
        s = [model.occ.addPlaneSurface(loop)]
        point += center_p
        surface += s
    return point, surface

def collect_surface(fragout):
    output = []
    for i in fragout[0]:
        if i[0] == 2:
            output.append(i)
    return output

def get_entity_in_boundingbox(model, surface):
    # search bounding box x,y,z of surface
    gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
    bounding_box = []
    for i in surface:
        x = model.getBoundingBox(2, i[1])
        bounding_box.append(x)
    #print(bounding_box)

    # get entity in the bounding box
    eps = 1e-3
    entity_in_box = []
    for i, _ in enumerate(surface):
        xmin, ymin, _, xmax, ymax, _ = \
            bounding_box[i][0]-eps, bounding_box[i][1]-eps, 0,\
            bounding_box[i][3]+eps, bounding_box[i][4]+eps, 0
        x = model.getEntitiesInBoundingBox(xmin, ymin, 0, xmax, ymax, 0, dim=0)
        entity_in_box.append(x)
    #print(entity_in_box)

def get_boundary_entity(model, surface):
    boundary_point = []
    boundary_line = []
    for i in surface:
        x = model.getBoundary([(2, i[1])], oriented=False, recursive=True)
        y = model.getBoundary([(2, i[1])], oriented=False, recursive=False)
        boundary_point.append(x)
        boundary_line.append(y)
    #print(boundary_point)
    #print(boundary_line)

def get_xyz_of_point(model, point):
    xyz = []
    for i in range(len(point)):
        temp = []
        for j in point[i]:
            x = list(model.getValue(0, j[1], []))
            temp.append(x)
        xyz.append(temp)
    #print(xyz)

def create_mesh_2d(outer, inner, shape, dia, lc):
    # create a new model
    gmsh.initialize()
    model = gmsh.model
    model.add("mesh")

    # create CAD geometry
    boundary = add_point(model, outer)
    loop     = add_curveloop(model, boundary)
    stag1    = model.occ.addPlaneSurface(loop, 1)
    cp, cs   = apply_circle(model, inner, dia)
    stag2    = 100
    model.occ.cut([(2,stag1)],[(2,i) for i in cs], tag=stag2, removeObject=True, removeTool=False)

    # draw meshing reference line to embed
    xlist = [0, -0.6/2, 0.6/2, -1.3/2, 1.3/2]     # user input
    ylist = [0, -0.6/2, 0.6/2, -1.3/2, 1.3/2]     # user input
    xline = add_line_x(model, shape[1], xlist)
    yline = add_line_y(model, shape[0], ylist)
    # occ.fragment
    fragout = model.occ.fragment([(2, stag2)], [(1, i) for i in xline], removeObject=True, removeTool=True)
    surface = collect_surface(fragout)
    fragout = model.occ.fragment(surface, [(1, i) for i in yline], removeObject=True, removeTool=True)
    surface = collect_surface(fragout)
    model.occ.removeAllDuplicates()

    # before finish CAD geom
    model.occ.synchronize()

    # embed cp in cs
    for i, j in enumerate(cp):
        model.mesh.embed(0, [j], 2, cs[i])

    # define physical group
    model.addPhysicalGroup(2, [i[1] for i in surface], name="pilecap")
    model.addPhysicalGroup(2, cs, name="pilecap")

    gmsh_mesh_option()
    model.mesh.setSize(model.getEntities(0), lc)
    # for quad
    #for i in surface:
    #    model.mesh.setRecombine(2, i[1])
    #    model.mesh.setSmoothing(2, i[1], 100)
    model.mesh.generate(2)

    # save mesh
    gmsh.write("./fem/mesh2.inp")

    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()

    gmsh.finalize()

if __name__ == "__main__":
    rect_size = (6, 5.6)
    thk = 2.0
    dia = 0.6
    outer = vertice_box(rect_size[0], rect_size[1])
    inner = [(-1.5, 2.05), (0, 2.05), (1.5, 2.05),\
             (-2.25, 0.75), (-0.75, 0.75), (0.75, 0.75), (2.25, 0.75),\
             (-2.25, -0.75), (-0.75, -0.75), (0.75, -0.75), (2.25, -0.75),\
             (-1.5, -2.05), (0, -2.05), (1.5, -2.05)]
    mesh_size = max(rect_size) / 12
    create_mesh_2d(outer, inner, rect_size, dia, mesh_size)