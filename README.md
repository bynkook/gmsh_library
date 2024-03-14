## GMSH LIBRARY

### libgmsh_001.py
1. draw rectangular
2. in the rectangular area, add circle and center point at (x,y) given
3. add vertical & horizontal reference line for result collecting nodes

known issue:
mesh.embed cannot embed point to edge of surface.  therefore there is no proper solution to put a node to center of circle when line passing through circle center.

![out1](https://github.com/bynkook/gmsh_library/assets/41982943/b19570d7-1847-4faa-ad6b-425ab0f102ad)
