// Пост-обработка в духе "пиксельный 3D-рендер + дизеринг + цветокоррекция".
// Godot 4.x. Повесить на ColorRect (Full Rect) внутри CanvasLayer поверх сцены.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;

// Внутреннее "пиксельное" разрешение. Меньше = крупнее пиксели.
uniform vec2 pixel_res = vec2(320.0, 240.0);

// Резкость внутри пиксельной сетки: подчёркивает контуры, как в пиксель-арте.
uniform float sharpen : hint_range(0.0, 2.0) = 0.3;
// Видимая сетка между пикселями (лёгкое затемнение краёв каждого пикселя).
uniform float pixel_grid : hint_range(0.0, 1.0) = 0.0;

// Сколько уровней на канал оставить (меньше = грубее постеризация).
uniform float color_levels : hint_range(2.0, 64.0) = 12.0;
uniform float dither_strength : hint_range(0.0, 2.0) = 1.0;

// Цветокоррекция: тени и света подкрашиваются в заданные цвета.
uniform vec3 shadow_tint : source_color = vec3(0.04, 0.07, 0.18);
uniform vec3 highlight_tint : source_color = vec3(0.85, 0.92, 1.0);
uniform float tint_amount : hint_range(0.0, 1.0) = 0.7;
uniform float saturation : hint_range(0.0, 2.0) = 0.85;
uniform float contrast : hint_range(0.5, 2.0) = 1.1;

// Свечение (bloom): яркие места «расплываются» мягким ореолом.
uniform float bloom_strength : hint_range(0.0, 2.0) = 0.3;
uniform float bloom_threshold : hint_range(0.0, 1.0) = 0.7;
// Радиус ореола в «больших» пикселях.
uniform float bloom_radius : hint_range(1.0, 8.0) = 3.0;

uniform float vignette_strength : hint_range(0.0, 2.0) = 0.6;
uniform float grain_amount : hint_range(0.0, 0.2) = 0.0;

const float BAYER4[16] = float[16](
	 0.0,  8.0,  2.0, 10.0,
	12.0,  4.0, 14.0,  6.0,
	 3.0, 11.0,  1.0,  9.0,
	15.0,  7.0, 13.0,  5.0
);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

vec3 sample_px(vec2 px) {
	return texture(screen_tex, (px + 0.5) / pixel_res).rgb;
}

void fragment() {
	// 1. Пикселизация: берём цвет из центра "большого" пикселя.
	vec2 px = floor(SCREEN_UV * pixel_res);
	vec3 c = sample_px(px);

	// 2. Резкость по соседним большим пикселям (unsharp mask).
	vec3 n = sample_px(px + vec2(1.0, 0.0)) + sample_px(px - vec2(1.0, 0.0))
	       + sample_px(px + vec2(0.0, 1.0)) + sample_px(px - vec2(0.0, 1.0));
	c += (c - n * 0.25) * sharpen;

	// 2b. Свечение: собираем яркость с двух колец вокруг пикселя.
	vec3 glow = vec3(0.0);
	for (int i = 0; i < 12; i++) {
		float a = float(i) * TAU / 12.0;
		vec2 dir = vec2(cos(a), sin(a));
		vec3 s1 = sample_px(floor(px + dir * bloom_radius));
		vec3 s2 = sample_px(floor(px + dir * bloom_radius * 2.0 + 0.5));
		glow += max(s1 - bloom_threshold, 0.0) + max(s2 - bloom_threshold, 0.0) * 0.6;
	}
	glow /= 12.0 * 1.6 * max(1.0 - bloom_threshold, 0.05);
	c += glow * bloom_strength;

	// 3. Насыщенность и контраст.
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, saturation);
	c = (c - 0.5) * contrast + 0.5;

	// 4. Сплит-тонинг: подъём теней и оттенок светов.
	c += shadow_tint * (1.0 - l) * tint_amount;
	c *= mix(vec3(1.0), highlight_tint, tint_amount);

	// 5. Виньетка.
	vec2 d = SCREEN_UV - 0.5;
	c *= 1.0 - dot(d, d) * vignette_strength * 2.0;

	// 6. Зерно (живёт на пиксельной сетке, меняется каждый кадр).
	c += (hash(px + fract(TIME) * 100.0) - 0.5) * grain_amount;

	// 7. Упорядоченный дизеринг Байера 4x4 + квантование цвета.
	ivec2 ip = ivec2(px);
	float b = BAYER4[(ip.x % 4) + (ip.y % 4) * 4] / 16.0 - 0.5;
	c += b * dither_strength / color_levels;
	c = floor(c * color_levels + 0.5) / color_levels;

	// 8. Сетка: слегка затемняем край каждого большого пикселя.
	vec2 f = fract(SCREEN_UV * pixel_res);
	float edge = step(0.85, max(f.x, f.y));
	c *= 1.0 - edge * pixel_grid;

	COLOR = vec4(clamp(c, 0.0, 1.0), 1.0);
}
