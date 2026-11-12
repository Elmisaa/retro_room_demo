extends Node2D
## Редкие машины по дороге: появляются за краем экрана, проезжают с фарами.

const CARS := [
	preload("res://assets/street/car_a.png"),
	preload("res://assets/street/car_b.png"),
	preload("res://assets/street/car_c.png"),
]
const CONE := preload("res://assets/street/beam.png")

@export var light_texture: Texture2D
@export var min_delay := 5.0
@export var max_delay := 11.0
## Полосы: y нижнего края машины (в пикселях окна) и направление.
@export var lanes: Array[Vector2] = [Vector2(606, -1), Vector2(642, 1)]

var _timer := 2.0
var _cars: Array[Node2D] = []


func _process(delta: float) -> void:
	_timer -= delta
	if _timer <= 0.0:
		_timer = randf_range(min_delay, max_delay)
		_spawn()

	var cam := get_viewport().get_camera_2d()
	for car in _cars.duplicate():
		var v: float = car.get_meta("speed")
		var fx: float = car.get_meta("x") + v * delta
		car.set_meta("x", fx)
		car.position.x = snappedf(fx, 3.0)
		if cam and absf(car.position.x - cam.global_position.x) > 1100.0:
			_cars.erase(car)
			car.queue_free()


func _spawn() -> void:
	var cam := get_viewport().get_camera_2d()
	if cam == null:
		return
	var lane: Vector2 = lanes[randi() % lanes.size()]
	var dir := lane.y
	var car := Node2D.new()
	var x := cam.global_position.x - dir * 700.0
	car.position = Vector2(x, lane.x)
	car.set_meta("x", x)
	car.set_meta("speed", dir * randf_range(260.0, 340.0))

	var body := Sprite2D.new()
	body.texture = CARS[randi() % CARS.size()]
	body.centered = false
	body.offset = Vector2(-30, -22)
	body.scale = Vector2(3, 3)
	body.flip_h = dir < 0.0
	car.add_child(body)

	# Луч фар: вытянутый конус, положенный горизонтально перед машиной.
	var cone := Sprite2D.new()
	cone.texture = CONE
	cone.material = CanvasItemMaterial.new()
	(cone.material as CanvasItemMaterial).blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	cone.modulate = Color(1.0, 0.85, 0.6, 0.35)
	cone.centered = false
	cone.offset = Vector2(-20, 0)
	cone.scale = Vector2(2.0, 2.0)
	cone.rotation = -dir * PI / 2.0
	cone.position = Vector2(dir * 87.0, -31.0)
	car.add_child(cone)

	if light_texture:
		var light := PointLight2D.new()
		light.texture = light_texture
		light.texture_scale = 1.3
		light.color = Color(1.0, 0.88, 0.65)
		light.energy = 0.7
		light.position = Vector2(dir * 170.0, -30.0)
		car.add_child(light)

	add_child(car)
	_cars.append(car)
