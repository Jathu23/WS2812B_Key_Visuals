#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN     6
#define NUM_LEDS    60
#define BRIGHTNESS  50
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB

CRGB leds[NUM_LEDS];

// Animation variables
unsigned long lastUpdate = 0;
unsigned long lastKeyboardActivity = 0;
int knightRiderPos = 0;
bool knightRiderDirection = true;
int pulseValue = 0;
bool pulseDirection = true;

// Notification animation variables
bool notificationActive = false;
unsigned long notificationStartTime = 0;
int notificationPhase = 0;
int blinkCount = 0;
int waveCount = 0;
uint8_t waveColor1, waveColor2;

// Enhanced key reactive effects
struct KeyEffect {
  int position;
  int maxRadius;
  int currentRadius;
  CRGB color;
  unsigned long startTime;
  bool active;
  int effectType; // 0: ripple, 1: explosion, 2: wave, 3: sparkle, 4: pulse, 5: comet, 6: firework, 7: lightning
};

#define MAX_KEY_EFFECTS 8
KeyEffect keyEffects[MAX_KEY_EFFECTS];
int nextEffectIndex = 0;

// Center-to-end ripple effect variables
struct RippleEffect {
  int centerPos;
  int currentRadius;
  int maxRadius;
  CRGB color;
  unsigned long startTime;
  bool active;
  bool expandingOut;
  int rippleType; // 0: normal, 1: double, 2: spiral
};

#define MAX_RIPPLES 5
RippleEffect ripples[MAX_RIPPLES];
int nextRippleIndex = 0;

// Custom effect variables
CRGB customColor = CRGB::Red;
int customSpeed = 50;
int customBrightness = 100;
String currentCustomEffect = "";

// Custom effect specific variables
int rainbowHue = 0;
int breathingValue = 0;
bool breathingDirection = true;
int colorWipePos = 0;
int sparkleCount = 0;
unsigned long fireUpdate = 0;
int sandClockPos = 0;
bool sandClockDirection = true;
int audioLevel = 0;

// Enhanced audio reactive variables
int audioSpectrum[8]; // 8 frequency bands
int audioHistory[32]; // Audio history for smoothing
int historyIndex = 0;

// States
enum AnimationState {
  IDLE_KNIGHT_RIDER,
  KEYBOARD_ACTIVITY,
  NOTIFICATION_ALERT,
  CUSTOM_EFFECT,
  OFF_STATE
};

AnimationState currentState = IDLE_KNIGHT_RIDER;
unsigned long stateChangeTime = 0;

// Key reactive effect types
String keyEffectTypes[] = {"ripple", "explosion", "wave", "sparkle", "pulse", "comet", "firework", "lightning"};

void setup() {
  Serial.begin(9600);
  
  // Initialize LED strip
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(BRIGHTNESS);
  
  // Clear all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  
  // Initialize key effects
  for (int i = 0; i < MAX_KEY_EFFECTS; i++) {
    keyEffects[i].active = false;
  }
  
  // Initialize ripple effects
  for (int i = 0; i < MAX_RIPPLES; i++) {
    ripples[i].active = false;
  }
  
  // Initialize audio history
  for (int i = 0; i < 32; i++) {
    audioHistory[i] = 0;
  }
  
  Serial.println("Enhanced Arduino LED Controller Ready - 60 LEDs");
}

void startNotification() {
  notificationActive = true;
  notificationStartTime = millis();
  notificationPhase = 0;
  blinkCount = 0;
  waveCount = 0;
  waveColor1 = random(0, 255);
  waveColor2 = random(0, 255);
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "KEY") {
      lastKeyboardActivity = millis();
      currentState = KEYBOARD_ACTIVITY;
      stateChangeTime = millis();
      createRandomKeyEffect();
      createCenterRippleEffect();
    }
    else if (command == "NOTIFY") {
      currentState = NOTIFICATION_ALERT;
      stateChangeTime = millis();
      startNotification();
    }
    else if (command == "IDLE") {
      currentState = IDLE_KNIGHT_RIDER;
      stateChangeTime = millis();
      notificationActive = false;
    }
    else if (command == "OFF") {
      currentState = OFF_STATE;
      stateChangeTime = millis();
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      FastLED.show();
    }
    else if (command.startsWith("CUSTOM,")) {
      parseCustomCommand(command);
    }
    else if (command.startsWith("AUDIO,")) {
      parseAudioCommand(command);
    }
    else if (command.startsWith("KEYEFFECT,")) {
      parseKeyEffectCommand(command);
    }
  }
  
  // Auto return to idle after keyboard inactivity
  if (currentState == KEYBOARD_ACTIVITY && 
      millis() - lastKeyboardActivity > 5000) {
    currentState = IDLE_KNIGHT_RIDER;
    stateChangeTime = millis();
  }
  
  // Auto return to idle after notification completes
  if (currentState == NOTIFICATION_ALERT && !notificationActive) {
    currentState = IDLE_KNIGHT_RIDER;
    stateChangeTime = millis();
  }
  
  // Update animations based on current state
  switch (currentState) {
    case IDLE_KNIGHT_RIDER:
      knightRiderAnimation();
      break;
    case KEYBOARD_ACTIVITY:
      keyboardActivityAnimation();
      break;
    case NOTIFICATION_ALERT:
      notificationAlertAnimation();
      break;
    case CUSTOM_EFFECT:
      updateCustomEffect();
      break;
    case OFF_STATE:
      // Do nothing, LEDs are off
      break;
  }
  
  if (currentState != OFF_STATE) {
    FastLED.show();
  }
  delay(20);
}

void parseAudioCommand(String command) {
  // Format: AUDIO,level1,level2,level3,level4,level5,level6,level7,level8
  command = command.substring(6); // Remove "AUDIO,"
  
  for (int i = 0; i < 8; i++) {
    int commaIndex = command.indexOf(',');
    if (commaIndex == -1) {
      audioSpectrum[i] = command.toInt();
      break;
    }
    audioSpectrum[i] = command.substring(0, commaIndex).toInt();
    command = command.substring(commaIndex + 1);
  }
  
  // Update audio history for smoothing
  audioHistory[historyIndex] = audioSpectrum[0]; // Use first band as overall level
  historyIndex = (historyIndex + 1) % 32;
  
  // Calculate smoothed audio level
  int sum = 0;
  for (int i = 0; i < 32; i++) {
    sum += audioHistory[i];
  }
  audioLevel = sum / 32;
}

void parseKeyEffectCommand(String command) {
  // Format: KEYEFFECT,type,position
  command = command.substring(10); // Remove "KEYEFFECT,"
  
  int commaIndex = command.indexOf(',');
  if (commaIndex == -1) return;
  
  String effectType = command.substring(0, commaIndex);
  int position = command.substring(commaIndex + 1).toInt();
  
  createSpecificKeyEffect(effectType, position);
}

void createSpecificKeyEffect(String effectType, int position) {
  KeyEffect* effect = &keyEffects[nextEffectIndex];
  effect->position = position;
  effect->startTime = millis();
  effect->active = true;
  
  if (effectType == "ripple") {
    effect->effectType = 0;
    effect->maxRadius = 8;
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 255), 255, 255);
  }
  else if (effectType == "explosion") {
    effect->effectType = 1;
    effect->maxRadius = 12;
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 60), 255, 255); // Orange/Red
  }
  else if (effectType == "wave") {
    effect->effectType = 2;
    effect->maxRadius = 15;
    effect->currentRadius = 0;
    effect->color = CHSV(random(180, 240), 255, 255); // Blue/Cyan
  }
  else if (effectType == "sparkle") {
    effect->effectType = 3;
    effect->maxRadius = 6;
    effect->currentRadius = 0;
    effect->color = CRGB::White;
  }
  else if (effectType == "pulse") {
    effect->effectType = 4;
    effect->maxRadius = 10;
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 255), 255, 255);
  }
  else if (effectType == "comet") {
    effect->effectType = 5;
    effect->maxRadius = 8;
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 255), 255, 255);
  }
  else if (effectType == "firework") {
    effect->effectType = 6;
    effect->maxRadius = 20;
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 255), 255, 255);
  }
  else if (effectType == "lightning") {
    effect->effectType = 7;
    effect->maxRadius = 5;
    effect->currentRadius = 0;
    effect->color = CRGB::White;
  }
  
  nextEffectIndex = (nextEffectIndex + 1) % MAX_KEY_EFFECTS;
}

void createRandomKeyEffect() {
  int effectType = random(8);
  int position = random(NUM_LEDS);
  
  String effectNames[] = {"ripple", "explosion", "wave", "sparkle", "pulse", "comet", "firework", "lightning"};
  createSpecificKeyEffect(effectNames[effectType], position);
}

void createCenterRippleEffect() {
  RippleEffect* ripple = &ripples[nextRippleIndex];
  ripple->centerPos = NUM_LEDS / 2;
  ripple->currentRadius = 0;
  ripple->maxRadius = NUM_LEDS / 2;
  ripple->color = CHSV(random(0, 255), 255, 200);
  ripple->startTime = millis();
  ripple->active = true;
  ripple->expandingOut = true;
  ripple->rippleType = random(3); // 0: normal, 1: double, 2: spiral
  
  nextRippleIndex = (nextRippleIndex + 1) % MAX_RIPPLES;
}

void parseCustomCommand(String command) {
  // Format: CUSTOM,effect,r,g,b,speed,brightness
  int commaIndex = command.indexOf(',', 7); // Skip "CUSTOM,"
  if (commaIndex == -1) return;
  
  currentCustomEffect = command.substring(7, commaIndex);
  
  // Parse color and settings
  String params = command.substring(commaIndex + 1);
  int r = params.substring(0, params.indexOf(',')).toInt();
  params = params.substring(params.indexOf(',') + 1);
  int g = params.substring(0, params.indexOf(',')).toInt();
  params = params.substring(params.indexOf(',') + 1);
  int b = params.substring(0, params.indexOf(',')).toInt();
  params = params.substring(params.indexOf(',') + 1);
  customSpeed = params.substring(0, params.indexOf(',')).toInt();
  params = params.substring(params.indexOf(',') + 1);
  customBrightness = params.toInt();
  
  customColor = CRGB(r, g, b);
  
  // Set brightness
  FastLED.setBrightness(customBrightness);
  
  // Switch to custom effect state
  currentState = CUSTOM_EFFECT;
  stateChangeTime = millis();
  
  // Initialize effect-specific variables
  initializeCustomEffect();
  
  Serial.println("Custom effect: " + currentCustomEffect);
}

void initializeCustomEffect() {
  rainbowHue = 0;
  breathingValue = 0;
  breathingDirection = true;
  colorWipePos = 0;
  sparkleCount = 0;
  sandClockPos = 0;
  sandClockDirection = true;
  audioLevel = 0;
}

void updateCustomEffect() {
  unsigned long currentTime = millis();
  int updateInterval = map(customSpeed, 1, 100, 100, 10); // Speed control
  
  if (currentTime - lastUpdate < updateInterval) {
    return;
  }
  
  if (currentCustomEffect == "solid") {
    solidColorEffect();
  }
  else if (currentCustomEffect == "rainbow") {
    rainbowEffect();
  }
  else if (currentCustomEffect == "breathing") {
    breathingEffect();
  }
  else if (currentCustomEffect == "colorwipe") {
    colorWipeEffect();
  }
  else if (currentCustomEffect == "sparkle") {
    sparkleEffect();
  }
  else if (currentCustomEffect == "fire") {
    fireEffect();
  }
  else if (currentCustomEffect == "sandclock") {
    sandClockEffect();
  }
  else if (currentCustomEffect == "audio") {
    audioReactiveEffect();
  }
  else if (currentCustomEffect == "spectrum") {
    spectrumEffect();
  }
  else if (currentCustomEffect == "wave") {
    waveEffect();
  }
  else if (currentCustomEffect == "matrix") {
    matrixEffect();
  }
  
  lastUpdate = currentTime;
}

void solidColorEffect() {
  fill_solid(leds, NUM_LEDS, customColor);
}

void rainbowEffect() {
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV((rainbowHue + i * 255 / NUM_LEDS) % 255, 255, 255);
  }
  rainbowHue = (rainbowHue + 1) % 255;
}

void breathingEffect() {
  if (breathingDirection) {
    breathingValue += 5;
    if (breathingValue >= 255) {
      breathingValue = 255;
      breathingDirection = false;
    }
  } else {
    breathingValue -= 5;
    if (breathingValue <= 0) {
      breathingValue = 0;
      breathingDirection = true;
    }
  }
  
  CRGB breathColor = customColor;
  breathColor.nscale8(breathingValue);
  fill_solid(leds, NUM_LEDS, breathColor);
}

void colorWipeEffect() {
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  
  for (int i = 0; i <= colorWipePos; i++) {
    leds[i] = customColor;
  }
  
  colorWipePos++;
  if (colorWipePos >= NUM_LEDS) {
    colorWipePos = 0;
  }
}

void sparkleEffect() {
  // Fade all LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i].nscale8(240);
  }
  
  // Add new sparkles
  for (int i = 0; i < 3; i++) {
    int pos = random(NUM_LEDS);
    leds[pos] = customColor;
  }
}

void fireEffect() {
  // Enhanced fire effect
  for (int i = 0; i < NUM_LEDS; i++) {
    int heat = random(160, 255);
    
    // Scale heat to color
    if (heat < 85) {
      leds[i] = CRGB(heat * 3, 0, 0);
    } else if (heat < 170) {
      leds[i] = CRGB(255, (heat - 85) * 3, 0);
    } else {
      leds[i] = CRGB(255, 255, (heat - 170) * 3);
    }
    
    // Add some randomness
    leds[i].nscale8(random(200, 255));
  }
}

void sandClockEffect() {
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  
  // Top half
  int topEnd = map(sandClockPos, 0, NUM_LEDS, NUM_LEDS/2, NUM_LEDS);
  for (int i = NUM_LEDS/2; i < topEnd; i++) {
    leds[i] = customColor;
  }
  
  // Bottom half
  int bottomEnd = map(sandClockPos, 0, NUM_LEDS, NUM_LEDS/2, 0);
  for (int i = bottomEnd; i < NUM_LEDS/2; i++) {
    leds[i] = customColor;
  }
  
  // Center point
  leds[NUM_LEDS/2] = CRGB::White;
  
  if (sandClockDirection) {
    sandClockPos++;
    if (sandClockPos >= NUM_LEDS) {
      sandClockDirection = false;
    }
  } else {
    sandClockPos--;
    if (sandClockPos <= 0) {
      sandClockDirection = true;
    }
  }
}

void audioReactiveEffect() {
  // Enhanced audio reactive effect
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  
  // Map audio level to number of LEDs to light up
  int numLeds = map(audioLevel, 0, 255, 0, NUM_LEDS);
  
  // Light up LEDs from center outward based on audio level
  int center = NUM_LEDS / 2;
  for (int i = 0; i < numLeds / 2; i++) {
    if (center - i >= 0) {
      leds[center - i] = CHSV(map(i, 0, NUM_LEDS/2, 0, 255), 255, 255);
    }
    if (center + i < NUM_LEDS) {
      leds[center + i] = CHSV(map(i, 0, NUM_LEDS/2, 0, 255), 255, 255);
    }
  }
}

void spectrumEffect() {
  // Spectrum analyzer effect using 8 frequency bands
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  
  int ledsPerBand = NUM_LEDS / 8;
  for (int band = 0; band < 8; band++) {
    int level = map(audioSpectrum[band], 0, 255, 0, ledsPerBand);
    int startLed = band * ledsPerBand;
    
    for (int i = 0; i < level; i++) {
      if (startLed + i < NUM_LEDS) {
        leds[startLed + i] = CHSV(band * 32, 255, 255);
      }
    }
  }
}

void waveEffect() {
  // Wave effect based on audio
  static int wavePos = 0;
  
  for (int i = 0; i < NUM_LEDS; i++) {
    int wave = sin8((i * 16) + wavePos) + cos8((i * 8) + wavePos);
    int brightness = map(wave, 0, 255, 50, 255);
    leds[i] = customColor;
    leds[i].nscale8(brightness);
  }
  
  wavePos += map(audioLevel, 0, 255, 1, 10);
}

void matrixEffect() {
  // Matrix-style effect
  static int matrixPos = 0;
  
  // Fade all LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i].nscale8(200);
  }
  
  // Add matrix drops
  for (int i = 0; i < 3; i++) {
    int pos = (matrixPos + i * 20) % NUM_LEDS;
    leds[pos] = CRGB::Green;
    
    // Trail effect
    for (int trail = 1; trail <= 3; trail++) {
      int trailPos = pos - trail;
      if (trailPos >= 0) {
        leds[trailPos] = CRGB(0, 100, 0);
      }
    }
  }
  
  matrixPos = (matrixPos + 1) % NUM_LEDS;
}

void knightRiderAnimation() {
  if (millis() - lastUpdate > 100) {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Create trailing effect
    for (int i = 0; i < 5; i++) {
      int pos = knightRiderPos - i;
      if (pos >= 0 && pos < NUM_LEDS) {
        leds[pos] = CRGB(255 - (i * 50), 0, 0);
      }
      pos = knightRiderPos + i;
      if (pos >= 0 && pos < NUM_LEDS) {
        leds[pos] = CRGB(255 - (i * 50), 0, 0);
      }
    }
    
    // Main LED
    if (knightRiderPos >= 0 && knightRiderPos < NUM_LEDS) {
      leds[knightRiderPos] = CRGB::Red;
    }
    
    // Move position
    if (knightRiderDirection) {
      knightRiderPos++;
      if (knightRiderPos >= NUM_LEDS - 1) {
        knightRiderDirection = false;
      }
    } else {
      knightRiderPos--;
      if (knightRiderPos <= 0) {
        knightRiderDirection = true;
      }
    }
    
    lastUpdate = millis();
  }
}

void keyboardActivityAnimation() {
  if (millis() - lastUpdate > 30) {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    updateKeyEffects();
    updateRippleEffects();
    lastUpdate = millis();
  }
}

void updateKeyEffects() {
  for (int i = 0; i < MAX_KEY_EFFECTS; i++) {
    if (keyEffects[i].active) {
      KeyEffect* effect = &keyEffects[i];
      unsigned long elapsed = millis() - effect->startTime;
      
      switch (effect->effectType) {
        case 0: // Ripple
          updateRippleKeyEffect(effect, elapsed);
          break;
        case 1: // Explosion
          updateExplosionKeyEffect(effect, elapsed);
          break;
        case 2: // Wave
          updateWaveKeyEffect(effect, elapsed);
          break;
        case 3: // Sparkle
          updateSparkleKeyEffect(effect, elapsed);
          break;
        case 4: // Pulse
          updatePulseKeyEffect(effect, elapsed);
          break;
        case 5: // Comet
          updateCometKeyEffect(effect, elapsed);
          break;
        case 6: // Firework
          updateFireworkKeyEffect(effect, elapsed);
          break;
        case 7: // Lightning
          updateLightningKeyEffect(effect, elapsed);
          break;
      }
      
      // Deactivate if effect is done
      if (elapsed > 1000) {
        effect->active = false;
      }
    }
  }
}

void updateRippleKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 500) {
    effect->currentRadius = map(elapsed, 0, 500, 0, effect->maxRadius);
    
    for (int r = 0; r <= effect->currentRadius; r++) {
      int brightness = map(r, 0, effect->maxRadius, 255, 50);
      
      int leftPos = effect->position - r;
      if (leftPos >= 0 && leftPos < NUM_LEDS) {
        leds[leftPos] = effect->color;
        leds[leftPos].nscale8(brightness);
      }
      
      int rightPos = effect->position + r;
      if (rightPos >= 0 && rightPos < NUM_LEDS) {
        leds[rightPos] = effect->color;
        leds[rightPos].nscale8(brightness);
      }
    }
  }
}

void updateExplosionKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 800) {
    effect->currentRadius = map(elapsed, 0, 800, 0, effect->maxRadius);
    
    for (int r = 0; r <= effect->currentRadius; r++) {
      int brightness = map(elapsed, 0, 800, 255, 100);
      
      for (int angle = 0; angle < 360; angle += 30) {
        int pos = effect->position + (r * cos(angle * PI / 180));
        if (pos >= 0 && pos < NUM_LEDS) {
          leds[pos] = effect->color;
          leds[pos].nscale8(brightness);
        }
      }
    }
  }
}

void updateWaveKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 600) {
    int wavePos = map(elapsed, 0, 600, 0, NUM_LEDS);
    
    for (int i = 0; i < NUM_LEDS; i++) {
      int dist = abs(i - wavePos);
      if (dist < 10) {
        int brightness = map(dist, 0, 10, 255, 50);
        leds[i] = effect->color;
        leds[i].nscale8(brightness);
      }
    }
  }
}

void updateSparkleKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 400) {
    for (int i = 0; i < 5; i++) {
      int pos = effect->position + random(-3, 4);
      if (pos >= 0 && pos < NUM_LEDS) {
        int brightness = map(elapsed, 0, 400, 255, 0);
        leds[pos] = effect->color;
        leds[pos].nscale8(brightness);
      }
    }
  }
}

void updatePulseKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 500) {
    int pulse = sin8(map(elapsed, 0, 500, 0, 255));
    
    for (int r = 0; r <= effect->maxRadius; r++) {
      int brightness = map(r, 0, effect->maxRadius, pulse, 50);
      
      int leftPos = effect->position - r;
      if (leftPos >= 0 && leftPos < NUM_LEDS) {
        leds[leftPos] = effect->color;
        leds[leftPos].nscale8(brightness);
      }
      
      int rightPos = effect->position + r;
      if (rightPos >= 0 && rightPos < NUM_LEDS) {
        leds[rightPos] = effect->color;
        leds[rightPos].nscale8(brightness);
      }
    }
  }
}

void updateCometKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 600) {
    int cometPos = map(elapsed, 0, 600, effect->position, effect->position + 20);
    
    for (int i = 0; i < 8; i++) {
      int pos = cometPos - i;
      if (pos >= 0 && pos < NUM_LEDS) {
        int brightness = map(i, 0, 8, 255, 50);
        leds[pos] = effect->color;
        leds[pos].nscale8(brightness);
      }
    }
  }
}

void updateFireworkKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 1000) {
    effect->currentRadius = map(elapsed, 0, 1000, 0, effect->maxRadius);
    
    for (int r = 0; r <= effect->currentRadius; r++) {
      int brightness = map(elapsed, 0, 1000, 255, 100);
      
      for (int angle = 0; angle < 360; angle += 15) {
        int pos = effect->position + (r * cos(angle * PI / 180));
        if (pos >= 0 && pos < NUM_LEDS) {
          CRGB fireworkColor = CHSV(random(0, 255), 255, 255);
          leds[pos] = fireworkColor;
          leds[pos].nscale8(brightness);
        }
      }
    }
  }
}

void updateLightningKeyEffect(KeyEffect* effect, unsigned long elapsed) {
  if (elapsed < 200) {
    // Flash effect
    if (elapsed < 50 || (elapsed > 100 && elapsed < 150)) {
      for (int r = 0; r <= effect->maxRadius; r++) {
        int leftPos = effect->position - r;
        if (leftPos >= 0 && leftPos < NUM_LEDS) {
          leds[leftPos] = effect->color;
        }
        
        int rightPos = effect->position + r;
        if (rightPos >= 0 && rightPos < NUM_LEDS) {
          leds[rightPos] = effect->color;
        }
      }
    }
  }
}

void updateRippleEffects() {
  for (int i = 0; i < MAX_RIPPLES; i++) {
    if (ripples[i].active) {
      RippleEffect* ripple = &ripples[i];
      unsigned long elapsed = millis() - ripple->startTime;
      
      if (elapsed < 800) {
        ripple->currentRadius = map(elapsed, 0, 800, 0, ripple->maxRadius);
        
        switch (ripple->rippleType) {
          case 0: // Normal ripple
            updateNormalRipple(ripple, elapsed);
            break;
          case 1: // Double ripple
            updateDoubleRipple(ripple, elapsed);
            break;
          case 2: // Spiral ripple
            updateSpiralRipple(ripple, elapsed);
            break;
        }
      } else {
        ripple->active = false;
      }
    }
  }
}

void updateNormalRipple(RippleEffect* ripple, unsigned long elapsed) {
  int brightness = map(elapsed, 0, 800, 255, 80);
  
  int rightPos = ripple->centerPos + ripple->currentRadius;
  if (rightPos < NUM_LEDS) {
    leds[rightPos] = ripple->color;
    leds[rightPos].nscale8(brightness);
    
    for (int trail = 1; trail <= 3 && (rightPos - trail) >= ripple->centerPos; trail++) {
      leds[rightPos - trail] += ripple->color;
      leds[rightPos - trail].nscale8(brightness / (trail + 1));
    }
  }
  
  int leftPos = ripple->centerPos - ripple->currentRadius;
  if (leftPos >= 0) {
    leds[leftPos] = ripple->color;
    leds[leftPos].nscale8(brightness);
    
    for (int trail = 1; trail <= 3 && (leftPos + trail) <= ripple->centerPos; trail++) {
      leds[leftPos + trail] += ripple->color;
      leds[leftPos + trail].nscale8(brightness / (trail + 1));
    }
  }
}

void updateDoubleRipple(RippleEffect* ripple, unsigned long elapsed) {
  int brightness = map(elapsed, 0, 800, 255, 80);
  
  // First ripple
  int rightPos1 = ripple->centerPos + ripple->currentRadius;
  int leftPos1 = ripple->centerPos - ripple->currentRadius;
  
  if (rightPos1 < NUM_LEDS) leds[rightPos1] = ripple->color;
  if (leftPos1 >= 0) leds[leftPos1] = ripple->color;
  
  // Second ripple (delayed)
  int secondRadius = max(0, ripple->currentRadius - 5);
  int rightPos2 = ripple->centerPos + secondRadius;
  int leftPos2 = ripple->centerPos - secondRadius;
  
  if (rightPos2 < NUM_LEDS) {
    leds[rightPos2] = ripple->color;
    leds[rightPos2].nscale8(brightness / 2);
  }
  if (leftPos2 >= 0) {
    leds[leftPos2] = ripple->color;
    leds[leftPos2].nscale8(brightness / 2);
  }
}

void updateSpiralRipple(RippleEffect* ripple, unsigned long elapsed) {
  int brightness = map(elapsed, 0, 800, 255, 80);
  
  for (int angle = 0; angle < 360; angle += 30) {
    int pos = ripple->centerPos + (ripple->currentRadius * cos(angle * PI / 180));
    if (pos >= 0 && pos < NUM_LEDS) {
      leds[pos] = ripple->color;
      leds[pos].nscale8(brightness);
    }
  }
}

void notificationAlertAnimation() {
  if (!notificationActive) return;
  
  unsigned long currentTime = millis();
  unsigned long elapsedTime = currentTime - notificationStartTime;
  
  if (notificationPhase == 0) {
    if (currentTime - lastUpdate > 100) {
      if (blinkCount < 4) {
        if (blinkCount % 2 == 0) {
          fill_solid(leds, NUM_LEDS, CRGB::White);
        } else {
          fill_solid(leds, NUM_LEDS, CRGB::Black);
        }
        blinkCount++;
        lastUpdate = currentTime;
      } else {
        notificationPhase = 1;
        notificationStartTime = currentTime;
        lastUpdate = currentTime;
        waveCount = 0;
      }
    }
  } 
  else if (notificationPhase == 1) {
    if (currentTime - lastUpdate > 15) {
      unsigned long waveElapsed = currentTime - notificationStartTime;
      
      if (waveCount < 2) {
        fill_solid(leds, NUM_LEDS, CRGB::Black);
        
        int waveOffset = (waveElapsed / 12) % (NUM_LEDS + 5);
        uint8_t currentHue = (waveCount == 0) ? waveColor1 : waveColor2;
        
        int center = NUM_LEDS / 2;
        for (int i = 0; i < NUM_LEDS; i++) {
          int distFromCenter = abs(i - center);
          int wavePos = (waveOffset - distFromCenter + NUM_LEDS) % (NUM_LEDS + 5);
          
          if (wavePos < 6) {
            int brightness = map(wavePos, 0, 5, 255, 60);
            leds[i] = CHSV(currentHue, 255, brightness);
            
            for (int trail = 1; trail <= 2; trail++) {
              int trailPos = i + (i < center ? trail : -trail);
              if (trailPos >= 0 && trailPos < NUM_LEDS) {
                leds[trailPos] += CHSV(currentHue, 255, brightness / (trail + 2));
              }
            }
          }
        }
        
        if (waveElapsed > (waveCount + 1) * 800) {
          waveCount++;
          if (waveCount >= 2) {
            notificationActive = false;
            fill_solid(leds, NUM_LEDS, CRGB::Black);
          }
        }
      }
      
      lastUpdate = currentTime;
    }
  }
} 