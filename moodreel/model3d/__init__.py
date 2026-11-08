"""Characters modelled as signed distance fields, meshed, rigged and checked.

  sdf        distance-field primitives, placement and (smooth) booleans
  mesh       surface nets with Newton projection: closed meshes with exact normals
  build      a spec (BONES, PARTS, POSES, ...) into one skinned model; Part
  skin       poses as bone rotations: linear blend skinning, two-bone reach (the same maths as kit/figure.js)
  export     the model as <NAME>.json and <NAME>.bin, and back
  check      closed parts, floating parts and penetration in every pose
  sheet      a contact sheet: views x poses, rendered in headless Chrome
  mannequin  a generic jointed figure, 1.72 m: the reference spec and the test model
"""
