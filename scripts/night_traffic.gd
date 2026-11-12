extends Node2D
## Изредка по дороге проезжает машина (седан из пакета в одной из расцветок —
## подряд одна и та же не повторяется) с фарами:
## луч фар вдоль дороги, пятно света (PointLight2D) — оно подсвечивает асфальт,
## фасады и героя, — блик фар на мокром асфальте и красные задние огни.
## Машины появляются за краем кадра и пропадают, уехав далеко.
## Звук (шины по мокрому асфальту + мотор) привязан к машине: громкость и
## панорама — по расстоянию до камеры, тон чуть выше при приближении и ниже,
## когда машина уехала (эффект Доплера).

@export var car_textures: Array[Texture2D] = []
@export var glow_texture: Texture2D
@export var cone_texture: Texture2D
@export var car_sound: AudioStream
@export var sound_volume_db := -6.0
@export var doppler := 0.07
@export var car_scale := 2.0
@export var min_delay := 18.0
@export var max_delay := 35.0
@export var first_delay := 6.0
@export var lane_y := 664.0           ## где колёса касаются дороги
@export var speed_min := 300.0
@export var speed_max := 380.0

## Точки на спрайте седана (в пикселях текстуры; спрайт смотрит влево).
const TEX_W := 171.0
const TEX_BOTTOM := 64.0
const HEADLIGHT := Vector2(12, 42)
const TAILLIGHT := Vector2(161, 38)

var _timer := 0.0
var _last := -1
var _cars: Array[Node2D] = []


func _ready() -> void:
	_timer = first_delay


func _process(delta: float) -> void:
	_timer -= delta
	if _timer <= 0.0:
		_timer = randf_range(min_delay, max_delay)
		_spawn()
	var cam := get_viewport().get_camera_2d()
	for car in _cars.duplicate():
		var x: float = car.get_meta("x") + float(car.get_meta("v")) * delta
		car.set_meta("x", x)
		car.position.x = roundf(x)
		var snd := car.get_node_or_null("Sound") as AudioStreamPlayer2D
		if snd and cam:
			var v: float = car.get_meta("v")
			# >0 — машина приближается к камере, <0 — удаляется.
			var approach := clampf(-(x - cam.global_position.x) * signf(v) / 400.0, -1.0, 1.0)
			snd.pitch_scale = 1.0 + doppler * approach
		# Вдали звук плавно затихает, чтобы не обрываться щелчком при удалении машины.
		var far := absf(x - cam.global_position.x) if cam else 0.0
		var snd_far := car.get_node_or_null("Sound") as AudioStreamPlayer2D
		if snd_far:
			snd_far.volume_db = sound_volume_db + linear_to_db(clampf(1.0 - (far - 1000.0) / 400.0, 0.001, 1.0))
		if far > 1400.0:
			_cars.erase(car)
			car.queue_free()


func _local(p: Vector2, dir: float) -> Vector2:
	# Точка текстуры -> координаты машины (начало — центр низа колёс).
	var x := (p.x - TEX_W / 2.0) * car_scale
	if dir > 0.0:
		x = -x  # едет вправо — спрайт отражён
	return Vector2(x, (p.y - TEX_BOTTOM) * car_scale)


func _add_glow(parent: Node2D, pos: Vector2, color: Color, sc: Vector2) -> void:
	var g := Sprite2D.new()
	g.texture = glow_texture
	g.material = _add_material()
	g.modulate = color
	g.position = pos
	g.scale = sc
	parent.add_child(g)


func _add_material() -> CanvasItemMaterial:
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return m


func _spawn() -> void:
	var cam := get_viewport().get_camera_2d()
	if cam == null or car_textures.is_empty():
		return
	var pick := randi() % car_textures.size()
	if car_textures.size() > 1 and pick == _last:
		pick = (pick + 1 + randi() % (car_textures.size() - 1)) % car_textures.size()
	_last = pick
	var dir := 1.0 if randf() < 0.5 else -1.0
	var x := cam.global_position.x - dir * 800.0
	var car := Node2D.new()
	car.position = Vector2(x, lane_y)
	car.set_meta("x", x)
	car.set_meta("v", dir * randf_range(speed_min, speed_max))

	var body := Sprite2D.new()
	body.texture = car_textures[pick]
	body.scale = Vector2(car_scale, car_scale)
	body.centered = false
	body.offset = Vector2(-TEX_W / 2.0, -TEX_BOTTOM)
	body.flip_h = dir > 0.0
	car.add_child(body)

	var head := _local(HEADLIGHT, dir)
	var tail := _local(TAILLIGHT, dir)
	# Луч фар: конус, положенный вдоль дороги по ходу движения.
	var beam := Sprite2D.new()
	beam.texture = cone_texture
	beam.material = _add_material()
	beam.modulate = Color(1, 0.9, 0.7, 0.22)
	beam.centered = false
	beam.offset = Vector2(-48, 0)
	beam.scale = Vector2(0.9, 2.6)
	beam.rotation = -dir * PI / 2.0
	beam.position = head
	car.add_child(beam)
	_add_glow(car, head, Color(1, 0.92, 0.75, 0.8), Vector2(0.9, 0.6))
	_add_glow(car, tail, Color(1, 0.15, 0.1, 0.6), Vector2(0.6, 0.45))
	# Блик фар на мокром асфальте — вытянутое пятно под машиной.
	_add_glow(car, Vector2(head.x + dir * 30.0, 50.0), Color(1, 0.85, 0.6, 0.35), Vector2(1.4, 2.4))
	# Настоящий свет: подсвечивает дорогу, фасады и героя впереди машины.
	var light := PointLight2D.new()
	light.texture = glow_texture
	light.texture_scale = 7.0
	light.color = Color(1, 0.88, 0.7)
	light.energy = 0.9
	light.position = head + Vector2(dir * 200.0, -40.0)
	car.add_child(light)

	if car_sound:
		var snd := AudioStreamPlayer2D.new()
		snd.name = "Sound"
		snd.stream = SoundUtil.looped(car_sound)
		snd.volume_db = sound_volume_db
		snd.max_distance = 1800.0
		snd.attenuation = 1.6
		car.add_child(snd)

	add_child(car)
	_cars.append(car)
	var s := car.get_node_or_null("Sound") as AudioStreamPlayer2D
	if s:
		s.play(randf() * 3.0)
