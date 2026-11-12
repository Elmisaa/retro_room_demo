extends PointLight2D
## Живой свет: лёгкое «дыхание» яркости и редкие короткие провалы,
## как у старой лампы или люминесцентного светильника.

@export var flicker := 0.06        ## Амплитуда плавного колебания яркости (доля от базовой)
@export var flicker_speed := 1.0   ## Скорость колебания
@export var blink_chance := 0.0    ## Сколько раз в секунду в среднем свет «моргает»

var _base := 1.0
var _t := 0.0
var _blink := 0.0


func _ready() -> void:
	_base = energy
	_t = randf() * 100.0


func _process(delta: float) -> void:
	_t += delta * flicker_speed
	var wave := (sin(_t * 2.3) + sin(_t * 5.1 + 1.7) * 0.5) / 1.5
	var e := _base * (1.0 + wave * flicker)

	if _blink > 0.0:
		_blink -= delta
		e *= 0.45
	elif blink_chance > 0.0 and randf() < blink_chance * delta:
		_blink = randf_range(0.04, 0.12)

	energy = e
