// Greg Allen shed - first printable Bambu Lab P1S model
// Source: uploaded handwritten shop drawings
// Units in this file are millimeters. Source dimensions are inches, scaled 1:16.
// Visible drawing dimensions used: front width 45", back width 62.25", depth 85.5",
// wall/eave height 45", ridge height 60".

$fn = 48;
scale_factor = 16;
function inch(v) = v * 25.4 / scale_factor;

front_width = inch(45);
back_width = inch(62.25);
depth = inch(85.5);
eave_height = inch(45);
ridge_height = inch(60);
base_height = inch(2);
wall_t = inch(1.5);
roof_t = inch(1.25);
roof_overhang = inch(3);

batten_spacing = inch(7.5);
batten_w = max(inch(0.75), 0.65);
batten_d = max(inch(0.35), 0.45);
trim_w = max(inch(1.5), 1.0);
trim_d = max(inch(0.45), 0.55);

y_front = -depth / 2;
y_back = depth / 2;
z0 = base_height;
z_eave = base_height + eave_height;
z_peak = base_height + ridge_height;

module centered_box(size, center_point, rz = 0) {
  translate(center_point)
    rotate([0, 0, rz])
      cube(size, center = true);
}

module prism_from_footprint(points, zmin, zmax) {
  polyhedron(
    points = concat(
      [for (p = points) [p[0], p[1], zmin]],
      [for (p = points) [p[0], p[1], zmax]]
    ),
    faces = [
      [3, 2, 1, 0],
      [4, 5, 6, 7],
      [0, 1, 5, 4],
      [1, 2, 6, 5],
      [2, 3, 7, 6],
      [3, 0, 4, 7]
    ]
  );
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

module side_wall(side = 1) {
  xf = side * front_width / 2;
  xb = side * back_width / 2;
  dx = xb - xf;
  len = sqrt(dx * dx + depth * depth);
  angle = atan2(depth, dx);
  centered_box([len, wall_t, eave_height], [(xf + xb) / 2 + side * wall_t / 2, 0, z0 + eave_height / 2], angle);
}

module side_battens(side = 1) {
  xf = side * (front_width / 2 + wall_t);
  xb = side * (back_width / 2 + wall_t);
  dx = xb - xf;
  len = sqrt(dx * dx + depth * depth);
  angle = atan2(depth, dx);
  count = max(2, floor(len / batten_spacing));
  for (i = [1 : count - 1]) {
    t = i / count;
    x = xf + dx * t + side * batten_d * 0.35;
    y = y_front + depth * t;
    centered_box([batten_w, batten_d, eave_height], [x, y, z0 + eave_height / 2], angle);
  }
}

module front_back_battens(y, width, label_height = eave_height) {
  count = max(2, floor(width / batten_spacing));
  for (i = [1 : count - 1]) {
    x = -width / 2 + width * i / count;
    centered_box([batten_w, batten_d, label_height], [x, y, z0 + label_height / 2]);
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
  prism_from_footprint([
    [-front_width / 2 - wall_t, y_front - wall_t],
    [ front_width / 2 + wall_t, y_front - wall_t],
    [ back_width / 2 + wall_t, y_back + wall_t],
    [-back_width / 2 - wall_t, y_back + wall_t]
  ], 0, base_height);

  centered_box([front_width + 2 * wall_t, wall_t, eave_height], [0, y_front - wall_t / 2, z0 + eave_height / 2]);
  centered_box([back_width + 2 * wall_t, wall_t, eave_height], [0, y_back + wall_t / 2, z0 + eave_height / 2]);
  triangle_prism(-front_width / 2 - wall_t, front_width / 2 + wall_t, y_front - wall_t / 2, wall_t, z_eave, z_peak);
  triangle_prism(-back_width / 2 - wall_t, back_width / 2 + wall_t, y_back + wall_t / 2, wall_t, z_eave, z_peak);
  side_wall(-1);
  side_wall(1);

  quad_plate([0, y_front - roof_overhang, z_peak], [0, y_back + roof_overhang, z_peak], [back_width / 2 + roof_overhang, y_back + roof_overhang, z_eave], [front_width / 2 + roof_overhang, y_front - roof_overhang, z_eave], roof_t);
  quad_plate([0, y_back + roof_overhang, z_peak], [0, y_front - roof_overhang, z_peak], [-front_width / 2 - roof_overhang, y_front - roof_overhang, z_eave], [-back_width / 2 - roof_overhang, y_back + roof_overhang, z_eave], roof_t);
  centered_box([inch(2), depth + 2 * roof_overhang, inch(2)], [0, 0, z_peak + inch(0.5)]);

  door_detail();
  front_back_battens(y_back + wall_t + batten_d / 2, back_width, eave_height);
  side_battens(-1);
  side_battens(1);
}

shed_model();
