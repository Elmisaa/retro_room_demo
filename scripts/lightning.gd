extends Node
## Гроза: редкие вспышки молнии. Каждая вспышка — несколько быстрых всплесков:
##  - DirectionalLight2D на миг подсвечивает всю улицу;
##  - яркое небо (SkyFlash) за силуэтами города — они становятся тёмным контуром;
##  - через случайную паузу (молния где-то вдали) гремит гром.

@export var light: DirectionalLight2D
@export var sky_flash: CanvasItem
@export var min_delay := 14.0
@export var max_delay := 32.0
@export var first_delay := 5.0
@export var light_energy := 1.1
@export var sky_alpha := 0.55
@export var thunder_player: AudioStreamPlayer
@export var thunder_sounds: Array[AudioStream] = []
@export var thunder_delay_min := 0.4
@export var thunder_delay_max := 2.2

## Огибающая вспышки: [время, яркость]; между точками — линейно.
const PATTERN := [
	[0.0, 0.0], [0.03, 1.0], [0.09, 0.15], [0.14, 0.75], [0.22, 0.1],
	[0.34, 0.45], [0.7, 0.0],
]

var _wait := 0.0
var _t := -1.0
var _thunder_in := -1.0


func _ready() -> void:
	_wait = first_delay
	_apply(0.0)


func _process(delta: float) -> void:
	if _thunder_in >= 0.0:
		_thunder_in -= delta
		if _thunder_in < 0.0:
			_thunder()
	if _t < 0.0:
		_wait -= delta
		if _wait <= 0.0:
			_t = 0.0
			_thunder_in = randf_range(thunder_delay_min, thunder_delay_max)
		return
	_t += delta
	var end: float = PATTERN[PATTERN.size() - 1][0]
	if _t >= end:
		_t = -1.0
		_wait = randf_range(min_delay, max_delay)
		_apply(0.0)
		return
	_apply(_envelope(_t))


func _thunder() -> void:
	if thunder_player == null or thunder_sounds.is_empty():
		return
	thunder_player.stream = thunder_sounds[randi() % thunder_sounds.size()]
	thunder_player.pitch_scale = randf_range(0.85, 1.1)
	thunder_player.play()


func _envelope(t: float) -> float:
	for i in PATTERN.size() - 1:
		var a: Array = PATTERN[i]
		var b: Array = PATTERN[i + 1]
		if t <= b[0]:
			return lerpf(a[1], b[1], (t - a[0]) / (b[0] - a[0]))
	return 0.0


func _apply(k: float) -> void:
	if light:
		light.energy = light_energy * k
		light.visible = k > 0.001
	if sky_flash:
		sky_flash.modulate.a = sky_alpha * k
