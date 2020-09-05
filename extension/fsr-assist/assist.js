class Recorder {
    // Speech API
    speechAPI = "https://speech.googleapis.com/v1/speech:recognize?key=AIzaSyBK-_TTjhxiWNc7LEAb4K9whgUn2bnbGRQ"
    salesAssistAPI = "https://receiver-ehbc3cwvsq-ue.a.run.app"

    // Audio Context for audio processing
    audioContext = new(window.AudioContext || window.webkitAudioContext)()

    
    constructor(audioSrc, options, speaker, meetingID) {
        this.meetingID = meetingID
        this.speaker = speaker
        this.audioSrc = audioSrc
        this.options = options
        this.mediaRecorder = new MediaRecorder(this.audioSrc, this.options);

        this.mediaRecorder.ondataavailable = e => {
            let start = this.start
            let end = this.end
            const blobDataInWebaFormat = e.data; // .weba = webaudio; subset of webm
            blobDataInWebaFormat.arrayBuffer().then(arrayBuffer => {
                this.audioContext.decodeAudioData(arrayBuffer, buffer => {
                    var wav = Recorder.audioBufferToWav(buffer)

                    var blob = new window.Blob([new DataView(wav)], {
                        type: 'audio/wav'
                    })
                    this.callSpeechAPI(blob, start, end)
                    
                }, function () {
                    throw new Error('Could not decode audio data.')
                })
            })
        }
    }
    static blobToBase64(blob) {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        return new Promise(resolve => {
            reader.onloadend = () => {
                resolve(reader.result);
            };
        });
    };

    static audioBufferToWav(buffer, opt) {
        opt = opt || {}


        var numChannels = buffer.numberOfChannels
        var sampleRate = buffer.sampleRate
        var format = opt.float32 ? 3 : 1
        var bitDepth = format === 3 ? 32 : 16

        var result
        if (numChannels === 2) {
            result = Recorder.interleave(buffer.getChannelData(0), buffer.getChannelData(1))
        } else {
            result = buffer.getChannelData(0)
        }

        return Recorder.encodeWAV(result, format, sampleRate, numChannels, bitDepth)
    }

    static encodeWAV(samples, format, sampleRate, numChannels, bitDepth) {
        var bytesPerSample = bitDepth / 8
        var blockAlign = numChannels * bytesPerSample
        var buffer = new ArrayBuffer(44 + samples.length * bytesPerSample)
        var view = new DataView(buffer)


        /* RIFF identifier */
        Recorder.writeString(view, 0, 'RIFF')
        /* RIFF chunk length */
        view.setUint32(4, 36 + samples.length * bytesPerSample, true)
        /* RIFF type */
        Recorder.writeString(view, 8, 'WAVE')
        /* format chunk identifier */
        Recorder.writeString(view, 12, 'fmt ')
        /* format chunk length */
        view.setUint32(16, 16, true)
        /* sample format (raw) */
        view.setUint16(20, format, true)
        /* channel count */
        view.setUint16(22, numChannels, true)
        /* sample rate */
        view.setUint32(24, sampleRate, true)
        /* byte rate (sample rate * block align) */
        view.setUint32(28, sampleRate * blockAlign, true)
        /* block align (channel count * bytes per sample) */
        view.setUint16(32, blockAlign, true)
        /* bits per sample */
        view.setUint16(34, bitDepth, true)
        /* data chunk identifier */
        Recorder.writeString(view, 36, 'data')
        /* data chunk length */
        view.setUint32(40, samples.length * bytesPerSample, true)


        if (format === 1) { // Raw PCM
            Recorder.floatTo16BitPCM(view, 44, samples)
        } else {
            Recorder.writeFloat32(view, 44, samples)
        }

        return buffer
    }

    static interleave(inputL, inputR) {
        var length = inputL.length + inputR.length
        var result = new Float32Array(length)

        var index = 0
        var inputIndex = 0

        while (index < length) {
            result[index++] = inputL[inputIndex]
            result[index++] = inputR[inputIndex]
            inputIndex++
        }
        return result
    }

    static writeFloat32(output, offset, input) {
        for (var i = 0; i < input.length; i++, offset += 4) {
            output.setFloat32(offset, input[i], true)
        }
    }

    static floatTo16BitPCM(output, offset, input) {
        for (var i = 0; i < input.length; i++, offset += 2) {
            var s = Math.max(-1, Math.min(1, input[i]))
            output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
        }
    }

    static writeString(view, offset, string) {
        for (var i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i))
        }
    }

    restart() {
        this.recorderStop()
        this.recorderStart()

    }

    start() {
        this.recorderStart()
        this.intervalID = setInterval(this.restart.bind(this), 10000);
    }

    recorderStart() {
        if (this.mediaRecorder.state == "inactive") {
            this.recordStart = new Date().toISOString().replace("Z","")
            this.mediaRecorder.start();
        }
    }

    recorderStop() {
        if (this.mediaRecorder.state != "inactive") {
            this.start = this.recorderStart
            this.end = new Date().toISOString().replace("Z","")
            this.mediaRecorder.stop();
        }
    }

    stop() {
        clearInterval(this.intervalID)
        this.mediaRecorder.stop()
    }

    callSpeechAPI(blob, start, end) {
        let xmlhttp = new XMLHttpRequest();
        let self = this
        xmlhttp.open("POST", this.speechAPI);
        xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xmlhttp.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                self.callSalesAssistAPI(this.responseText, start, end);

            } else if (this.readyState == 4) {
                console.log(this.responseText);
            }
        };
        Recorder.blobToBase64(blob).then(res => {
            console.log(res)
            xmlhttp.send(JSON.stringify({
                "config": {
                    "sampleRateHertz": 48000,
                    "encoding": "LINEAR16",
                    "languageCode": "pt-BR",
                    "enableAutomaticPunctuation": false,
                    "speechContexts": [{
                        "phrases": [
                            "ai platform"
                        ]
                    }]
                },
                "audio": {
                    "content": res.split(",")[1]
                }
        }));});

    }

    callSalesAssistAPI(responseText, start, end) {
        var responseObj = JSON.parse(responseText);
        if (responseObj.results) {
            let xmlhttp = new XMLHttpRequest();
            xmlhttp.open("POST", this.salesAssistAPI);
            xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xmlhttp.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    console.log(this.responseText);

                } else if (this.readyState == 4) {
                    console.log(this.responseText);
                }
            };
            xmlhttp.send(JSON.stringify({
                "meetingID":this.meetingID,
                "speaker": this.speaker,
                "transcript": responseObj.results[0].alternatives[0].transcript, 
                "start": start, 
                "end": end
            }));
        }
        
    }

}

class UserRecorder extends Recorder {
    constructor(muteNode, ...args){
        super(...args);
        this.muteNode = muteNode;
    }

    restart() {
        this.recorderStop()

        if ((this.muteNode != null && this.muteNode.getAttribute("data-is-muted")=='false') || this.muteNode == null) {
            this.recorderStart()
        }

    }

    start(){
        if ((this.muteNode != null && this.muteNode.getAttribute("data-is-muted")=='false') || this.muteNode == null) {
            this.recorderStart()
        }
        this.intervalID = setInterval(this.restart.bind(this), 10000);
    }
}

class Assist {
    options = {
        //audioBitsPerSecond : 128000,
        //videoBitsPerSecond : 2500000,
        mimeType: 'audio/webm;codecs=opus'
    }

    constructor(options) {
        if (options) {
            this.options = options
        }
        this.waitForAudioStream();
    }

    static async getMedia(constraints) {
        let stream = null;

        try {
            stream = await navigator.mediaDevices.getUserMedia(constraints)
            /* use the stream */
        } catch (err) {
            /* handle the error */
            console.log(err)
            return null
        }

        return stream
    }

    static __delay__(timer) {
        return new Promise(resolve => {
            timer = timer || 2000;
            setTimeout(function () {
                resolve();
            }, timer);
        });
    };
    async waitForAudioStream() {
        while (true) {
            let audioCustomer = document.getElementsByTagName('audio')[0];
            let userMute = document.querySelector("div.I5fjHe.wb61gb")
            let meetingID = window.location.pathname.toString().match(/[\w]+-[\w]+-[\w]+/)[0]
            if (audioCustomer && userMute) {
                this.customerRecorder = new Recorder(document.getElementsByTagName('audio')[0].srcObject, this.options, "GOOGLER", meetingID);
                this.userStream = await Assist.getMedia({
                    audio: true
                });
                this.userRecorder = new UserRecorder(userMute.parentNode, this.userStream, this.options, "CUSTOMER", meetingID);

                this.customerRecorder.start();
                this.userRecorder.start();
                return "ok"
            };
            await Assist.__delay__(1000); // prevents app from hanging
        }
    }
}

var assist = new Assist();