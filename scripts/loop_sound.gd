extends AudioStreamPlayer
## Фоновый звук, зацикленный по всей длине файла (например, дождь).
## WAV-файл не обязан быть помечен как петля при импорте.


func _ready() -> void:
	stream = SoundUtil.looped(stream)
	play()
