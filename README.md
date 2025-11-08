# Mesh Generator

![mesh-thumb](https://github.com/user-attachments/assets/e84162a7-7e7b-4add-adec-863a9abb4d84)

**Author:** The French Monkey (TFMSTYLE)  
**Version:** 1.0.0  

---

## Overview

The **Mesh Generator** is a procedural modeling toolset for Blender that provides parametric control over a large collection of **2D** and **3D** geometric primitives.  
It allows users to generate and modify shapes directly from adjustable parameters in the properties panel.

The add-on uses **BMesh** for dynamic topology construction and supports real-time updates when parameters are modified, enabling a highly flexible and non-destructive workflow.

---

## Shape Collections

### Shape Collection
Determines whether to generate **2D** or **3D** shapes.  
- **2D:** Flat surface meshes (useful for extrusion or pattern design).  
- **3D:** Volumetric meshes with height, curvature, and complex surface geometry.

---

## Shape Type
Specifies the particular geometry to generate.  
Shape types are grouped by their collection:

### 2D Shapes
- **Polygon** — Regular n-sided polygon.  
- **Star** — Alternating outer/inner radii to form pointed shapes.  
- **Superellipse** — Rounded rectangle or supercircle.  
- **Flower** — Organic sinusoidal petal-like shape.  
- **Plus** — Plus-shaped mesh with controllable thickness.  
- **Cross** — Cross with adjustable gap and arm width.  
- **Crescent** — Two-circle subtraction forming a moon-like shape.  
- **Arc Segment** — Circular segment defined by start/end angles.  
- **Gear** — 2D cogwheel profile.  
- **Vent Disk** — Circular disk with radial holes.

### 3D Shapes
- **Column** — Fluted architectural column with taper and entasis.  
- **Arch** — 3D arched segment with radial thickness and depth.  
- **Dome** — Hemispherical dome with curvature control.  
- **Gear3D** — 3D gear with hub, taper, and twist deformation.  
- **Pipe** — Hollow cylindrical mesh.  
- **Bolt** — Hexagonal bolt with shaft and head.  
- **Capsule** — Rounded capsule form with hemispherical ends.  
- **Geometric Sphere** — Parameterized sphere using latitude/longitude exponents.  
- **Buckyball** — Geodesic structure generated from subdivided icosahedron.

---

## Global Parameters

### Segments
Controls the polygonal resolution of generated meshes.  
Higher values yield smoother geometry at the cost of computation.

### Size
Overall scale of the generated shape.  
Affects radius, width, or general size depending on the selected shape.

---

## 2D Parameters

### Inner Ratio
For hollow or nested shapes — defines the ratio between inner and outer radius.

### Exponent
Used in shapes such as **Superellipse**, controls the curvature from round to square.

### Petals
Number of petals for flower-like structures.

### Petal Depth
Amplitude of the petal shape modulation.

### Thickness
Defines radial or profile thickness (used in Cross, Arc, etc.).

### Roundness
Smooths transitions between convex and concave regions (used in gears and organic shapes).

### Center Gap
Adds spacing at the intersection point of the cross arms.

### Offset
Offset between inner and outer arcs for crescent shapes.

### Start Angle
Starting rotation or angular boundary (for arcs and circular segments).

### End Angle
Defines the end of the angular span in degrees.

---

## 3D Parameters

### Height (Z)
Total height of the shape along the Z-axis.

### Depth (Z)
Defines extrusion or mesh depth for shapes like arches and gears.

### Vertical Segments
Number of subdivisions along the vertical axis.  
Affects smoothness of domes, capsules, and spheres.

### Curvature
Controls dome or surface curvature intensity.

### Flutes
Number of vertical grooves (applies to columns).

### Flute Depth
Depth of each flute indentation.

### Taper
Scales the shape along its vertical axis to narrow or widen toward the top.

### Twist (°)
Applies a twist deformation along the Z-axis in degrees.

### Radial Thickness
Controls radial wall thickness in arch or ring-like structures.

### Cap Segments
Number of subdivisions in the rounded caps (used in capsules).

### Entasis
Adjusts the subtle curvature of a column shaft (common in classical architecture).

### Base Fraction
Proportion of total height allocated to the column base.

### Cap Fraction
Proportion of total height allocated to the column capital (top section).

### Loop Cuts
Defines the number of smoothing loops between column sections.

---

## Gear Parameters

### Teeth
Number of teeth around the gear perimeter.

### Tooth Depth
Depth of the tooth profile.

### Hub Ratio
Size of the central hub relative to the gear’s outer radius.

---

## Bolt Parameters

### Shaft Radius
Radius of the cylindrical shaft.

### Shaft Length
Length of the shaft portion.

### Head Radius
Radius of the bolt head.

### Head Height
Vertical thickness of the head.

---

## Vent Disk Parameters

### Holes
Number of radial holes.

### Hole Width
Controls the horizontal size of each vent opening.

### Hole Length
Controls the longitudinal size of each vent opening.

---

## Geometric Sphere Parameters

### Latitude Exponent
Controls the vertical deformation — smaller values flatten poles, larger values stretch them.

### Longitude Exponent
Controls the horizontal deformation — affects equatorial roundness.

---

## Buckyball Parameters

### Detail
Level of icosahedral subdivision for the geodesic dome.  
Higher values produce smoother and denser meshes.

---

## Technical Notes

- All shapes are generated via **BMesh** for efficient geometry construction.  
- 3D shapes often feature **loop bridging** and **polar capping** logic for closed surfaces.  
- **Twist** and **Taper** transformations are applied progressively along the Z-axis.  
- Normal recalculation and duplicate removal ensure clean, manifold results.  
- Real-time updates occur when adjusting parameters in the UI.

---

## Workflow

1. Choose **Shape Collection** (2D or 3D).  
2. Select a **Shape Type** from the available list.  
3. Adjust relevant parameters (size, segments, ratio, height, etc.).  
4. Click **Generate Mesh** to create a new object.  
5. Modify parameters interactively — the object updates automatically.  
6. Export or convert to standard mesh data for modeling or rendering.
