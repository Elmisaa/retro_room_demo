// Фон меню-паузы: лёгкое размытие того, что под ним, и затемнение.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
// Радиус размытия в пикселях экрана.
uniform float blur_radius : hint_range(0.0, 12.0) = 3.0;
// 0 — без затемнения, 1 — чёрный экран.
uniform float dim : hint_range(0.0, 1.0) = 0.55;

void fragment() {
	vec2 px = SCREEN_PIXEL_SIZE * blur_radius;
	vec3 c = texture(screen_tex, SCREEN_UV).rgb * 0.2;
	// Два кольца по 8 точек: ближнее весит больше, дальнее меньше.
	for (int i = 0; i < 8; i++) {
		float a = float(i) * TAU / 8.0;
		vec2 d = vec2(cos(a), sin(a));
		c += texture(screen_tex, SCREEN_UV + d * px).rgb * 0.06;
		c += texture(screen_tex, SCREEN_UV + d * px * 2.0).rgb * 0.04;
	}
	COLOR = vec4(c * (1.0 - dim), 1.0);
}
