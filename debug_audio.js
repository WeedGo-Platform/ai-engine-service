// Override Audio constructor to debug
const OriginalAudio = window.Audio;
let audioCount = 0;

window.Audio = function(src) {
    audioCount++;
    const audioId = audioCount;
    console.log(`[Audio ${audioId}] Created with src:`, src?.substring(0, 50) + '...');
    
    const audio = new OriginalAudio(src);
    
    // Track all events
    const events = ['play', 'pause', 'ended', 'error', 'loadstart', 'canplay'];
    events.forEach(event => {
        audio.addEventListener(event, (e) => {
            console.log(`[Audio ${audioId}] Event: ${event}`, {
                loop: audio.loop,
                currentTime: audio.currentTime,
                duration: audio.duration
            });
        });
    });
    
    // Override loop property
    Object.defineProperty(audio, 'loop', {
        get() {
            return this._loop || false;
        },
        set(value) {
            console.log(`[Audio ${audioId}] Setting loop to:`, value);
            this._loop = value;
        }
    });
    
    return audio;
};

console.log('Audio debugging enabled');
