// Передний план: предмет почти у камеры — тёмный силуэт с лёгким размытием
// (как будто не в фокусе). Вешается на Sprite2D переднего плана.
shader_type canvas_item;

// Цвет силуэта (очень тёмный, с оттенком ночи).
uniform vec3 tint : source_color = vec3(0.02, 0.025, 0.045);
// Сколько собственного цвета предмета оставить (0 — чистый силуэт).
uniform float keep_color : hint_range(0.0, 1.0) = 0.12;
// Радиус размытия в пикселях текстуры.
uniform float blur : hint_range(0.0, 6.0) = 1.5;

void fragment() {
	vec2 px = TEXTURE_PIXEL_SIZE * blur;
	vec4 c = texture(TEXTURE, UV) * 0.2;
	for (int i = 0; i < 8; i++) {
		float a = float(i) * TAU / 8.0;
		c += texture(TEXTURE, UV + vec2(cos(a), sin(a)) * px) * 0.1;
	}
	COLOR = vec4(mix(tint, c.rgb, keep_color), c.a * COLOR.a);
}
