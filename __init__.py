# SPDX-FileCopyrightText: 2025-2026 The French Monkey
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Mesh",
    "author": "The French Monkey",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Mesh",
    "description": "Generate parametric Meshes",
    "category": "Add Mesh",
    "license": "GPL-3.0-or-later",
}

import bpy
import bmesh
from math import sin, cos, pi, copysign, sqrt, radians

# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

def clamp(v, a, b):
    return max(a, min(b, v))

def safe_seg(seg, maxv=4096):
    return max(3, min(int(seg), maxv))

def face_from_points(bm, pts):
    verts = [bm.verts.new((x, y, 0.0)) for (x, y) in pts]
    bm.verts.ensure_lookup_table()
    try:
        bm.faces.new(verts)
    except:
        pass

def add_face_strip(bm, outer, inner):
    n = min(len(outer), len(inner))
    for i in range(n):
        bm.faces.new((outer[i], outer[(i+1)%n], inner[(i+1)%n], inner[i]))

def superellipse_xy(a, b, exp, segments, rot=0.0):
    pts = []
    for i in range(segments):
        t = (i / segments) * 2.0 * pi + rot
        x = copysign(abs(cos(t)) ** (2.0 / exp), cos(t)) * a
        y = copysign(abs(sin(t)) ** (2.0 / exp), sin(t)) * b
        pts.append((x, y))
    return pts

def circle_pts(radius, seg, phase=0.0):
    return [(cos(2*pi*i/seg + phase)*radius, sin(2*pi*i/seg + phase)*radius) for i in range(seg)]

def build_loop(bm, pts):
    return [bm.verts.new((x, y, 0.0)) for (x, y) in pts]

def extrude_region_z(bm, faces, height):
    res = bmesh.ops.extrude_face_region(bm, geom=faces)
    geom = res["geom"]
    verts = [e for e in geom if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=(0.0, 0.0, height))
    return verts

def twist_taper_along_z(verts, total_h, twist_deg=0.0, taper=0.0):
    if abs(total_h) < 1e-9:
        return
    tw = radians(twist_deg)
    for v in verts:
        f = clamp(v.co.z / total_h, 0.0, 1.0)
        ang = tw * f
        sc = 1.0 - taper * f
        x, y = v.co.x * sc, v.co.y * sc
        ca, sa = cos(ang), sin(ang)
        v.co.x = ca * x - sa * y
        v.co.y = sa * x + ca * y

# ----------------------------------------------------------
# 2D Shapes
# ----------------------------------------------------------

def make_polygon(bm, sides, radius):
    bm.clear()
    sides = safe_seg(sides)
    pts = [(cos(2*pi*i/sides)*radius, sin(2*pi*i/sides)*radius) for i in range(sides)]
    face_from_points(bm, pts)

def make_star(bm, points, radius, inner_ratio):
    bm.clear()
    points = max(3, points)
    r2 = clamp(inner_ratio, 0.01, 0.99) * radius
    pts = []
    for i in range(points * 2):
        a = (i / (points * 2)) * 2 * pi
        r = radius if i % 2 == 0 else r2
        pts.append((cos(a) * r, sin(a) * r))
    face_from_points(bm, pts)

def make_superellipse(bm, sides, radius, exponent):
    bm.clear()
    seg = safe_seg(sides)
    pts = superellipse_xy(radius, radius, exponent, seg)
    face_from_points(bm, pts)

def make_flower(bm, sides, radius, petals, depth):
    bm.clear()
    seg = safe_seg(sides * 4)
    d = clamp(depth, 0.0, 1.0)
    pts = []
    for i in range(seg):
        a = (i / seg) * 2 * pi
        r = radius * (1.0 + d * sin(petals * a))
        pts.append((cos(a) * r, sin(a) * r))
    face_from_points(bm, pts)

def make_plus(bm, size, thickness):
    bm.clear()
    t = clamp(thickness, 0.02, 0.98) * size
    s = size
    pts = [
        (-t,  s), ( t,  s), ( t,  t),
        ( s,  t), ( s, -t), ( t, -t),
        ( t, -s), (-t, -s), (-t, -t),
        (-s, -t), (-s,  t), (-t,  t),
    ]
    face_from_points(bm, pts)

def make_cross(bm, size, thickness, gap):
    bm.clear()
    s = size
    arm = clamp(thickness, 0.02, 0.98) * s
    g = clamp(gap, 0.0, 0.95) * arm
    pts = [
        (-arm,  s), ( arm,  s), ( arm,  arm),
        ( s,    arm), ( s,   -arm), ( arm, -arm),
        ( arm, -s), (-arm, -s), (-arm, -arm),
        (-s,   -arm), (-s,    arm), (-arm,  arm),
    ]
    if g > 0:
        def sh(p):
            x,y = p
            if abs(x) == arm and abs(y) == arm:
                x = copysign(abs(x)+g, x)
                y = copysign(abs(y)+g, y)
            return (x,y)
        pts = [sh(p) for p in pts]
    face_from_points(bm, pts)

def make_crescent(bm, segments, radius, inner_ratio, offset):
    bm.clear()

    seg = safe_seg(segments * 4)  
    R = max(0.01, float(radius))  
    r = clamp(float(inner_ratio), 0.01, 0.99) * R 
    d = clamp(float(offset), 0.0, 0.99) * (R - r) 

    outer_pts = [(cos(2 * pi * i / seg) * R, sin(2 * pi * i / seg) * R) for i in range(seg + 1)]
    inner_pts = [(cos(2 * pi * i / seg) * r + d, sin(2 * pi * i / seg) * r) for i in range(seg + 1)]

    outer_verts = [bm.verts.new((x, y, 0.0)) for x, y in outer_pts]
    inner_verts = [bm.verts.new((x, y, 0.0)) for x, y in inner_pts]
    bm.verts.ensure_lookup_table()

    for i in range(seg):
        bm.faces.new((outer_verts[i], outer_verts[i + 1], inner_verts[i]))
        bm.faces.new((outer_verts[i + 1], inner_verts[i + 1], inner_verts[i]))
        bm.faces.new((inner_verts[i], inner_verts[i + 1], outer_verts[i]))
        bm.faces.new((inner_verts[i + 1], outer_verts[i + 1], outer_verts[i]))

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()

def make_arc_segment(bm, segments, radius, thickness, a0_deg, a1_deg):
    bm.clear()
    a0 = radians(a0_deg % 360.0)
    a1 = radians(a1_deg % 360.0)
    span = (a1 - a0) % (2*pi)
    if span < 1e-6:
        span = 2*pi
    seg = safe_seg(int(segments * max(0.1, span/(2*pi))))
    R = radius
    t = clamp(thickness, 0.01, 0.99)
    r = max(1e-6, R * (1.0 - t))
    outer = [(cos(a0 + span*i/seg)*R, sin(a0 + span*i/seg)*R) for i in range(seg+1)]
    inner = [(cos(a0 + span*i/seg)*r, sin(a0 + span*i/seg)*r) for i in range(seg+1)]
    inner.reverse()
    face_from_points(bm, outer + inner)

def make_gear(bm, segments, radius, teeth, tooth_depth, roundness):
    bm.clear()
    teeth = max(2, int(teeth))
    seg = max(max(64, segments), teeth * 24)
    R_pitch = float(radius)
    d = clamp(float(tooth_depth), 0.0, 0.95)
    add = d * 0.5 * R_pitch
    ded = d * 0.5 * R_pitch
    R_tip = R_pitch + add
    R_root = max(1e-6, R_pitch - ded)
    theta_p = 2.0 * pi / teeth
    f_top = 0.33
    soft = clamp(roundness, 0.0, 1.0)
    exp = 1.0 + (1.0 - soft) * 3.0

    def tooth_envelope(angle):
        u = ((angle + 0.5 * theta_p) % theta_p) - 0.5 * theta_p
        u = abs(u) / (0.5 * theta_p)
        if u <= f_top:
            s = 1.0
        else:
            t = (u - f_top) / max(1e-6, (1.0 - f_top))
            s = (0.5 * (1.0 + cos(pi * t))) ** exp
        return s

    pts = []
    for i in range(seg):
        ang = 2.0 * pi * i / seg
        s = tooth_envelope(ang)
        r = R_root + s * (R_tip - R_root)
        pts.append((cos(ang) * r, sin(ang) * r))

    face_from_points(bm, pts)

def make_vent_disk(bm, segments, radius, hole_count, hole_width, hole_length):
    bm.clear()
    seg = safe_seg(segments * 4)
    R = radius
    outer_loop = [bm.verts.new((cos(2*pi*i/seg)*R, sin(2*pi*i/seg)*R, 0)) for i in range(seg)]
    bm.verts.ensure_lookup_table()
    bm.faces.new(outer_loop)
    n = max(1, int(hole_count))
    w = clamp(hole_width, 0.0, 1.0) * R * 0.5
    L = clamp(hole_length, 0.0, 1.0) * R * 0.8
    for i in range(n):
        a = 2*pi*i/n
        cx = cos(a) * (R*0.55)
        cy = sin(a) * (R*0.55)
        ux, uy = cos(a), sin(a)
        vx, vy = -uy, ux
        p1 = (cx + ux*L + vx*w, cy + uy*L + vy*w, 0)
        p2 = (cx + ux*L - vx*w, cy + uy*L - vy*w, 0)
        p3 = (cx - ux*L - vx*w, cy - uy*L - vy*w, 0)
        p4 = (cx - ux*L + vx*w, cy - uy*L + vy*w, 0)
        v1 = bm.verts.new(p1); v2 = bm.verts.new(p2); v3 = bm.verts.new(p3); v4 = bm.verts.new(p4)
        bm.faces.new((v1, v2, v3, v4))

# ----------------------------------------------------------
# 3D Shapes
# ----------------------------------------------------------

def make_column(bm, segments, radius, height, flutes, flute_depth, taper, twist_deg, entasis, base_frac, cap_frac, loop_cuts):
    bm.clear()

    seg = safe_seg(segments)
    fl = max(0, int(flutes))
    fd = clamp(flute_depth, 0.0, 0.9)
    base_frac = clamp(base_frac, 0.0, 0.5)
    cap_frac = clamp(cap_frac, 0.0, 0.5)
    entasis = clamp(entasis, -0.5, 0.5)
    height = max(0.01, float(height))
    loop_cuts = max(0, int(loop_cuts))

    base_height = height * base_frac
    cap_height = height * cap_frac
    shaft_height = height - base_height - cap_height

    profile = [
        (0.0, radius * (1.0 + base_frac * 0.3)),          
        (base_height, radius),                               
        (base_height + shaft_height * 0.5, radius * (1.0 + entasis)), 
        (base_height + shaft_height, radius * (1.0 - abs(taper))),  
        (height, radius * (1.0 + cap_frac * 0.3)),     
    ]

    smooth_profile = []
    seam_indices = [0, 1, 2, 3]  
    for i in range(len(profile) - 1):
        z0, r0 = profile[i]
        z1, r1 = profile[i + 1]
        smooth_profile.append((z0, r0))
        if i in seam_indices and (abs(z1 - z0) > 1e-6 or abs(r1 - r0) > 1e-6):
            delta_z = (z1 - z0) * 0.1  
            delta_r = (r1 - r0) * 0.1
            for j in range(1, loop_cuts + 1):
                t = 1.0 - 0.5 * (1 - cos(pi * j / (loop_cuts + 1))) 
                z = z1 - delta_z * (1.0 - t)
                r = r1 - delta_r * (1.0 - t)
                smooth_profile.append((z, r))
            for j in range(1, loop_cuts + 1):
                t = 0.5 * (1 - cos(pi * j / (loop_cuts + 1))) 
                z = z0 + delta_z * t
                r = r0 + delta_r * t
                smooth_profile.append((z, r))

    smooth_profile.append(profile[-1])
    smooth_profile.sort(key=lambda x: x[0]) 

    rings = []
    for z, r in smooth_profile:
        ring = []
        for i in range(seg):
            th = 2 * pi * i / seg
            r_mod = r
            if fl > 0:
                r_mod *= (1.0 - fd * max(0.0, (abs(cos(fl * th)) ** 2.0)))
            ring.append(bm.verts.new((cos(th) * r_mod, sin(th) * r_mod, z)))
        rings.append(ring)

    bm.verts.ensure_lookup_table()

    for j in range(len(rings) - 1):
        a = rings[j]
        b = rings[j + 1]
        for i in range(seg):
            v0 = a[i]
            v1 = a[(i + 1) % seg]
            v2 = b[(i + 1) % seg]
            v3 = b[i]
            bm.faces.new((v0, v1, v2, v3))

    bottom_pole = bm.verts.new((0, 0, 0.0))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((bottom_pole, rings[0][j], rings[0][i]))

    top_pole = bm.verts.new((0, 0, height))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((top_pole, rings[-1][i], rings[-1][j]))

    all_verts = [v for ring in rings for v in ring] + [bottom_pole, top_pole]
    twist_taper_along_z(all_verts, height, twist_deg=twist_deg, taper=taper)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()

def make_arch3d(bm, segments, radius, inner_ratio, thickness_radial, a0_deg, a1_deg, depth_z):
    bm.clear()

    seg = safe_seg(segments)
    a0 = radians(a0_deg)
    a1 = radians(a1_deg)

    R_out = radius
    R_in = clamp(inner_ratio, 0.01, 0.99) * R_out
    t = clamp(thickness_radial, 0.0, 1.0)
    R_in = max(1e-6, min(R_out - 1e-6, R_in + t * (R_out - R_in)))

    ang = [a0 + (a1 - a0) * i / seg for i in range(seg + 1)]

    outer_bottom = [bm.verts.new((cos(a) * R_out, sin(a) * R_out, 0)) for a in ang]
    inner_bottom = [bm.verts.new((cos(a) * R_in,  sin(a) * R_in,  0)) for a in ang]
    outer_top = [bm.verts.new((cos(a) * R_out, sin(a) * R_out, depth_z)) for a in ang]
    inner_top = [bm.verts.new((cos(a) * R_in,  sin(a) * R_in,  depth_z)) for a in ang]

    bm.verts.ensure_lookup_table()

    for i in range(seg):
        j = i + 1
        bm.faces.new((outer_bottom[i], outer_bottom[j], outer_top[j], outer_top[i])) 
        bm.faces.new((inner_top[i], inner_top[j], inner_bottom[j], inner_bottom[i]))  
        bm.faces.new((outer_bottom[i], outer_bottom[j], inner_bottom[j], inner_bottom[i])) 
        bm.faces.new((outer_top[i], inner_top[i], inner_top[j], outer_top[j])) 

    bm.faces.new((outer_bottom[0], inner_bottom[0], inner_top[0], outer_top[0]))    
    bm.faces.new((outer_bottom[-1], outer_top[-1], inner_top[-1], inner_bottom[-1]))  

    bm.normal_update()

def make_dome(bm, segments, radius, vertical_segments, curvature):
    bm.clear()
    seg = safe_seg(segments)
    vseg = max(4, vertical_segments)
    curv = clamp(curvature, 0.1, 2.0)
    rings = []
    for j in range(vseg+1):
        t = j / vseg
        theta = (t ** curv) * (pi/2)
        r = radius * sin(theta)
        z = radius * cos(theta)
        ring = [bm.verts.new((cos(2*pi*i/seg)*r, sin(2*pi*i/seg)*r, z)) for i in range(seg)]
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for j in range(vseg):
        a = rings[j]
        b = rings[j+1]
        for i in range(seg):
            v0 = a[i]; v1 = a[(i+1)%seg]; v2 = b[(i+1)%seg]; v3 = b[i]
            bm.faces.new((v0, v1, v2, v3))

def make_gear3d(bm, segments, radius, teeth, tooth_depth, roundness, hub_ratio, thickness_z, taper, twist_deg):
    bm.clear()

    seg = safe_seg(max(segments, teeth * 8))  
    R = max(0.01, float(radius)) 
    k = max(2, int(teeth)) 
    d = clamp(float(tooth_depth), 0.0, 0.9)  
    exp = 1.0 + clamp(roundness, 0.0, 1.0) * 7.0  
    thickness_z = max(0.01, float(thickness_z))  
    hub_ratio = clamp(hub_ratio, 0.01, 0.95)  
    taper = clamp(float(taper), -0.95, 0.95)  
    twist_deg = float(twist_deg) 

    outer_pts = []
    min_rr = float('inf')
    for i in range(seg):
        th = 2.0 * pi * i / seg
        c = cos(k * th)
        s = copysign(abs(c) ** (2.0 / exp), c)
        rr = R * (1.0 + d * s)
        min_rr = min(min_rr, rr)
        outer_pts.append((cos(th) * rr, sin(th) * rr))

    R_hub = min(hub_ratio * R, min_rr * 0.85) 
    inner_pts = [(cos(2 * pi * i / seg) * R_hub, sin(2 * pi * i / seg) * R_hub) for i in range(seg)]

    outer_bottom = [bm.verts.new((x, y, 0.0)) for x, y in outer_pts]
    inner_bottom = [bm.verts.new((x, y, 0.0)) for x, y in inner_pts]
    outer_top = [bm.verts.new((x, y, thickness_z)) for x, y in outer_pts]
    inner_top = [bm.verts.new((x, y, thickness_z)) for x, y in inner_pts]
    bm.verts.ensure_lookup_table()

    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((outer_bottom[i], outer_bottom[j], outer_top[j], outer_top[i]))

    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((inner_bottom[j], inner_bottom[i], inner_top[i], inner_top[j]))

    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((outer_top[i], inner_top[i], inner_top[j])) 
        bm.faces.new((outer_top[i], inner_top[j], outer_top[j])) 

    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((outer_bottom[i], inner_bottom[j], inner_bottom[i])) 
        bm.faces.new((outer_bottom[i], outer_bottom[j], inner_bottom[j])) 

    top_verts = [v for v in bm.verts if abs(v.co.z - thickness_z) < 1e-6]
    twist_taper_along_z(top_verts, thickness_z, twist_deg=twist_deg, taper=taper)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()

def make_pipe(bm, segments, outer_radius, inner_ratio, height_z):
    bm.clear()
    seg = safe_seg(segments)
    R_out = float(outer_radius)
    R_in  = max(1e-6, float(inner_ratio) * R_out)
    H     = float(height_z)
    ang = [2.0 * pi * i / seg for i in range(seg)]
    outer_bottom = [bm.verts.new((cos(a)*R_out, sin(a)*R_out, 0.0)) for a in ang]
    inner_bottom = [bm.verts.new((cos(a)*R_in,  sin(a)*R_in,  0.0)) for a in ang]
    outer_top = [bm.verts.new((v.co.x, v.co.y, H)) for v in outer_bottom]
    inner_top = [bm.verts.new((v.co.x, v.co.y, H)) for v in inner_bottom]
    bm.verts.ensure_lookup_table()
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((outer_bottom[i], outer_bottom[j], outer_top[j], outer_top[i]))
        bm.faces.new((inner_top[i], inner_top[j], inner_bottom[j], inner_bottom[i]))
        bm.faces.new((outer_bottom[i], outer_bottom[j], inner_bottom[j], inner_bottom[i]))
        bm.faces.new((outer_top[i], inner_top[i], inner_top[j], outer_top[j]))
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

def make_bolt(bm, segments, shaft_radius, shaft_length, head_radius, head_height):
    bm.clear()
    seg = safe_seg(segments)
    rs = max(0.01, shaft_radius)
    rl = max(0.01, head_radius)
    Ls = max(0.01, shaft_length)
    Lh = max(0.01, head_height)
    shaft_loop = build_loop(bm, circle_pts(rs, seg))
    bm.verts.ensure_lookup_table()
    face_shaft = bm.faces.new(shaft_loop)
    top_shaft = extrude_region_z(bm, [face_shaft], Ls)
    hex_pts = [(cos(2*pi*i/6)*rl, sin(2*pi*i/6)*rl) for i in range(6)]
    head_base = [bm.verts.new((x, y, Ls)) for (x, y) in hex_pts]
    bm.verts.ensure_lookup_table()
    face_head = bm.faces.new(head_base)
    extrude_region_z(bm, [face_head], Lh)
    
def make_capsule(bm, segments, radius, height, cap_segments, taper):
    bm.clear()
    seg = safe_seg(segments)
    cs = max(4, int(cap_segments))
    R = max(0.01, float(radius))
    H = max(0.01, float(height))
    taper = clamp(float(taper), -0.95, 0.95)
    rings = []
    
    for i in range(cs): 
        theta = pi / 2 * i / cs  
        r = R * sin(theta)
        z = -H / 2 - R * cos(theta)
        ring = [(cos(2 * pi * j / seg) * r, sin(2 * pi * j / seg) * r, z) for j in range(seg)]
        rings.append([bm.verts.new(p) for p in ring])
    
    ring = [(cos(2 * pi * j / seg) * R, sin(2 * pi * j / seg) * R, -H / 2) for j in range(seg)]
    rings.append([bm.verts.new(p) for p in ring])
    ring = [(cos(2 * pi * j / seg) * R, sin(2 * pi * j / seg) * R, H / 2) for j in range(seg)]
    rings.append([bm.verts.new(p) for p in ring])
    
    for i in range(cs): 
        theta = pi / 2 * (cs - i) / cs 
        r = R * sin(theta)
        z = H / 2 + R * cos(theta)  
        ring = [(cos(2 * pi * j / seg) * r, sin(2 * pi * j / seg) * r, z) for j in range(seg)]
        rings.append([bm.verts.new(p) for p in ring])
    
    bm.verts.ensure_lookup_table()
    
    for i in range(len(rings) - 1):
        for j in range(seg):
            k = (j + 1) % seg
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    
    bottom_pole = bm.verts.new((0, 0, -H / 2 - R))
    for j in range(seg):
        k = (j + 1) % seg
        bm.faces.new((bottom_pole, rings[0][k], rings[0][j]))
    
    top_pole = bm.verts.new((0, 0, H / 2 + R))
    for j in range(seg):
        k = (j + 1) % seg
        bm.faces.new((top_pole, rings[-1][j], rings[-1][k]))
    
    top_verts = [v for v in bm.verts if v.co.z >= H / 2 - 1e-6]
    twist_taper_along_z(top_verts, H + 2 * R, twist_deg=0.0, taper=taper)
    
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    
def make_geometric_sphere(bm, segments, rings, radius, exp_lat, exp_long):
    bm.clear()
    seg = safe_seg(segments)
    rings = max(3, int(rings))
    exp_lat = max(0.1, float(exp_lat))
    exp_long = max(0.1, float(exp_long))
    R = float(radius)

    def sgn(v): 
        return copysign(1.0, v)

    verts = []
    for j in range(rings + 1):
        v = -pi/2 + pi * j / rings
        z = sgn(sin(v)) * (abs(sin(v)) ** (2.0 / exp_lat)) * R
        r_xy = abs(cos(v)) ** (2.0 / exp_lat)
        ring = []
        for i in range(seg):
            u = 2*pi * i / seg
            x = sgn(cos(u)) * (abs(cos(u)) ** (2.0 / exp_long)) * R * r_xy
            y = sgn(sin(u)) * (abs(sin(u)) ** (2.0 / exp_long)) * R * r_xy
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)

    bm.verts.ensure_lookup_table()
    for j in range(rings):
        for i in range(seg):
            v0 = verts[j][i]
            v1 = verts[j][(i+1)%seg]
            v2 = verts[j+1][(i+1)%seg]
            v3 = verts[j+1][i]
            bm.faces.new((v0, v1, v2, v3))

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    
def make_buckyball(bm, radius=1.0, detail=1):
    import bmesh
    from math import sqrt, atan2
    from mathutils import Vector

    bm.clear()
    detail = max(1, int(detail))
    r = float(radius)

    phi = (1.0 + sqrt(5.0)) / 2.0
    ico_verts = [
        Vector((-1,  phi, 0)), Vector(( 1,  phi, 0)),
        Vector((-1, -phi, 0)), Vector(( 1, -phi, 0)),
        Vector((0, -1,  phi)), Vector((0,  1,  phi)),
        Vector((0, -1, -phi)), Vector((0,  1, -phi)),
        Vector(( phi, 0, -1)), Vector(( phi, 0,  1)),
        Vector((-phi, 0, -1)), Vector((-phi, 0,  1)),
    ]

    ico_verts = [v.normalized() for v in ico_verts]

    ico_faces = [
        (0,11,5),  (0,5,1),   (0,1,7),   (0,7,10),  (0,10,11),
        (1,5,9),   (5,11,4),  (11,10,2), (10,7,6),  (7,1,8),
        (3,9,4),   (3,4,2),   (3,2,6),   (3,6,8),   (3,8,9),
        (4,9,5),   (2,4,11),  (6,2,10),  (8,6,7),   (9,8,1),
    ]

    def key_round(v, tol=1e-8):
        return (round(v.x, 8), round(v.y, 8), round(v.z, 8))

    vert_index = {}   
    verts = []        
    faces_small = []  

    def add_vertex(v):
        k = key_round(v)
        idx = vert_index.get(k)
        if idx is None:
            idx = len(verts)
            vert_index[k] = idx
            verts.append(v)
        return idx

    def subdivide_triangle(v0, v1, v2, f):
        idx_grid = []
        for i in range(f+1):
            row = []
            for j in range(f+1 - i):
                k = f - i - j
                p = (v1 * i + v2 * j + v0 * k) / f
                p = p.normalized()
                row.append(add_vertex(p))
            idx_grid.append(row)

        for i in range(f):
            for j in range(f - i):
                a = idx_grid[i][j]
                b = idx_grid[i+1][j]
                c = idx_grid[i][j+1]
                faces_small.append([a, b, c])
                if j + 1 < f - i:
                    d = idx_grid[i+1][j+1]
                    faces_small.append([b, d, c])

    f = detail
    for a, b, c in ico_faces:
        subdivide_triangle(ico_verts[a], ico_verts[b], ico_verts[c], f)

    verts = [v.normalized() * r for v in verts]

    dual_verts = []
    tri_to_dual = []

    for tri in faces_small:
        p = (verts[tri[0]] + verts[tri[1]] + verts[tri[2]]) / 3.0
        p = p.normalized() * r
        tri_to_dual.append(len(dual_verts))
        dual_verts.append(p)

    from collections import defaultdict
    incident = defaultdict(list)

    def tangent_frame(n):
        h = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
        u = (h - n * n.dot(h)).normalized()
        v = n.cross(u)
        return u, v

    for ti, (a, b, c) in enumerate(faces_small):
        incident[a].append(ti)
        incident[b].append(ti)
        incident[c].append(ti)

    bm_verts = [bm.verts.new(co) for co in dual_verts]
    bm.verts.ensure_lookup_table()

    for vi, tris in incident.items():
        if len(tris) < 3:
            continue

        p0 = verts[vi]
        n = p0.normalized()
        u, v = tangent_frame(n)

        ang_order = []
        for ti in tris:
            dp = dual_verts[tri_to_dual[ti]] - p0
            x = dp.dot(u)
            y = dp.dot(v)
            ang = atan2(y, x)
            ang_order.append((ang, ti))

        ang_order.sort(key=lambda x: x[0])
        loop = [bm_verts[tri_to_dual[ti]] for (ang, ti) in ang_order]

        try:
            bm.faces.new(loop)
        except ValueError:
            pass

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()

# ----------------------------------------------------------
# Rebuild
# ----------------------------------------------------------

def rebuild_shape(obj):
    if not obj or obj.type != 'MESH':
        return

    col = obj.get("shape_collection", "2D")
    st  = obj.get("shape_type", "")
    seg = int(obj.get("segments", 64))
    sz  = float(obj.get("size", 1.0))

    ir  = float(obj.get("inner_ratio", 0.5))
    exp = float(obj.get("exponent", 2.5))
    petals = int(obj.get("petals", 5))
    petal_depth = float(obj.get("petal_depth", 0.2))
    thickness = float(obj.get("thickness", 0.2))
    roundness = float(obj.get("roundness", 0.2))
    angle_start = float(obj.get("angle_start", 0.0))
    angle_end   = float(obj.get("angle_end", 270.0))
    hole_count  = int(obj.get("hole_count", 8))
    hole_width  = float(obj.get("hole_width", 0.15))
    hole_length = float(obj.get("hole_length", 0.35))
    teeth       = int(obj.get("teeth", 12))
    tooth_depth = float(obj.get("tooth_depth", 0.25))

    height3d = float(obj.get("height3d", 1.0))
    depth_z  = float(obj.get("depth_z", 0.2))
    vertical_segments = int(obj.get("vertical_segments", 16))
    curvature = float(obj.get("curvature", 1.0))
    flutes = int(obj.get("flutes", 12))
    flute_depth = float(obj.get("flute_depth", 0.2))
    taper = float(obj.get("taper", 0.0))
    twist_deg = float(obj.get("twist_deg", 0.0))
    thickness_radial = float(obj.get("thickness_radial", 0.0))
    entasis = float(obj.get("entasis", 0.0))
    base_frac = float(obj.get("base_frac", 0.05))
    cap_frac  = float(obj.get("cap_frac", 0.05))
    hub_ratio = float(obj.get("hub_ratio", 0.3))
    shaft_radius = float(obj.get("shaft_radius", 0.25))
    shaft_length = float(obj.get("shaft_length", 1.0))
    head_radius  = float(obj.get("head_radius", 0.5))
    head_height  = float(obj.get("head_height", 0.25))

    mesh = obj.data
    bm = bmesh.new()

    if col == "2D":
        if st == "POLYGON":
            make_polygon(bm, seg, sz)
        elif st == "STAR":
            make_star(bm, seg, sz, ir)
        elif st == "SUPERELLIPSE":
            make_superellipse(bm, seg, sz, exp)
        elif st == "FLOWER":
            make_flower(bm, seg, sz, petals, petal_depth)
        elif st == "PLUS":
            make_plus(bm, sz, thickness)
        elif st == "CROSS":
            make_cross(bm, sz, thickness, float(obj.get("center_gap", 0.0)))
        elif st == "CRESCENT":
            make_crescent(bm, seg, sz, ir, float(obj.get("offset", 0.2)))
        elif st == "ARC_SEGMENT":
            make_arc_segment(bm, seg, sz, thickness, angle_start, angle_end)
        elif st == "GEAR":
            make_gear(bm, seg, sz, teeth, tooth_depth, roundness)
        elif st == "VENT_DISK":
            make_vent_disk(bm, seg, sz, hole_count, hole_width, hole_length)
    else:
        if st == "COLUMN":
            make_column(bm, seg, sz, height3d, flutes, flute_depth, taper, twist_deg, entasis, base_frac, cap_frac, int(obj.get("loop_cuts", 2)))
        elif st == "ARCH3D":
            make_arch3d(bm, seg, sz, ir, thickness_radial, angle_start, angle_end, depth_z)
        elif st == "DOME":
            make_dome(bm, seg, sz, vertical_segments, curvature)
        elif st == "GEAR3D":
            make_gear3d(bm, seg, sz, teeth, tooth_depth, roundness, hub_ratio, depth_z, taper, twist_deg)
        elif st == "PIPE":
            make_pipe(bm, seg, sz, ir, height3d)
        elif st == "BOLT":
            make_bolt(bm, seg, shaft_radius*sz, shaft_length*sz, head_radius*sz, head_height*sz)
        elif st == "CAPSULE":
            make_capsule(bm, seg, sz, height3d, int(obj.get("cap_segments", 16)), taper)
        elif st == "GEOMETRIC_SPHERE":
            make_geometric_sphere(bm, seg, int(obj.get("vertical_segments", 32)), sz, float(obj.get("exp_lat", 2.0)), float(obj.get("exp_long", 2.0)))
        elif st == "BUCKYBALL":
            make_buckyball(bm, radius=sz, detail=int(obj.get("detail", 1)))

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

# ----------------------------------------------------------
# Operator / Update
# ----------------------------------------------------------

class MESHGEN_OT_generate(bpy.types.Operator):
    bl_idname = "mesh.mesh_generator"
    bl_label = "Generate Mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p = context.scene.meshgen_props
        mesh = bpy.data.meshes.new(f"{p.shape_type}_Object")
        obj = bpy.data.objects.new(mesh.name, mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        for k in p.__annotations__.keys():
            obj[k] = getattr(p, k)

        obj["shape_collection"] = p.shape_collection

        rebuild_shape(obj)

        return {'FINISHED'}

def update_shape(self, context):
    if not hasattr(self, "shape_type"):
        return

    obj = context.active_object

    if (
        not obj or
        obj.type != 'MESH' or
        not obj.select_get() or
        "shape_type" not in obj or
        "shape_collection" not in obj
    ):
        return

    for k in self.__annotations__.keys():
        if hasattr(self, k):
            obj[k] = getattr(self, k)

    rebuild_shape(obj)

    new_name = f"{self.shape_type}_Shape"
    if obj.name != new_name:
        obj.name = new_name
        obj.data.name = new_name

# ----------------------------------------------------------
# Properties
# ----------------------------------------------------------

SHAPES_2D = [
    ("POLYGON", "Polygon (2D)", ""),
    ("STAR", "Star (2D)", ""),
    ("SUPERELLIPSE", "Superellipse (2D)", ""),
    ("FLOWER", "Flower (2D)", ""),
    ("PLUS", "Plus (2D)", ""),
    ("CROSS", "Cross (2D)", ""),
    ("CRESCENT", "Crescent (2D)", ""),
    ("ARC_SEGMENT", "Arc Segment (2D)", ""),
    ("GEAR", "Gear (2D)", ""),
    ("VENT_DISK", "Vent Disk (2D)", ""),
]

SHAPES_3D = [
    ("COLUMN", "Column (3D)", ""),
    ("ARCH3D", "Arch (3D)", ""),
    ("DOME", "Dome (3D)", ""),
    ("GEAR3D", "Gear (3D)", ""),
    ("PIPE", "Pipe (3D)", ""),
    ("BOLT", "Bolt (3D)", ""),
    ("CAPSULE", "Capsule (3D)", ""),
    ("GEOMETRIC_SPHERE", "Geometric Sphere (3D)", ""),
    ("BUCKYBALL", "Buckyball (3D)", ""),
]

def shape_items(self, context):
    return SHAPES_2D if self.shape_collection == "2D" else SHAPES_3D

def on_collection_change(self, context):
    if self.shape_collection == "2D":
        self.shape_type = SHAPES_2D[0][0]
    else:
        self.shape_type = SHAPES_3D[0][0]

    update_shape(self, context)

class MeshGenProperties(bpy.types.PropertyGroup):
    shape_collection: bpy.props.EnumProperty(
        name="Shape Collection",
        items=[("2D", "2D", ""), ("THREED", "3D", "")],
        default="2D",
        update=on_collection_change
    )

    shape_type: bpy.props.EnumProperty(name="Shape Type", items=shape_items, update=update_shape)

    segments: bpy.props.IntProperty(name="Segments", default=64, min=3, max=4096, subtype='FACTOR', update=update_shape)
    size: bpy.props.FloatProperty(name="Size", default=1.0, min=0.01, max=100.0, subtype='FACTOR', update=update_shape)

    inner_ratio: bpy.props.FloatProperty(name="Inner Ratio", default=0.5, min=0.01, max=0.99, subtype='FACTOR', update=update_shape)
    exponent: bpy.props.FloatProperty(name="Exponent", default=2.5, min=0.5, max=10.0, subtype='FACTOR', update=update_shape)
    petals: bpy.props.IntProperty(name="Petals", default=5, min=1, max=128, subtype='FACTOR', update=update_shape)
    petal_depth: bpy.props.FloatProperty(name="Petal Depth", default=0.2, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    thickness: bpy.props.FloatProperty(name="Thickness", default=0.2, min=0.01, max=0.99, subtype='FACTOR', update=update_shape)
    roundness: bpy.props.FloatProperty(name="Roundness", default=0.2, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    center_gap: bpy.props.FloatProperty(name="Center Gap", default=0.0, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    offset: bpy.props.FloatProperty(name="Offset", default=0.2, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    angle_start: bpy.props.FloatProperty(name="Start Angle", default=0.0, min=-720.0, max=720.0, subtype='FACTOR', update=update_shape)
    angle_end: bpy.props.FloatProperty(name="End Angle", default=270.0, min=-720.0, max=1080.0, subtype='FACTOR', update=update_shape)

    height3d: bpy.props.FloatProperty(name="Height (Z)", default=1.0, min=0.0, max=100.0, subtype='FACTOR', update=update_shape)
    depth_z: bpy.props.FloatProperty(name="Depth (Z)", default=0.2, min=0.0, max=100.0, subtype='FACTOR', update=update_shape)
    vertical_segments: bpy.props.IntProperty(name="Vertical Segments", default=16, min=2, max=512, subtype='FACTOR', update=update_shape)
    curvature: bpy.props.FloatProperty(name="Curvature", default=1.0, min=0.1, max=3.0, subtype='FACTOR', update=update_shape)
    flutes: bpy.props.IntProperty(name="Flutes", default=12, min=0, max=512, subtype='FACTOR', update=update_shape)
    flute_depth: bpy.props.FloatProperty(name="Flute Depth", default=0.2, min=0.0, max=0.95, subtype='FACTOR', update=update_shape)
    taper: bpy.props.FloatProperty(name="Taper", default=0.0, min=-0.95, max=0.95, subtype='FACTOR', update=update_shape)
    twist_deg: bpy.props.FloatProperty(name="Twist (°)", default=0.0, min=-2160.0, max=2160.0, subtype='FACTOR', update=update_shape)
    thickness_radial: bpy.props.FloatProperty(name="Radial Thickness", default=0.0, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    cap_segments: bpy.props.IntProperty(name="Cap Segments", default=16, min=4, max=512, subtype='FACTOR', update=update_shape)
    entasis: bpy.props.FloatProperty(name="Entasis", default=0.0, min=-0.5, max=0.5, subtype='FACTOR', update=update_shape)
    base_frac: bpy.props.FloatProperty(name="Base Fraction", default=0.05, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    cap_frac: bpy.props.FloatProperty(name="Cap Fraction", default=0.05, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    loop_cuts: bpy.props.IntProperty(name="Loop Cuts", default=2, min=0, max=10, subtype='FACTOR', update=update_shape)

    hub_ratio: bpy.props.FloatProperty(name="Hub Ratio", default=0.3, min=0.0, max=0.95, subtype='FACTOR', update=update_shape)
    shaft_radius: bpy.props.FloatProperty(name="Shaft Radius", default=0.25, min=0.01, max=10.0, subtype='FACTOR', update=update_shape)
    shaft_length: bpy.props.FloatProperty(name="Shaft Length", default=1.0, min=0.01, max=100.0, subtype='FACTOR', update=update_shape)
    head_radius: bpy.props.FloatProperty(name="Head Radius", default=0.5, min=0.01, max=10.0, subtype='FACTOR', update=update_shape)
    head_height: bpy.props.FloatProperty(name="Head Height", default=0.25, min=0.01, max=10.0, subtype='FACTOR', update=update_shape)
    teeth: bpy.props.IntProperty(name="Teeth", default=12, min=2, max=1024, subtype='FACTOR', update=update_shape)
    tooth_depth: bpy.props.FloatProperty(name="Tooth Depth", default=0.25, min=0.0, max=0.95, subtype='FACTOR', update=update_shape)
    hole_count: bpy.props.IntProperty(name="Holes", default=8, min=1, max=256, subtype='FACTOR', update=update_shape)
    hole_width: bpy.props.FloatProperty(name="Hole Width", default=0.15, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    hole_length: bpy.props.FloatProperty(name="Hole Length", default=0.35, min=0.0, max=1.0, subtype='FACTOR', update=update_shape)
    
    exp_lat: bpy.props.FloatProperty(name="Latitude Exponent", default=2.0, min=0.1, max=8.0, subtype='FACTOR', update=update_shape)
    exp_long: bpy.props.FloatProperty(name="Longitude Exponent", default=2.0, min=0.1, max=8.0, subtype='FACTOR', update=update_shape)
    detail: bpy.props.IntProperty(name="Detail", default=1, min=1, max=20, subtype='FACTOR', update=update_shape)

# ----------------------------------------------------------
# UI
# ----------------------------------------------------------

class VIEW3D_PT_mesh_generator(bpy.types.Panel):
    bl_label = "Mesh"
    bl_idname = "VIEW3D_PT_mesh_generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mesh"

    def draw(self, context):
        layout = self.layout
        p = context.scene.meshgen_props
        o = context.object

        layout.operator("mesh.mesh_generator", text="Generate Mesh", icon="MESH_DATA")

        layout.separator(factor=0.5)

        layout.prop(p, "shape_collection", expand=True)
        layout.prop(p, "shape_type")
        layout.prop(p, "segments")
        layout.prop(p, "size")

        layout.separator(factor=0.5)

        st = p.shape_type
        col = p.shape_collection

        #       2D PARAMETERS
        if col == "2D":

            if st == "STAR":
                layout.prop(p, "inner_ratio")

            elif st == "SUPERELLIPSE":
                layout.prop(p, "exponent")

            elif st == "FLOWER":
                layout.prop(p, "petals")
                layout.prop(p, "petal_depth")

            elif st == "PLUS":
                layout.prop(p, "thickness")

            elif st == "CROSS":
                layout.prop(p, "thickness")
                layout.prop(p, "center_gap")

            elif st == "CRESCENT":
                layout.prop(p, "inner_ratio")
                layout.prop(p, "offset")

            elif st == "ARC_SEGMENT":
                layout.prop(p, "thickness")
                layout.prop(p, "angle_start")
                layout.prop(p, "angle_end")

            elif st == "GEAR":
                layout.prop(p, "teeth")
                layout.prop(p, "tooth_depth")
                layout.prop(p, "roundness")

            elif st == "VENT_DISK":
                layout.prop(p, "hole_count")
                layout.prop(p, "hole_width")
                layout.prop(p, "hole_length")

        #       3D PARAMETERS
        else:

            if st == "COLUMN":
                layout.prop(p, "height3d")
                layout.prop(p, "flutes")
                layout.prop(p, "flute_depth")
                layout.prop(p, "taper")
                layout.prop(p, "twist_deg")
                layout.prop(p, "entasis")
                layout.prop(p, "base_frac")
                layout.prop(p, "cap_frac")
                layout.prop(p, "loop_cuts")

            elif st == "ARCH3D":
                layout.prop(p, "inner_ratio")
                layout.prop(p, "thickness_radial")
                layout.prop(p, "angle_start")
                layout.prop(p, "angle_end")
                layout.prop(p, "depth_z")

            elif st == "DOME":
                layout.prop(p, "vertical_segments")
                layout.prop(p, "curvature")

            elif st == "GEAR3D":
                layout.prop(p, "teeth")
                layout.prop(p, "tooth_depth")
                layout.prop(p, "roundness")
                layout.prop(p, "hub_ratio")
                layout.prop(p, "depth_z")
                layout.prop(p, "taper")
                layout.prop(p, "twist_deg")

            elif st == "PIPE":
                layout.prop(p, "inner_ratio")
                layout.prop(p, "height3d")

            elif st == "BOLT":
                layout.prop(p, "shaft_radius")
                layout.prop(p, "shaft_length")
                layout.prop(p, "head_radius")
                layout.prop(p, "head_height")

            elif st == "CAPSULE":
                layout.prop(p, "height3d")
                layout.prop(p, "cap_segments")
                layout.prop(p, "taper")

            elif st == "GEOMETRIC_SPHERE":
                layout.prop(p, "vertical_segments")
                layout.prop(p, "exp_lat")
                layout.prop(p, "exp_long")

            elif st == "BUCKYBALL":
                layout.prop(p, "detail")

        layout.separator(factor=0.5)

        if (
            o and o.type == "MESH"
            and "shape_type" in o
            and "shape_collection" in o
            and o.select_get()
        ):
            layout.label(text=f"Editing: {o['shape_type']}", icon="MESH_DATA")
        else:
            layout.label(text="No mesh selected", icon="INFO")

# ----------------------------------------------------------
# Register
# ----------------------------------------------------------

classes = (
    MeshGenProperties,
    MESHGEN_OT_generate,
    VIEW3D_PT_mesh_generator, 
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.meshgen_props = bpy.props.PointerProperty(type=MeshGenProperties)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.meshgen_props

if __name__ == "__main__":
    register()
