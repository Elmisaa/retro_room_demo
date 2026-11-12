extends CPUParticles2D
## Пыль в воздухе: медленно «гуляющая» гравитация закручивает частицы,
## поэтому движение не выглядит прямолинейным.

@export var drift_strength := 6.0   ## Насколько сильно пыль сносит из стороны в сторону
@export var drift_speed := 0.25     ## Как быстро меняется направление сноса
@export var rise := -1.5            ## Лёгкий подъём вверх (тёплый воздух)

var _t := 0.0
var _phase := 0.0


func _ready() -> void:
	_phase = randf() * TAU


func _process(delta: float) -> void:
	_t += delta * drift_speed
	gravity = Vector2(
		sin(_t + _phase) * drift_strength + sin(_t * 2.7) * drift_strength * 0.4,
		cos(_t * 0.8 + _phase) * drift_strength * 0.6 + rise
	)
