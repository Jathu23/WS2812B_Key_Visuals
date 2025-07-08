#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN 6
#define NUM_LEDS 60
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS 100
#define MAX_BRIGHTNESS 255

CRGB leds[NUM_LEDS];

// System States
enum SystemMode {
  MODE_OFF = 0,
  MODE_KEYBOARD = 1,
  MODE_AUDIO = 2,
  MODE_IDLE = 3
};

enum NotificationMode {
  NOTIF_OFF = 0,
  NOTIF_DOUBLE_BLINK = 1,
  NOTIF_CENTER_TO_ENDS = 2,
  NOTIF_STROBE = 3
};

enum KeyboardMode {
  KB_CENTER_SPREAD = 0,
  KB_RANDOM_BLINK = 1,
  KB_SINGLE_COLOR_BLINK = 2,
  KB_WAVE_EFFECT = 3,
  KB_TYPING_TRAIL = 4
};

enum AudioMode {
  AUDIO_CENTER_OUT = 0,
  AUDIO_RANDOM_COLOR = 1,
  AUDIO_SINGLE_COLOR = 2,
  AUDIO_VU_METER = 3,
  AUDIO_SPECTRUM = 4,
  AUDIO_WAVE = 5,
  AUDIO_PULSE = 6,
  AUDIO_CENTER_BARS = 7
};

enum IdleMode {
  IDLE_KNIGHT_RIDER = 0,
  IDLE_RAINBOW = 1,
  IDLE_SAND_CLOCK = 2,
  IDLE_BREATHING = 3,
  IDLE_FIRE = 4
};

// Global Variables
SystemMode currentMode = MODE_OFF;
NotificationMode notificationMode = NOTIF_DOUBLE_BLINK;
KeyboardMode keyboardMode = KB_CENTER_SPREAD;
AudioMode audioMode = AUDIO_CENTER_OUT;
IdleMode idleMode = IDLE_KNIGHT_RIDER;

bool systemEnabled = true;
bool keyboardEnabled = true;
bool audioEnabled = true;
bool idleEnabled = true;
bool notificationActive = false;

unsigned long lastActivity = 0;
unsigned long idleTimeout = 30000; // 30 seconds
unsigned long notificationStartTime = 0;
unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 20; // 50 FPS

// Keyboard animation timeout
unsigned long keyboardAnimationStart = 0;
unsigned long KEYBOARD_ANIMATION_DURATION = 1000; // 1 second animation (modifiable)

// Animation Variables
int animationStep = 0;
int knightRiderPos = 0;
int knightRiderDirection = 1;
uint8_t hueOffset = 0;
int audioLevel = 0;
int audioFreqBands[8] = {0};

// Color Palettes
CRGB getRandomColor() {
  return CRGB(random(50, 255), random(50, 255), random(50, 255));
}

CRGB getTypingColor() {
  CRGB colors[] = {CRGB::Red, CRGB::Blue, CRGB::Green, CRGB::Yellow, CRGB::Purple, CRGB::Cyan};
  return colors[random(6)];
}

void setup() {
  Serial.begin(115200);
  
  // Initialize LED strip
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
  
  // Startup animation
  startupAnimation();
  
  lastActivity = millis();
  Serial.println("Arduino LED Controller Ready");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Handle serial communication
  handleSerialInput();
  
  // Update animations at consistent framerate
  if (currentTime - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentTime;
    
    if (!systemEnabled) {
      FastLED.clear();
      FastLED.show();
      return;
    }
    
    // Check for idle mode
    if (idleEnabled && (currentTime - lastActivity > idleTimeout) && !notificationActive) {
      if (currentMode != MODE_IDLE) {
        currentMode = MODE_IDLE;
        animationStep = 0;
      }
    }
    
    // Check for keyboard animation timeout
    if (currentMode == MODE_KEYBOARD && (currentTime - keyboardAnimationStart > KEYBOARD_ANIMATION_DURATION)) {
      // Return to idle mode after keyboard animation completes
      if (idleEnabled) {
        currentMode = MODE_IDLE;
        animationStep = 0;
      } else {
        currentMode = MODE_OFF;
        FastLED.clear();
      }
    }
    
    // Handle notifications (highest priority)
    if (notificationActive) {
      handleNotification();
    } else {
      // Handle current mode
      switch (currentMode) {
        case MODE_KEYBOARD:
          handleKeyboardMode();
          break;
        case MODE_AUDIO:
          handleAudioMode();
          break;
        case MODE_IDLE:
          handleIdleMode();
          break;
        case MODE_OFF:
          FastLED.clear();
          break;
      }
    }
    
    FastLED.show();
    animationStep++;
  }
}

void handleSerialInput() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // Parse commands
    if (command.startsWith("SYSTEM:")) {
      systemEnabled = command.substring(7).toInt();
    }
    else if (command.startsWith("KEYBOARD:")) {
      if (command.substring(9) == "ON" && keyboardEnabled) {
        currentMode = MODE_KEYBOARD;
        lastActivity = millis();
        keyboardAnimationStart = millis();
        animationStep = 0;
      }
    }
    else if (command.startsWith("AUDIO:")) {
      String audioData = command.substring(6);
      if (audioEnabled) {
        parseAudioData(audioData);
        currentMode = MODE_AUDIO;
        lastActivity = millis();
      }
    }
    else if (command.startsWith("NOTIFICATION:")) {
      triggerNotification();
    }
    else if (command.startsWith("CONFIG:")) {
      handleConfiguration(command.substring(7));
    }
    else if (command.startsWith("BRIGHTNESS:")) {
      int brightness = command.substring(11).toInt();
      FastLED.setBrightness(constrain(brightness, 10, 255));
    }
  }
}

void handleConfiguration(String config) {
  if (config.startsWith("KB_MODE:")) {
    keyboardMode = (KeyboardMode)config.substring(8).toInt();
  }
  else if (config.startsWith("AUDIO_MODE:")) {
    audioMode = (AudioMode)config.substring(11).toInt();
  }
  else if (config.startsWith("IDLE_MODE:")) {
    idleMode = (IdleMode)config.substring(10).toInt();
  }
  else if (config.startsWith("NOTIF_MODE:")) {
    notificationMode = (NotificationMode)config.substring(11).toInt();
  }
  else if (config.startsWith("KB_ENABLE:")) {
    keyboardEnabled = config.substring(10).toInt();
  }
  else if (config.startsWith("AUDIO_ENABLE:")) {
    audioEnabled = config.substring(13).toInt();
  }
  else if (config.startsWith("IDLE_ENABLE:")) {
    idleEnabled = config.substring(12).toInt();
  }
  else if (config.startsWith("IDLE_TIMEOUT:")) {
    idleTimeout = config.substring(13).toInt() * 1000; // Convert to milliseconds
  }
  else if (config.startsWith("KB_DURATION:")) {
    // Update keyboard animation duration (convert from milliseconds to milliseconds)
    unsigned long newDuration = config.substring(13).toInt();
    if (newDuration >= 500 && newDuration <= 5000) { // 0.5 to 5 seconds
      KEYBOARD_ANIMATION_DURATION = newDuration;
    }
  }
}

// Keyboard Animation Modes
void handleKeyboardMode() {
  switch (keyboardMode) {
    case KB_CENTER_SPREAD:
      keyboardCenterSpread();
      break;
    case KB_RANDOM_BLINK:
      keyboardRandomBlink();
      break;
    case KB_SINGLE_COLOR_BLINK:
      keyboardSingleColorBlink();
      break;
    case KB_WAVE_EFFECT:
      keyboardWaveEffect();
      break;
    case KB_TYPING_TRAIL:
      keyboardTypingTrail();
      break;
  }
}

void keyboardCenterSpread() {
  static int spreadPos = 0;
  static CRGB spreadColor = getTypingColor();
  static unsigned long lastSpread = 0;
  
  if (millis() - lastSpread > 50) {
    fadeToBlackBy(leds, NUM_LEDS, 30);
    
    int center = NUM_LEDS / 2;
    if (spreadPos < center) {
      leds[center + spreadPos] = spreadColor;
      leds[center - spreadPos] = spreadColor;
      spreadPos++;
    } else {
      spreadPos = 0;
      spreadColor = getTypingColor();
    }
    lastSpread = millis();
  }
}

void keyboardRandomBlink() {
  static unsigned long lastBlink = 0;
  
  if (millis() - lastBlink > 100) {
    fadeToBlackBy(leds, NUM_LEDS, 50);
    
    for (int i = 0; i < 5; i++) {
      int pos = random(NUM_LEDS);
      leds[pos] = getRandomColor();
    }
    lastBlink = millis();
  }
}

void keyboardSingleColorBlink() {
  static unsigned long lastBlink = 0;
  static CRGB blinkColor = CRGB::Blue;
  
  if (millis() - lastBlink > 200) {
    if (animationStep % 2 == 0) {
      fill_solid(leds, NUM_LEDS, blinkColor);
    } else {
      FastLED.clear();
    }
    lastBlink = millis();
  }
}

void keyboardWaveEffect() {
  for (int i = 0; i < NUM_LEDS; i++) {
    int wave = sin8(i * 10 + animationStep * 5);
    leds[i] = CHSV(hueOffset + i * 2, 255, wave);
  }
  hueOffset++;
}

void keyboardTypingTrail() {
  static int trailPos = 0;
  static CRGB trailColor = getTypingColor();
  
  fadeToBlackBy(leds, NUM_LEDS, 20);
  
  leds[trailPos] = trailColor;
  trailPos = (trailPos + 1) % NUM_LEDS;
  
  if (trailPos == 0) {
    trailColor = getTypingColor();
  }
}

// Audio Visualization Modes
void handleAudioMode() {
  switch (audioMode) {
    case AUDIO_CENTER_OUT:
      audioCenterOut();
      break;
    case AUDIO_RANDOM_COLOR:
      audioRandomColor();
      break;
    case AUDIO_SINGLE_COLOR:
      audioSingleColor();
      break;
    case AUDIO_VU_METER:
      audioVUMeter();
      break;
    case AUDIO_SPECTRUM:
      audioSpectrum();
      break;
    case AUDIO_WAVE:
      audioWave();
      break;
    case AUDIO_PULSE:
      audioPulse();
      break;
    case AUDIO_CENTER_BARS:
      audioCenterBars();
      break;
  }
}

void audioCenterOut() {
  FastLED.clear();
  int center = NUM_LEDS / 2;
  
  // More responsive mapping for lower audio levels
  int spread = map(audioLevel, 0, 255, 0, center);
  if (audioLevel > 10) { // Even small audio levels get some response
    spread = max(1, spread);
  }
  
  // Dynamic color based on audio level
  uint8_t hue = map(audioLevel, 0, 255, 160, 0); // Green to Red
  CRGB color = CHSV(hue, 255, 255);
  
  for (int i = 0; i <= spread; i++) {
    if (center + i < NUM_LEDS) {
      int brightness = map(i, 0, spread, 255, 50);
      leds[center + i] = color;
      leds[center + i].nscale8(brightness);
    }
    if (center - i >= 0) {
      int brightness = map(i, 0, spread, 255, 50);
      leds[center - i] = color;
      leds[center - i].nscale8(brightness);
    }
  }
}

void audioRandomColor() {
  static unsigned long lastChange = 0;
  static CRGB baseColor = CRGB::Red;
  
  // Change base color every 500ms
  if (millis() - lastChange > 500) {
    baseColor = getRandomColor();
    lastChange = millis();
  }
  
  // More responsive threshold
  if (audioLevel > 5) { // Lowered threshold
    fadeToBlackBy(leds, NUM_LEDS, 20);
    
    // Create multiple random flashes based on audio level
    int numFlashes = map(audioLevel, 5, 255, 1, 8);
    for (int i = 0; i < numFlashes; i++) {
      int pos = random(NUM_LEDS);
      int brightness = map(audioLevel, 5, 255, 50, 255); // Lower minimum brightness
      leds[pos] = baseColor;
      leds[pos].nscale8(brightness);
    }
  } else {
    fadeToBlackBy(leds, NUM_LEDS, 10);
  }
}

void audioSingleColor() {
  // Dynamic color based on dominant frequency band
  int dominantBand = 0;
  int maxLevel = 0;
  
  for (int i = 0; i < 8; i++) {
    if (audioFreqBands[i] > maxLevel) {
      maxLevel = audioFreqBands[i];
      dominantBand = i;
    }
  }
  
  // Color mapping based on frequency bands
  uint8_t hue;
  switch (dominantBand) {
    case 0: hue = 0; break;    // Bass - Red
    case 1: hue = 32; break;   // Low Mid - Orange
    case 2: hue = 64; break;   // Mid - Yellow
    case 3: hue = 96; break;   // High Mid - Green
    case 4: hue = 128; break;  // High - Cyan
    case 5: hue = 160; break;  // Presence - Blue
    case 6: hue = 192; break;  // Brilliance - Purple
    case 7: hue = 224; break;  // Air - Pink
    default: hue = 0; break;
  }
  
  int brightness = map(audioLevel, 0, 255, 0, 255);
  fill_solid(leds, NUM_LEDS, CHSV(hue, 255, brightness));
}

void audioVUMeter() {
  FastLED.clear();
  
  // More responsive mapping for lower audio levels
  int activeLEDs = map(audioLevel, 0, 255, 0, NUM_LEDS);
  if (audioLevel > 5) { // Even small audio levels get some response
    activeLEDs = max(1, activeLEDs);
  }
  
  for (int i = 0; i < activeLEDs; i++) {
    if (i < NUM_LEDS / 3) {
      leds[i] = CRGB::Green;
    } else if (i < NUM_LEDS * 2 / 3) {
      leds[i] = CRGB::Yellow;
    } else {
      leds[i] = CRGB::Red;
    }
    
    // Add brightness variation
    int brightness = map(i, 0, activeLEDs, 255, 100);
    leds[i].nscale8(brightness);
  }
  
  // Add peak indicator - more sensitive
  if (audioLevel > 50) { // Lowered threshold
    leds[NUM_LEDS - 1] = CRGB::White;
  }
}

void audioSpectrum() {
  FastLED.clear();
  int ledsPerBand = NUM_LEDS / 8;
  
  for (int band = 0; band < 8; band++) {
    int bandHeight = map(audioFreqBands[band], 0, 255, 0, ledsPerBand);
    int startPos = band * ledsPerBand;
    
    // Color mapping for each band
    uint8_t hue;
    switch (band) {
      case 0: hue = 0; break;    // Bass - Red
      case 1: hue = 32; break;   // Low Mid - Orange
      case 2: hue = 64; break;   // Mid - Yellow
      case 3: hue = 96; break;   // High Mid - Green
      case 4: hue = 128; break;  // High - Cyan
      case 5: hue = 160; break;  // Presence - Blue
      case 6: hue = 192; break;  // Brilliance - Purple
      case 7: hue = 224; break;  // Air - Pink
      default: hue = 0; break;
    }
    
    for (int i = 0; i < bandHeight; i++) {
      if (startPos + i < NUM_LEDS) {
        int brightness = map(i, 0, ledsPerBand, 255, 100);
        leds[startPos + i] = CHSV(hue, 255, brightness);
      }
    }
  }
}

void audioWave() {
  // Create a wave effect that responds to audio
  static uint8_t waveOffset = 0;
  
  for (int i = 0; i < NUM_LEDS; i++) {
    // Create wave pattern
    uint8_t wave = sin8(i * 8 + waveOffset);
    
    // Modulate wave with audio level
    uint8_t audioModulation = map(audioLevel, 0, 255, 50, 255);
    wave = scale8(wave, audioModulation);
    
    // Color based on dominant frequency
    uint8_t hue = map(audioFreqBands[0], 0, 255, 0, 255); // Use bass for color
    
    leds[i] = CHSV(hue + i * 2, 255, wave);
  }
  
  // Speed of wave based on audio level
  uint8_t waveSpeed = map(audioLevel, 0, 255, 2, 8);
  waveOffset += waveSpeed;
}

void audioPulse() {
  // Create pulsing effect that responds to audio beats
  static unsigned long lastPulse = 0;
  static uint8_t pulseBrightness = 0;
  static bool pulseActive = false;
  
  // Detect audio peaks for pulse trigger
  if (audioLevel > 100 && !pulseActive) {
    pulseActive = true;
    pulseBrightness = 255;
    lastPulse = millis();
  }
  
  if (pulseActive) {
    // Calculate pulse decay
    unsigned long pulseAge = millis() - lastPulse;
    if (pulseAge > 200) { // 200ms pulse duration
      pulseActive = false;
      pulseBrightness = 0;
    } else {
      // Exponential decay
      pulseBrightness = 255 * exp(-pulseAge / 50.0);
    }
  }
  
  // Create pulse effect
  int center = NUM_LEDS / 2;
  int pulseWidth = map(pulseBrightness, 0, 255, 0, NUM_LEDS / 2);
  
  // Clear LEDs
  fadeToBlackBy(leds, NUM_LEDS, 30);
  
  // Draw pulse
  for (int i = 0; i < pulseWidth; i++) {
    if (center + i < NUM_LEDS) {
      uint8_t brightness = map(i, 0, pulseWidth, pulseBrightness, 0);
      leds[center + i] = CHSV(hueOffset, 255, brightness);
    }
    if (center - i >= 0) {
      uint8_t brightness = map(i, 0, pulseWidth, pulseBrightness, 0);
      leds[center - i] = CHSV(hueOffset, 255, brightness);
    }
  }
  
  // Change color over time
  hueOffset++;
}

void audioCenterBars() {
  // Enhanced center bars animation adapted for PC audio
  static float volumeLevel = 0;
  static float prevVolumeLevel = 0;
  static const float SMOOTHING_FACTOR = 0.7;
  static const int MAX_HEIGHT = NUM_LEDS / 2;
  static const int SPARKLE_CHANCE = 10;
  static const int HUE_STEP = 5;
  
  // Map audio level to bar height with smoothing
  float newVolume = map(audioLevel, 0, 255, 0, MAX_HEIGHT);
  volumeLevel = (newVolume * (1.0 - SMOOTHING_FACTOR)) + (prevVolumeLevel * SMOOTHING_FACTOR);
  prevVolumeLevel = volumeLevel;
  
  // Fade all LEDs to create smooth transitions
  fadeToBlackBy(leds, NUM_LEDS, 80);
  
  // Start at the center and expand outward
  int center = NUM_LEDS / 2;
  int ledsToLight = volumeLevel;
  
  // Set colors expanding from center with enhanced color dynamics
  for (int i = 0; i < ledsToLight; i++) {
    // Color based on distance from center and volume intensity
    byte hue = hueOffset + i * HUE_STEP;
    byte sat = 255;
    
    // Brightness varies with volume and position for more dynamic effect
    byte val = constrain(255 - (i * 2), 0, 255);
    
    // Right side
    if (center + i < NUM_LEDS) {
      leds[center + i] = CHSV(hue, sat, val);
    }
    
    // Left side with slight variance for asymmetry
    if (center - i - 1 >= 0) {
      leds[center - i - 1] = CHSV(hue + 10, sat, val);
    }
  }
  
  // Add sparkle effects on strong beats
  if (volumeLevel > prevVolumeLevel + 5 && random8() < SPARKLE_CHANCE) {
    int sparklePos = random16(NUM_LEDS);
    leds[sparklePos] = CRGB::White;
  }
  
  // Add a gradient fade at the edges of the bars
  for (int i = 0; i < ledsToLight / 2; i++) {
    // Right side gradient
    if (center + ledsToLight + i < NUM_LEDS) {
      byte fadeVal = map(i, 0, ledsToLight / 2, 255, 0);
      leds[center + ledsToLight + i] = CHSV(hueOffset + (ledsToLight + i) * HUE_STEP, 255, fadeVal);
    }
    
    // Left side gradient
    if (center - ledsToLight - i - 1 >= 0) {
      byte fadeVal = map(i, 0, ledsToLight / 2, 255, 0);
      leds[center - ledsToLight - i - 1] = CHSV(hueOffset + (ledsToLight + i) * HUE_STEP + 10, 255, fadeVal);
    }
  }
  
  // Update hue for color cycling
  hueOffset++;
}

// Idle Animation Modes
void handleIdleMode() {
  switch (idleMode) {
    case IDLE_KNIGHT_RIDER:
      idleKnightRider();
      break;
    case IDLE_RAINBOW:
      idleRainbow();
      break;
    case IDLE_SAND_CLOCK:
      idleSandClock();
      break;
    case IDLE_BREATHING:
      idleBreathing();
      break;
    case IDLE_FIRE:
      idleFire();
      break;
  }
}

void idleKnightRider() {
  static unsigned long lastMove = 0;
  
  if (millis() - lastMove > 80) {
    FastLED.clear();
    
    // Create trailing effect
    for (int i = -3; i <= 3; i++) {
      int pos = knightRiderPos + i;
      if (pos >= 0 && pos < NUM_LEDS) {
        int brightness = 255 - abs(i) * 60;
        leds[pos] = CRGB(brightness, 0, 0);
      }
    }
    
    knightRiderPos += knightRiderDirection;
    
    if (knightRiderPos >= NUM_LEDS - 1 || knightRiderPos <= 0) {
      knightRiderDirection *= -1;
    }
    
    lastMove = millis();
  }
}

void idleRainbow() {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV((hueOffset + i * 4) % 255, 255, 200);
  }
  hueOffset++;
}

void idleSandClock() {
  static int topPos = 0;
  static int bottomPos = NUM_LEDS - 1;
  static unsigned long lastDrop = 0;
  
  if (millis() - lastDrop > 100) {
    if (topPos <= bottomPos) {
      leds[topPos] = CRGB::Yellow;
      leds[bottomPos] = CRGB::Blue;
      topPos++;
      bottomPos--;
    } else {
      // Reset
      FastLED.clear();
      topPos = 0;
      bottomPos = NUM_LEDS - 1;
    }
    lastDrop = millis();
  }
}

void idleBreathing() {
  int brightness = (sin8(animationStep * 2) + 127) / 2;
  fill_solid(leds, NUM_LEDS, CHSV(160, 255, brightness));
}

void idleFire() {
  for (int i = 0; i < NUM_LEDS; i++) {
    int heat = random(0, 255);
    if (heat > 200) {
      leds[i] = CRGB::Red;
    } else if (heat > 150) {
      leds[i] = CRGB::Orange;
    } else if (heat > 100) {
      leds[i] = CRGB::Yellow;
    } else {
      leds[i] = CRGB::Black;
    }
  }
}

// Notification Animations
void triggerNotification() {
  notificationActive = true;
  notificationStartTime = millis();
  animationStep = 0;
}

void handleNotification() {
  unsigned long elapsed = millis() - notificationStartTime;
  
  switch (notificationMode) {
    case NOTIF_DOUBLE_BLINK:
      notificationDoubleBlink(elapsed);
      break;
    case NOTIF_CENTER_TO_ENDS:
      notificationCenterToEnds(elapsed);
      break;
    case NOTIF_STROBE:
      notificationStrobe(elapsed);
      break;
  }
}

void notificationDoubleBlink(unsigned long elapsed) {
  if (elapsed < 5000) { // 5 seconds total
    if ((elapsed < 200) || (elapsed >= 400 && elapsed < 600)) {
      fill_solid(leds, NUM_LEDS, CRGB::White);
    } else if (elapsed >= 1000 && elapsed < 4000) {
      // Center to ends animation
      int progress = map(elapsed - 1000, 0, 3000, 0, NUM_LEDS/2);
      FastLED.clear();
      CRGB color = getRandomColor();
      
      int center = NUM_LEDS / 2;
      for (int i = 0; i <= progress; i++) {
        if (center + i < NUM_LEDS) leds[center + i] = color;
        if (center - i >= 0) leds[center - i] = color;
      }
    } else if (elapsed >= 4000) {
      // Ends to center
      int progress = map(elapsed - 4000, 0, 1000, NUM_LEDS/2, 0);
      FastLED.clear();
      CRGB color = getRandomColor();
      
      for (int i = 0; i < progress; i++) {
        leds[i] = color;
        leds[NUM_LEDS - 1 - i] = color;
      }
    } else {
      FastLED.clear();
    }
  } else {
    notificationActive = false;
  }
}

void notificationCenterToEnds(unsigned long elapsed) {
  if (elapsed < 5000) {
    int center = NUM_LEDS / 2;
    int spread = map(elapsed, 0, 2500, 0, center);
    
    FastLED.clear();
    CRGB color = getRandomColor();
    
    for (int i = 0; i <= spread; i++) {
      if (center + i < NUM_LEDS) leds[center + i] = color;
      if (center - i >= 0) leds[center - i] = color;
    }
    
    if (elapsed > 2500) {
      // Fade out
      fadeToBlackBy(leds, NUM_LEDS, 10);
    }
  } else {
    notificationActive = false;
  }
}

void notificationStrobe(unsigned long elapsed) {
  if (elapsed < 5000) {
    if ((elapsed / 100) % 2 == 0) {
      fill_solid(leds, NUM_LEDS, CRGB::White);
    } else {
      FastLED.clear();
    }
  } else {
    notificationActive = false;
  }
}

void parseAudioData(String data) {
  // Parse audio level and frequency bands
  // Format: "LEVEL:255,BANDS:100,120,80,90,110,70,60,85"
  
  int levelIndex = data.indexOf("LEVEL:");
  int bandsIndex = data.indexOf("BANDS:");
  
  if (levelIndex != -1) {
    int commaIndex = data.indexOf(",", levelIndex);
    if (commaIndex != -1) {
      audioLevel = data.substring(levelIndex + 6, commaIndex).toInt();
    } else {
      audioLevel = data.substring(levelIndex + 6).toInt();
    }
  }
  
  if (bandsIndex != -1) {
    String bandsData = data.substring(bandsIndex + 6);
    int bandIndex = 0;
    int startPos = 0;
    
    for (int i = 0; i <= bandsData.length() && bandIndex < 8; i++) {
      if (i == bandsData.length() || bandsData.charAt(i) == ',') {
        if (i > startPos) {
          audioFreqBands[bandIndex] = bandsData.substring(startPos, i).toInt();
          bandIndex++;
        }
        startPos = i + 1;
      }
    }
  }
}

void startupAnimation() {
  // Rainbow sweep on startup
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(i * 255 / NUM_LEDS, 255, 255);
    FastLED.show();
    delay(20);
  }
  
  delay(500);
  
  // Fade out
  for (int brightness = 255; brightness >= 0; brightness -= 5) {
    FastLED.setBrightness(brightness);
    FastLED.show();
    delay(20);
  }
  
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
}