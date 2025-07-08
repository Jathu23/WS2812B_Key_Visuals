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
bool keyboardReactiveEnabled = true;

// Idle animation variables
enum IdleAnimationMode {
  IDLE_KNIGHT_RIDER,
  IDLE_PULSE_WAVE,
  IDLE_RAINBOW_FLOW,
  IDLE_SPARKLE_DRIFT,
  IDLE_FIRE_GLOW,
  IDLE_OCEAN_WAVE
};

IdleAnimationMode currentIdleAnimation = IDLE_KNIGHT_RIDER;
bool idleAnimationEnabled = true;

// Knight Rider variables
int knightRiderPos = 0;
bool knightRiderDirection = true;
int knightRiderSpeed = 100;
int knightRiderLength = 6;  // Only 6 LEDs
CRGB knightRiderColor = CRGB::Red;  // Current color

// Pulse Wave variables
int pulseWaveHue = 0;
int pulseWaveBrightness = 0;
bool pulseWaveDirection = true;

// Rainbow Flow variables
int rainbowFlowHue = 0;

// Sparkle Drift variables
int sparklePositions[10];
CRGB sparkleColors[10];
int activeSparkles = 0;

// Fire Glow variables
int fireHeat[NUM_LEDS];
int fireCooling = 55;
int fireSparking = 120;

// Ocean Wave variables
int oceanWavePos = 0;
int oceanWaveHue = 160;

// Keyboard effects variables
struct KeyEffect {
  int position;
  int maxRadius;
  int currentRadius;
  CRGB color;
  unsigned long startTime;
  bool active;
};

#define MAX_KEY_EFFECTS 5
KeyEffect keyEffects[MAX_KEY_EFFECTS];
int nextEffectIndex = 0;

// Animation modes for keyboard reactive
enum KeyAnimationMode {
  KEY_RIPPLE_WAVES,
  KEY_RANDOM_BURSTS,
  KEY_RAINBOW_WAVES,
  KEY_PULSE_FROM_CENTER,
  KEY_LIGHTNING_FLASH,
  KEY_FIRE_BURST,
  KEY_SPARKLE_RAIN,
  KEY_COLOR_CHASE
};

KeyAnimationMode currentKeyAnimation = KEY_RIPPLE_WAVES;

// Ripple effect variables
struct RippleEffect {
  int centerPos;
  int currentRadius;
  int maxRadius;
  CRGB color;
  unsigned long startTime;
  bool active;
};

#define MAX_RIPPLES 3
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
int sandClockPos = 0;
bool sandClockDirection = true;
int audioLevel = 0;

// States
enum AnimationState {
  IDLE_STATE,
  KEYBOARD_ACTIVITY,
  CUSTOM_EFFECT,
  OFF_STATE
};

AnimationState currentState = IDLE_STATE;
unsigned long stateChangeTime = 0;

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
  
  // Initialize fire heat array
  for (int i = 0; i < NUM_LEDS; i++) {
    fireHeat[i] = random(160, 255);
  }
  
  // Initialize sparkle positions
  for (int i = 0; i < 10; i++) {
    sparklePositions[i] = random(NUM_LEDS);
    sparkleColors[i] = CHSV(random(0, 255), 255, 255);
  }
  
  Serial.println("Enhanced Arduino LED Controller Ready - 60 LEDs");
  Serial.println("Commands: KEY, NOTIFY, IDLE_ANIM_X, IDLE_OFF, OFF, ANIMATION_X, CUSTOM_X");
}

void loop() {
  // Check for serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "KEY") {
      if (keyboardReactiveEnabled) {
        lastKeyboardActivity = millis();
        currentState = KEYBOARD_ACTIVITY;
        stateChangeTime = millis();
        triggerKeyboardAnimation();
      }
    }
    else if (command == "NOTIFY") {
      // Notification effect - create a bright flash
      notificationEffect();
    }
    else if (command.startsWith("IDLE_ANIM,")) {
      String animName = command.substring(10);
      setIdleAnimation(animName);
      currentState = IDLE_STATE;
      stateChangeTime = millis();
    }
    else if (command == "IDLE_OFF") {
      idleAnimationEnabled = false;
      currentState = OFF_STATE;
      stateChangeTime = millis();
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      FastLED.show();
    }
    else if (command == "OFF") {
      currentState = OFF_STATE;
      stateChangeTime = millis();
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      FastLED.show();
    }
    else if (command == "KEYMODE_ON") {
      keyboardReactiveEnabled = true;
      Serial.println("Keyboard reactive mode: ON");
    }
    else if (command == "KEYMODE_OFF") {
      keyboardReactiveEnabled = false;
      Serial.println("Keyboard reactive mode: OFF");
    }
    else if (command.startsWith("ANIMATION_")) {
      int animationIndex = command.substring(10).toInt();
      setKeyboardAnimation(animationIndex);
    }
    else if (command.startsWith("KNIGHT_SPEED_")) {
      knightRiderSpeed = command.substring(13).toInt();
      Serial.println("Knight Rider speed set to: " + String(knightRiderSpeed));
    }
    else if (command.startsWith("KNIGHT_TRAIL_")) {
      knightRiderLength = command.substring(13).toInt();
      Serial.println("Knight Rider trail length set to: " + String(knightRiderLength));
    }
    else if (command.startsWith("CUSTOM,")) {
      parseCustomCommand(command);
    }
    else if (command.startsWith("AUDIO,")) {
      audioLevel = command.substring(6).toInt();
    }
  }
  
  // Auto return to idle after keyboard inactivity
  if (currentState == KEYBOARD_ACTIVITY && 
      millis() - lastKeyboardActivity > 3000) {
    currentState = IDLE_STATE;
    stateChangeTime = millis();
  }
  
  // Update animations based on current state
  switch (currentState) {
    case IDLE_STATE:
      if (idleAnimationEnabled) {
        updateIdleAnimation();
      }
      break;
    case KEYBOARD_ACTIVITY:
      keyboardActivityAnimation();
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

void setIdleAnimation(String animName) {
  idleAnimationEnabled = true;
  
  if (animName == "knight_rider") {
    currentIdleAnimation = IDLE_KNIGHT_RIDER;
  }
  else if (animName == "pulse_wave") {
    currentIdleAnimation = IDLE_PULSE_WAVE;
  }
  else if (animName == "rainbow_flow") {
    currentIdleAnimation = IDLE_RAINBOW_FLOW;
  }
  else if (animName == "sparkle_drift") {
    currentIdleAnimation = IDLE_SPARKLE_DRIFT;
  }
  else if (animName == "fire_glow") {
    currentIdleAnimation = IDLE_FIRE_GLOW;
  }
  else if (animName == "ocean_wave") {
    currentIdleAnimation = IDLE_OCEAN_WAVE;
  }
  
  Serial.println("Idle animation set to: " + animName);
}

void updateIdleAnimation() {
  switch (currentIdleAnimation) {
    case IDLE_KNIGHT_RIDER:
      knightRiderAnimation();
      break;
    case IDLE_PULSE_WAVE:
      pulseWaveAnimation();
      break;
    case IDLE_RAINBOW_FLOW:
      rainbowFlowAnimation();
      break;
    case IDLE_SPARKLE_DRIFT:
      sparkleDriftAnimation();
      break;
    case IDLE_FIRE_GLOW:
      fireGlowAnimation();
      break;
    case IDLE_OCEAN_WAVE:
      oceanWaveAnimation();
      break;
  }
}

void pulseWaveAnimation() {
  if (millis() - lastUpdate > 50) {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Create pulsing wave effect
    for (int i = 0; i < NUM_LEDS; i++) {
      int wavePos = (i + pulseWaveHue) % NUM_LEDS;
      int brightness = sin8(wavePos * 4 + pulseWaveBrightness);
      leds[i] = CHSV(pulseWaveHue, 255, brightness);
    }
    
    pulseWaveHue = (pulseWaveHue + 1) % 255;
    
    if (pulseWaveDirection) {
      pulseWaveBrightness += 3;
      if (pulseWaveBrightness >= 255) {
        pulseWaveBrightness = 255;
        pulseWaveDirection = false;
      }
    } else {
      pulseWaveBrightness -= 3;
      if (pulseWaveBrightness <= 0) {
        pulseWaveBrightness = 0;
        pulseWaveDirection = true;
      }
    }
    
    lastUpdate = millis();
  }
}

void rainbowFlowAnimation() {
  if (millis() - lastUpdate > 30) {
    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CHSV((rainbowFlowHue + i * 4) % 255, 255, 255);
    }
    rainbowFlowHue = (rainbowFlowHue + 2) % 255;
    lastUpdate = millis();
  }
}

void sparkleDriftAnimation() {
  if (millis() - lastUpdate > 100) {
    // Fade all LEDs
    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i].nscale8(240);
    }
    
    // Add new sparkles
    if (random(0, 100) < 30) {
      int pos = random(NUM_LEDS);
      leds[pos] = CHSV(random(0, 255), 255, 255);
    }
    
    // Move existing sparkles
    for (int i = 0; i < 10; i++) {
      if (random(0, 100) < 20) {
        sparklePositions[i] = (sparklePositions[i] + 1) % NUM_LEDS;
        sparkleColors[i] = CHSV(random(0, 255), 255, 255);
        leds[sparklePositions[i]] = sparkleColors[i];
      }
    }
    
    lastUpdate = millis();
  }
}

void fireGlowAnimation() {
  if (millis() - lastUpdate > 50) {
    // Random walk for fire effect
    for (int i = 0; i < NUM_LEDS; i++) {
      fireHeat[i] = qsub8(fireHeat[i], random(0, fireCooling));
      if (random(0, 255) < fireSparking) {
        fireHeat[i] = qadd8(fireHeat[i], random(160, 255));
      }
    }
    
    // Map heat to LED colors
    for (int i = 0; i < NUM_LEDS; i++) {
      CRGB color = HeatColor(fireHeat[i]);
      leds[i] = color;
    }
    
    lastUpdate = millis();
  }
}

void oceanWaveAnimation() {
  if (millis() - lastUpdate > 80) {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Create ocean wave effect
    for (int i = 0; i < NUM_LEDS; i++) {
      int waveHeight = sin8((i + oceanWavePos) * 4) / 4;
      int brightness = map(waveHeight, 0, 63, 50, 255);
      leds[i] = CHSV(oceanWaveHue, 255, brightness);
    }
    
    oceanWavePos = (oceanWavePos + 2) % 255;
    oceanWaveHue = (oceanWaveHue + 1) % 255;
    
    lastUpdate = millis();
  }
}

void notificationEffect() {
  // Bright white flash
  fill_solid(leds, NUM_LEDS, CRGB::White);
  FastLED.show();
  delay(100);
  
  // Fade to black
  for (int i = 255; i >= 0; i -= 5) {
    FastLED.setBrightness(i);
    FastLED.show();
    delay(10);
  }
  
  // Restore brightness
  FastLED.setBrightness(BRIGHTNESS);
  
  // Create ripple effect
  createRippleWaves();
}

void setKeyboardAnimation(int animationIndex) {
  if (animationIndex >= 0 && animationIndex <= 7) {
    currentKeyAnimation = (KeyAnimationMode)animationIndex;
    Serial.println("Keyboard animation mode set to: " + String(animationIndex));
  }
}

void triggerKeyboardAnimation() {
  switch (currentKeyAnimation) {
    case KEY_RIPPLE_WAVES:
      createRippleWaves();
      break;
    case KEY_RANDOM_BURSTS:
      createRandomBursts();
      break;
    case KEY_RAINBOW_WAVES:
      createRainbowWaves();
      break;
    case KEY_PULSE_FROM_CENTER:
      createPulseFromCenter();
      break;
    case KEY_LIGHTNING_FLASH:
      createLightningFlash();
      break;
    case KEY_FIRE_BURST:
      createFireBurst();
      break;
    case KEY_SPARKLE_RAIN:
      createSparkleRain();
      break;
    case KEY_COLOR_CHASE:
      createColorChase();
      break;
  }
}

void createRippleWaves() {
  RippleEffect* ripple = &ripples[nextRippleIndex];
  ripple->centerPos = NUM_LEDS / 2;
  ripple->currentRadius = 0;
  ripple->maxRadius = NUM_LEDS / 2;
  ripple->color = CHSV(random(0, 255), 255, 200);
  ripple->startTime = millis();
  ripple->active = true;
  
  nextRippleIndex = (nextRippleIndex + 1) % MAX_RIPPLES;
}

void createRandomBursts() {
  for (int i = 0; i < 3; i++) {
    KeyEffect* effect = &keyEffects[nextEffectIndex];
    effect->position = random(0, NUM_LEDS);
    effect->maxRadius = random(5, 12);
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 255), 255, 255);
    effect->startTime = millis();
    effect->active = true;
    
    nextEffectIndex = (nextEffectIndex + 1) % MAX_KEY_EFFECTS;
  }
}

void createRainbowWaves() {
  RippleEffect* ripple = &ripples[nextRippleIndex];
  ripple->centerPos = NUM_LEDS / 2;
  ripple->currentRadius = 0;
  ripple->maxRadius = NUM_LEDS / 2;
  ripple->color = CHSV(rainbowHue, 255, 255);
  ripple->startTime = millis();
  ripple->active = true;
  
  rainbowHue = (rainbowHue + 30) % 255;
  nextRippleIndex = (nextRippleIndex + 1) % MAX_RIPPLES;
}

void createPulseFromCenter() {
  KeyEffect* effect = &keyEffects[nextEffectIndex];
  effect->position = NUM_LEDS / 2;
  effect->maxRadius = NUM_LEDS / 2;
  effect->currentRadius = 0;
  effect->color = CHSV(random(180, 255), 255, 255); // Cool colors
  effect->startTime = millis();
  effect->active = true;
  
  nextEffectIndex = (nextEffectIndex + 1) % MAX_KEY_EFFECTS;
}

void createLightningFlash() {
  // Brief white flash across all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::White);
  FastLED.show();
  delay(50);
  
  // Then create random sparks
  for (int i = 0; i < 5; i++) {
    KeyEffect* effect = &keyEffects[nextEffectIndex];
    effect->position = random(0, NUM_LEDS);
    effect->maxRadius = random(2, 6);
    effect->currentRadius = 0;
    effect->color = CRGB::White;
    effect->startTime = millis();
    effect->active = true;
    
    nextEffectIndex = (nextEffectIndex + 1) % MAX_KEY_EFFECTS;
  }
}

void createFireBurst() {
  for (int i = 0; i < 4; i++) {
    KeyEffect* effect = &keyEffects[nextEffectIndex];
    effect->position = random(0, NUM_LEDS);
    effect->maxRadius = random(6, 10);
    effect->currentRadius = 0;
    effect->color = CHSV(random(0, 30), 255, 255); // Red to orange
    effect->startTime = millis();
    effect->active = true;
    
    nextEffectIndex = (nextEffectIndex + 1) % MAX_KEY_EFFECTS;
  }
}

void createSparkleRain() {
  for (int i = 0; i < 8; i++) {
    int pos = random(0, NUM_LEDS);
    leds[pos] = CHSV(random(0, 255), 255, 255);
  }
}

void createColorChase() {
  static int chasePos = 0;
  static CRGB chaseColor = CHSV(random(0, 255), 255, 255);
  
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  
  for (int i = 0; i < 10; i++) {
    int pos = (chasePos + i) % NUM_LEDS;
    leds[pos] = chaseColor;
    leds[pos].nscale8(255 - (i * 25));
  }
  
  chasePos = (chasePos + 1) % NUM_LEDS;
  if (chasePos == 0) {
    chaseColor = CHSV(random(0, 255), 255, 255);
  }
}

void knightRiderAnimation() {
  if (millis() - lastUpdate > knightRiderSpeed) {
    // Clear all LEDs
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Light up 6 LEDs with current color
    for (int i = 0; i < knightRiderLength; i++) {
      int pos = knightRiderPos - i;
      if (pos >= 0 && pos < NUM_LEDS) {
        leds[pos] = knightRiderColor;
      }
    }
    
    // Move position
    if (knightRiderDirection) {
      knightRiderPos++;
      if (knightRiderPos >= NUM_LEDS - 1) {
        knightRiderDirection = false;
        // Change to random color when touching right end
        knightRiderColor = CHSV(random(0, 255), 255, 255);
      }
    } else {
      knightRiderPos--;
      if (knightRiderPos <= 0) {
        knightRiderDirection = true;
        // Change to random color when touching left end
        knightRiderColor = CHSV(random(0, 255), 255, 255);
      }
    }
    
    lastUpdate = millis();
  }
}

void keyboardActivityAnimation() {
  if (millis() - lastUpdate > 30) {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Update all active effects
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
      
      if (elapsed < 800) {
        effect->currentRadius = map(elapsed, 0, 800, 0, effect->maxRadius);
        
        for (int r = 0; r <= effect->currentRadius; r++) {
          int brightness = map(r, 0, effect->maxRadius, 255, 30);
          
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
      } else {
        effect->active = false;
      }
    }
  }
}

void updateRippleEffects() {
  for (int i = 0; i < MAX_RIPPLES; i++) {
    if (ripples[i].active) {
      RippleEffect* ripple = &ripples[i];
      unsigned long elapsed = millis() - ripple->startTime;
      
      if (elapsed < 1000) {
        ripple->currentRadius = map(elapsed, 0, 1000, 0, ripple->maxRadius);
        
        int brightness = map(elapsed, 0, 1000, 255, 50);
        
        // Right side
        int rightPos = ripple->centerPos + ripple->currentRadius;
        if (rightPos < NUM_LEDS) {
          leds[rightPos] = ripple->color;
          leds[rightPos].nscale8(brightness);
          
          // Add trailing effect
          for (int trail = 1; trail <= 4 && (rightPos - trail) >= ripple->centerPos; trail++) {
            leds[rightPos - trail] += ripple->color;
            leds[rightPos - trail].nscale8(brightness / (trail + 1));
          }
        }
        
        // Left side
        int leftPos = ripple->centerPos - ripple->currentRadius;
        if (leftPos >= 0) {
          leds[leftPos] = ripple->color;
          leds[leftPos].nscale8(brightness);
          
          // Add trailing effect
          for (int trail = 1; trail <= 4 && (leftPos + trail) <= ripple->centerPos; trail++) {
            leds[leftPos + trail] += ripple->color;
            leds[leftPos + trail].nscale8(brightness / (trail + 1));
          }
        }
      } else {
        ripple->active = false;
      }
    }
  }
}

// Custom effects functions
void parseCustomCommand(String command) {
  int commaIndex = command.indexOf(',', 7);
  if (commaIndex == -1) return;
  
  currentCustomEffect = command.substring(7, commaIndex);
  
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
  FastLED.setBrightness(customBrightness);
  
  currentState = CUSTOM_EFFECT;
  stateChangeTime = millis();
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
  int updateInterval = map(customSpeed, 1, 100, 100, 10);
  
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
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i].nscale8(240);
  }
  
  for (int i = 0; i < 3; i++) {
    int pos = random(NUM_LEDS);
    leds[pos] = customColor;
  }
}

void fireEffect() {
  for (int i = 0; i < NUM_LEDS; i++) {
    int heat = random(160, 255);
    
    if (heat < 85) {
      leds[i] = CRGB(heat * 3, 0, 0);
    } else if (heat < 170) {
      leds[i] = CRGB(255, (heat - 85) * 3, 0);
    } else {
      leds[i] = CRGB(255, 255, (heat - 170) * 3);
    }
    
    leds[i].nscale8(random(200, 255));
  }
}

void sandClockEffect() {
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  
  int topEnd = map(sandClockPos, 0, NUM_LEDS, NUM_LEDS/2, NUM_LEDS);
  for (int i = NUM_LEDS/2; i < topEnd; i++) {
    leds[i] = customColor;
  }
  
  int bottomEnd = map(sandClockPos, 0, NUM_LEDS, NUM_LEDS/2, 0);
  for (int i = bottomEnd; i < NUM_LEDS/2; i++) {
    leds[i] = customColor;
  }
  
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
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i].nscale8(200);
  }
  
  int numLeds = map(audioLevel, 0, 255, 0, NUM_LEDS);
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