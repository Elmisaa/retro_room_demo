extends Node2D
## Тени героя от источников света. Вешается на узел «Shadows» внутри героя
## (перед его спрайтом, чтобы тени были под ним).
##
## Для каждого источника создаётся тёмная копия текущего кадра героя,
## «положенная» на тротуар: она тянется от источника (длина — по подобию
## треугольников: чем ниже свет и чем дальше герой, тем длиннее тень)
## и бледнеет с расстоянием. Если источник выключен (мигалка), тень пропадает.

## Источники: узлы, по позиции которых считается тень.
@export var lights: Array[NodePath] = []
## Куда ложится тень: -1 — к стене (свет перед героем, у бордюра),
## +1 — к зрителю (свет на стене, позади героя). По одному значению на источник.
@export var depth: Array[float] = []
## Дальность действия источника по горизонтали, px.
@export var ranges: Array[float] = []
## Сила тени от источника (0..1).
@export var strength: Array[float] = []

@export var max_alpha := 0.55
@export var depth_len := 36.0      ## насколько тень уходит вверх/вниз по тротуару
@export var max_len := 220.0       ## максимальная длина тени по горизонтали

const HERO_H := 160.0  ## видимый рост героя на экране (макушка ≈ 160 px над ступнями)

var _hero: Sprite2D
var _pivots: Array[Node2D] = []
var _sprites: Array[Sprite2D] = []


func _ready() -> void:
	_hero = get_parent().get_node("Sprite")
	for i in lights.size():
		var pivot := Node2D.new()
		var s := Sprite2D.new()
		s.texture = _hero.texture
		s.hframes = _hero.hframes
		s.centered = false
		s.offset = _hero.offset
		s.scale = _hero.scale
		s.modulate = Color(0, 0, 0, 0)
		pivot.add_child(s)
		add_child(pivot)
		_pivots.append(pivot)
		_sprites.append(s)


func _process(_delta: float) -> void:
	var feet := global_position
	for i in lights.size():
		var light := get_node_or_null(lights[i]) as Node2D
		var s := _sprites[i]
		s.frame = _hero.frame
		s.flip_h = _hero.flip_h
		if light == null or not light.is_visible_in_tree():
			s.modulate.a = 0.0
			continue
		var lp := light.global_position
		var dx := feet.x - lp.x
		var rng := ranges[i] if i < ranges.size() else 400.0
		var fall := clampf(1.0 - absf(dx) / rng, 0.0, 1.0)
		var st := strength[i] if i < strength.size() else 1.0
		s.modulate.a = max_alpha * st * pow(fall, 0.7)
		# Длина по подобию треугольников, направление — от источника.
		var h := maxf(feet.y - lp.y, 40.0)
		var tip_x := clampf(dx * HERO_H / h, -max_len, max_len)
		var d := depth[i] if i < depth.size() else -1.0
		var tip_y := d * depth_len
		# Ось Y спрайта ведёт от ступней к макушке; переводим макушку в точку тени.
		_pivots[i].transform = Transform2D(Vector2(1, 0), Vector2(-tip_x / HERO_H, -tip_y / HERO_H), Vector2.ZERO)
