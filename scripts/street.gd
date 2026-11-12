extends Node2D
## Сцена «Улица»: ночной квартал с параллаксом, по которому ходит полицейский.
## Управление: A/D или стрелки — идти, E — осмотреть, Tab — эффект, Esc — меню (пауза).
##
## Графика: assets/street/*.png, генерируется tools/gen_street.py.
## 1 пиксель картинки = 3 пикселя окна = 1 «большой» пиксель шейдера.
## Координаты ниже даны в пикселях картинки (ART) и умножаются на 3.

const ART := 3.0
const HALF_W := 480.0
const WORLD_W := 1200.0 * ART

## x фонарных столбов — те же, что LAMPS в tools/gen_street.py.
const LAMPS := [96, 300, 470, 730, 920, 1120]
## Остальной свет: [x, y, цвет, энергия, масштаб, мерцание, частота морганий]
const LIGHTS := [
	[238, 124, Color(1.0, 0.35, 0.75), 0.7, 0.8, 0.08, 0.3],   # неон «КАФЕ»
	[238, 150, Color(1.0, 0.85, 0.6), 0.6, 1.0, 0.02, 0.0],    # свет витрины кафе на тротуаре
	[600, 104, Color(0.6, 0.75, 1.0), 0.6, 0.7, 0.03, 0.0],    # табличка «ПОЛИЦИЯ»
	[579, 121, Color(1.0, 0.9, 0.7), 0.5, 0.5, 0.04, 0.0],     # фонари у входа
	[622, 121, Color(1.0, 0.9, 0.7), 0.5, 0.5, 0.04, 0.0],
	[1104, 124, Color(0.4, 1.0, 0.6), 0.7, 0.8, 0.06, 0.5],    # неон «24»
	[1104, 150, Color(0.9, 1.0, 0.85), 0.5, 1.0, 0.02, 0.0],   # свет витрины магазина
	[964, 78, Color(1.0, 0.75, 0.5), 0.35, 0.5, 0.1, 0.0],     # окно за курильщиком
]
## Точки осмотра: [x, название, реплика]
const POINTS := [
	[163, "Переулок", "Из переулка тянет сыростью. Где-то звякнула крышка мусорного бака."],
	[238, "Кафе", "Кафе работает до последнего посетителя. Посетителей нет уже час."],
	[541, "Тумба связи", "Тумба экстренной связи. Трубка ещё тёплая."],
	[600, "Участок", "Участок. Дежурный машет через стекло: «Опаздываешь»."],
	[660, "Служебная машина", "Служебная машина. Мигалку опять забыли выключить."],
	[711, "Переулок", "Узкий проход между домами. Слишком тихо."],
	[964, "Балкон", "Сосед с третьего этажа снова курит на балконе. Кивает, как старому знакомому."],
	[1104, "Круглосуточный", "Круглосуточный. Продавец спит за прилавком."],
]
const INTERACT_RADIUS := 20.0 * ART

@export var light_texture: Texture2D
@export var cone_texture: Texture2D
@export var flicker_script: Script

@onready var cam: Camera2D = $Camera
@onready var player: Node2D = $World/Player
@onready var lights_root: Node2D = $World/Lights
@onready var post: ColorRect = $PostFX/Effect
@onready var hint: Label = $UI/BottomBar/Hint
@onready var subtitle: Label = $UI/BottomBar/Subtitle
@onready var fade: ColorRect = $UI/Fade

var _cam_x := HALF_W
var _subtitle_timer := 0.0
var _near := -1


func _ready() -> void:
	_build_lights()
	_cam_x = clampf(player.position.x, HALF_W, WORLD_W - HALF_W)
	cam.position = Vector2(snappedf(_cam_x, ART), 360.0)
	hint.text = ""
	say("Ночная смена. Пора на участок.")
	# Затемнение доигрывает даже на паузе, чтобы за меню не остался чёрный экран.
	var tw := create_tween().set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw.tween_property(fade, "modulate:a", 0.0, 0.8)


func _build_lights() -> void:
	for x in LAMPS:
		var origin := Vector2(x + 9, 63) * ART
		_add_light(origin + Vector2(0, 30), Color(1.0, 0.8, 0.55), 0.9, 1.8, 0.03, 0.0)
		var cone := Sprite2D.new()
		cone.texture = cone_texture
		cone.material = CanvasItemMaterial.new()
		(cone.material as CanvasItemMaterial).blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		cone.modulate = Color(1.0, 0.82, 0.55, 0.22)
		cone.centered = false
		cone.offset = Vector2(-24, 0)
		cone.scale = Vector2(ART, ART * 0.95)
		cone.position = origin
		lights_root.add_child(cone)
	for l in LIGHTS:
		_add_light(Vector2(l[0], l[1]) * ART, l[2], l[3], l[4], l[5], l[6])


func _add_light(pos: Vector2, color: Color, energy: float, scale_: float, flicker: float, blink: float) -> void:
	var light := PointLight2D.new()
	light.texture = light_texture
	light.position = pos
	light.color = color
	light.energy = energy
	light.texture_scale = scale_
	if flicker_script:
		light.set_script(flicker_script)
		light.set("flicker", flicker)
		light.set("flicker_speed", 2.0)
		light.set("blink_chance", blink)
	lights_root.add_child(light)


func _process(delta: float) -> void:
	# Камера: мягко догоняет героя с небольшим упреждением по ходу движения.
	var target := clampf(player.position.x + player.get("facing") * 90.0, HALF_W, WORLD_W - HALF_W)
	_cam_x = lerpf(_cam_x, target, 1.0 - exp(-delta * 2.5))
	cam.position.x = snappedf(_cam_x, ART)

	_near = -1
	var best := INTERACT_RADIUS
	for i in POINTS.size():
		var d := absf(POINTS[i][0] * ART - player.position.x)
		if d < best:
			best = d
			_near = i
	hint.text = "[E] %s" % POINTS[_near][1] if _near >= 0 else ""

	if _subtitle_timer > 0.0:
		_subtitle_timer -= delta
		if _subtitle_timer <= 0.0:
			subtitle.text = ""


func say(line: String) -> void:
	subtitle.text = line
	_subtitle_timer = 5.0


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	match event.physical_keycode:
		KEY_E:
			if _near >= 0:
				say(POINTS[_near][2])
		KEY_TAB:
			post.visible = not post.visible
