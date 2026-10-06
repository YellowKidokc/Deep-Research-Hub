#Requires AutoHotkey v2

SetOutputVoiceFormat(AudioOutputStreamFormatType) {
    oVoice := ComObject("SAPI.SpVoice")
    oVoice.AllowAudioOutputFormatChangesOnNextSet := 0
    oVoice.AudioOutputStream.Format.Type := AudioOutputStreamFormatType
    oVoice.AudioOutputStream := oVoice.AudioOutputStream
    oVoice.AllowAudioOutputFormatChangesOnNextSet := 1
    return oVoice
}

class SpeechHandler {
    static speaker := SetOutputVoiceFormat(39)
    static voices := SpeechHandler.speaker.GetVoices
    static settingsFile := A_ScriptDir "\settings.ini"
    static externalAudioFile := A_Temp "\bettertts_external.wav"
    static stopExternalPlayback := false

    static GetProviderList() {
        return ["Windows", "Edge", "Piper"]
    }

    static SpeakText(text, voiceIndex, volume, speed, pitch, provider := "Windows") {
        if (provider = "Edge")
            return this.SpeakWithEdge(text, speed)
        if (provider = "Piper")
            return this.SpeakWithPiper(text)
        return this.SpeakWithWindows(text, voiceIndex, volume, speed, pitch)
    }

    static SpeakWithWindows(text, voiceIndex, volume, speed, pitch) {
        this.speaker.Voice := this.voices.Item(voiceIndex)
        this.speaker.Volume := volume
        this.speaker.Rate := (speed/10 - 5)
        pitchValue := pitch - 5
        textWithPitch := '<pitch middle="' pitchValue '">' text '</pitch>'
        this.speaker.Speak(textWithPitch, 9)
    }

    static SpeakWithEdge(text, speed) {
        edgeVoice := IniRead(this.settingsFile, "TTS", "EdgeVoice", "en-US-GuyNeural")
        rate := this.SpeedToPercent(speed)
        chunks := this.SplitText(text, 3500)
        this.stopExternalPlayback := false
        for index, chunk in chunks {
            if (this.stopExternalPlayback)
                break
            inputFile := A_Temp "\bettertts_edge_input_" index ".txt"
            outputFile := A_Temp "\bettertts_edge_" index ".mp3"
            this.WriteTempText(inputFile, chunk)
            this.DeleteIfExists(outputFile)
            psFile := A_Temp "\bettertts_edge_" index ".ps1"
            this.WriteTempText(psFile, "$text = Get-Content -LiteralPath '" this.PSEscape(inputFile) "' -Raw`n"
                . "edge-tts --voice '" this.PSEscape(edgeVoice) "' --rate='" rate "' --text $text --write-media '" this.PSEscape(outputFile) "'`n")
            cmd := 'powershell -NoProfile -ExecutionPolicy Bypass -File "' psFile '"'
            RunWait(cmd, , "Hide")
            if (!FileExist(outputFile))
                throw Error("Edge TTS did not create audio for chunk " index ". Make sure edge-tts is installed and working.")
            this.externalAudioFile := outputFile
            SoundPlay(outputFile, "Wait")
        }
    }

    static SpeakWithPiper(text) {
        piperExe := IniRead(this.settingsFile, "TTS", "PiperExe", "piper.exe")
        piperModel := IniRead(this.settingsFile, "TTS", "PiperModel", A_ScriptDir "\voices\en_US-lessac-medium.onnx")
        inputFile := A_Temp "\bettertts_piper_input.txt"
        outputFile := A_Temp "\bettertts_piper.wav"
        if (!FileExist(piperModel))
            throw Error("Piper voice model not found: " piperModel)
        this.WriteTempText(inputFile, text)
        this.DeleteIfExists(outputFile)
        psFile := A_Temp "\bettertts_piper.ps1"
        this.WriteTempText(psFile, "Get-Content -LiteralPath '" this.PSEscape(inputFile) "' -Raw | & '" this.PSEscape(piperExe) "' --model '" this.PSEscape(piperModel) "' --output_file '" this.PSEscape(outputFile) "'`n")
        cmd := 'powershell -NoProfile -ExecutionPolicy Bypass -File "' psFile '"'
        RunWait(cmd, , "Hide")
        if (!FileExist(outputFile))
            throw Error("Piper did not create an audio file. Make sure piper.exe is installed or set PiperExe in settings.ini.")
        this.externalAudioFile := outputFile
        SoundPlay(outputFile)
    }

    static StopSpeaking() {
        this.stopExternalPlayback := true
        this.speaker.Speak("", 3)
        SoundPlay("")
    }

    static PauseSpeech() {
        static isPaused := false
        if (!isPaused) {
            this.speaker.Pause()
            isPaused := true
        } else {
            this.speaker.Resume()
            isPaused := false
        }
    }

    static WriteTempText(filePath, text) {
        this.DeleteIfExists(filePath)
        FileAppend(text, filePath, "UTF-8")
    }

    static DeleteIfExists(filePath) {
        if (FileExist(filePath))
            FileDelete(filePath)
    }

    static PSEscape(value) {
        return StrReplace(value, "'", "''")
    }

    static SpeedToPercent(speed) {
        percent := Round((speed - 50) * 2)
        if (percent > 0)
            return "+" percent "%"
        return percent "%"
    }

    static SplitText(text, maxChars := 3500) {
        chunks := []
        normalized := RegExReplace(text, "\R{3,}", "`n`n")
        paragraphs := StrSplit(normalized, "`n`n")
        current := ""
        for paragraph in paragraphs {
            paragraph := Trim(paragraph)
            if (paragraph = "")
                continue
            if (StrLen(paragraph) > maxChars) {
                if (current != "") {
                    chunks.Push(current)
                    current := ""
                }
                for sentence in this.SplitLongText(paragraph, maxChars)
                    chunks.Push(sentence)
                continue
            }
            if (current = "") {
                current := paragraph
            } else if (StrLen(current) + StrLen(paragraph) + 2 <= maxChars) {
                current .= "`n`n" paragraph
            } else {
                chunks.Push(current)
                current := paragraph
            }
        }
        if (current != "")
            chunks.Push(current)
        if (chunks.Length = 0)
            chunks.Push(text)
        return chunks
    }

    static SplitLongText(text, maxChars) {
        chunks := []
        sentences := RegExReplace(text, "([.!?;:])\s+", "$1`n")
        current := ""
        for sentence in StrSplit(sentences, "`n") {
            sentence := Trim(sentence)
            if (sentence = "")
                continue
            while (StrLen(sentence) > maxChars) {
                chunks.Push(SubStr(sentence, 1, maxChars))
                sentence := Trim(SubStr(sentence, maxChars + 1))
            }
            if (current = "") {
                current := sentence
            } else if (StrLen(current) + StrLen(sentence) + 1 <= maxChars) {
                current .= " " sentence
            } else {
                chunks.Push(current)
                current := sentence
            }
        }
        if (current != "")
            chunks.Push(current)
        return chunks
    }

    static GetVoiceList() {
        voiceList := []
        Loop this.voices.Count {
            try {
                current_voice := this.voices.Item(A_Index-1)
                lang := current_voice.GetAttribute("Language")
                description := current_voice.GetDescription()
                voiceList.Push(description . " [" . lang . "]")
            } catch {
                voiceList.Push(current_voice.GetDescription())
            }
        }
        return voiceList
    }
}
