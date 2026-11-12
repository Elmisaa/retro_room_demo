class_name SoundUtil
## Помощники для звука.


## Копия WAV-звука, зацикленная по всей длине (для дождя, мотора и т.п.).
static func looped(s: AudioStream) -> AudioStream:
	if s is AudioStreamWAV:
		var w := (s as AudioStreamWAV).duplicate() as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = int(w.get_length() * w.mix_rate)
		return w
	return s
