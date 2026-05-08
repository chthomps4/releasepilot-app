// Greg Allen shed - corrected rectangular Bambu Lab P1S model
// Source: uploaded handwritten shop drawings.
// Corrected interpretation: the shed is square-cornered / rectangular in plan, not tapered.
// Units in this file are millimeters. Source dimensions are inches, scaled 1:16.
// Drawing dimensions used: width 62.25", depth 85.5", eave height 45", ridge height 60".

$fn = 48;
scale_factor = 16;
function inch(v) = v * 25.4 / scale_factor;

shed_width = inch(62.25);
shed_depth = inch(85.5);
eave_height = inch(45);
ridge_height = inch(60);
base_height = inch(2);
wall_t = inch(1.5);
roof_t = inch(1.25);
roof_overhang_front_back = inch(3);
roof_overhang_sides = inch(3);

batten_spacing = inch(7.5);
batten_w = max(inch(0.75), 0.65);
batten_d = max(inch(0.35), 0.45);
trim_w = max(inch(1.5), 1.0);
trim_d = max(inch(0.45), 0.55);
ridge_cap_w = inch(2);

y_front = -shed_depth / 2;
y_back = shed_depth / 2;
z0 = base_height;
z_eave = z0 + eave_height;
z_peak = z0 + ridge_height;

module centered_box(size, center_point, rz = 0) {
  translate(center_point)
    rotate([0, 0, rz])
      cube(size, center = true);
}

module triangle_prism(xl, xr, yc, t, zbase, zpeak) {
  y0 = yc - t / 2;
  y1 = yc + t / 2;
  polyhedron(
    points = [
      [xl, y0, zbase], [xr, y0, zbase], [0, y0, zpeak],
      [xl, y1, zbase], [xr, y1, zbase], [0, y1, zpeak]
    ],
    faces = [
      [0, 2, 1], [3, 4, 5],
      [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]
    ]
  );
}

module quad_plate(p0, p1, p2, p3, t) {
  polyhedron(
    points = [p0, p1, p2, p3, [p0[0],p0[1],p0[2]-t], [p1[0],p1[1],p1[2]-t], [p2[0],p2[1],p2[2]-t], [p3[0],p3[1],p3[2]-t]],
    faces = [
      [0,1,2,3], [7,6,5,4],
      [0,4,5,1], [1,5,6,2], [2,6,7,3], [3,7,4,0]
    ]
  );
}

module front_back_battens(y, width, height = eave_height) {
  count = max(2, floor(width / batten_spacing));
  for (i = [1 : count - 1]) {
    x = -width / 2 + width * i / count;
    centered_box([batten_w, batten_d, height], [x, y, z0 + height / 2]);
  }
}

module side_battens(x, depth, height = eave_height) {
  count = max(2, floor(depth / batten_spacing));
  for (i = [1 : count - 1]) {
    y = -depth / 2 + depth * i / count;
    centered_box([batten_d, batten_w, height], [x, y, z0 + height / 2]);
  }
}

module door_detail() {
  door_w = inch(45);
  door_h = inch(45);
  door_y = y_front - wall_t - trim_d * 0.55;
  centered_box([door_w, trim_d, door_h], [0, door_y, z0 + door_h / 2]);
  centered_box([trim_w, trim_d * 1.2, door_h], [-door_w / 2, door_y - 0.1, z0 + door_h / 2]);
  centered_box([trim_w, trim_d * 1.2, door_h], [door_w / 2, door_y - 0.1, z0 + door_h / 2]);
  centered_box([trim_w * 0.65, trim_d * 1.25, door_h], [0, door_y - 0.15, z0 + door_h / 2]);
  centered_box([door_w + trim_w, trim_d * 1.2, trim_w], [0, door_y - 0.1, z0 + door_h]);
  centered_box([door_w + trim_w, trim_d * 1.2, trim_w], [0, door_y - 0.1, z0]);
  centered_box([trim_w * 0.7, trim_d * 1.6, trim_w * 1.8], [-door_w * 0.08, door_y - trim_d * 0.8, z0 + door_h * 0.55]);
  centered_box([trim_w * 0.7, trim_d * 1.6, trim_w * 1.8], [door_w * 0.08, door_y - trim_d * 0.8, z0 + door_h * 0.55]);
  front_back_battens(y_front - wall_t - batten_d / 2, door_w, door_h - 2 * trim_w);
}

module shed_model() {
  centered_box([shed_width + 2 * wall_t, shed_depth + 2 * wall_t, base_height], [0, 0, base_height / 2]);
  centered_box([shed_width + 2 * wall_t, wall_t, eave_height], [0, y_front - wall_t / 2, z0 + eave_height / 2]);
  centered_box([shed_width + 2 * wall_t, wall_t, eave_height], [0, y_back + wall_t / 2, z0 + eave_height / 2]);
  centered_box([wall_t, shed_depth, eave_height], [-shed_width / 2 - wall_t / 2, 0, z0 + eave_height / 2]);
  centered_box([wall_t, shed_depth, eave_height], [shed_width / 2 + wall_t / 2, 0, z0 + eave_height / 2]);
  triangle_prism(-shed_width / 2 - wall_t, shed_width / 2 + wall_t, y_front - wall_t / 2, wall_t, z_eave, z_peak);
  triangle_prism(-shed_width / 2 - wall_t, shed_width / 2 + wall_t, y_back + wall_t / 2, wall_t, z_eave, z_peak);

  quad_plate([0, y_front - roof_overhang_front_back, z_peak], [0, y_back + roof_overhang_front_back, z_peak], [shed_width / 2 + roof_overhang_sides, y_back + roof_overhang_front_back, z_eave], [shed_width / 2 + roof_overhang_sides, y_front - roof_overhang_front_back, z_eave], roof_t);
  quad_plate([0, y_back + roof_overhang_front_back, z_peak], [0, y_front - roof_overhang_front_back, z_peak], [-shed_width / 2 - roof_overhang_sides, y_front - roof_overhang_front_back, z_eave], [-shed_width / 2 - roof_overhang_sides, y_back + roof_overhang_front_back, z_eave], roof_t);
  centered_box([ridge_cap_w, shed_depth + 2 * roof_overhang_front_back, ridge_cap_w], [0, 0, z_peak + ridge_cap_w * 0.25]);

  door_detail();
  front_back_battens(y_back + wall_t + batten_d / 2, shed_width, eave_height);
  side_battens(-shed_width / 2 - wall_t - batten_d / 2, shed_depth, eave_height);
  side_battens(shed_width / 2 + wall_t + batten_d / 2, shed_depth, eave_height);

  for (sx = [-1, 1]) for (sy = [-1, 1])
    centered_box([trim_w, trim_w, eave_height], [sx * (shed_width / 2 + wall_t + trim_w / 4), sy * (shed_depth / 2 + wall_t + trim_w / 4), z0 + eave_height / 2]);
}

shed_model();
