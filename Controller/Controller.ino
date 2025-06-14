#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN     6
#define NUM_LEDS    60  // Updated to 60 LEDs
#define BRIGHTNESS  100
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

// Center-to-end ripple effect variables
struct RippleEffect {
  int centerPos;
  int currentRadius;
  int maxRadius;
  CRGB color;
  unsigned long startTime;
  bool active;
  bool expandingOut;
};

#define MAX_RIPPLES 3
RippleEffect ripples[MAX_RIPPLES];
int nextRippleIndex = 0;

// States
enum AnimationState {
  IDLE_KNIGHT_RIDER,
  KEYBOARD_ACTIVITY,
  NOTIFICATION_ALERT
};

AnimationState currentState = IDLE_KNIGHT_RIDER;
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
  
  Serial.println("Arduino LED Controller Ready - 60 LEDs");
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
      
      // Create random blink effect
      createRandomBlinkEffect();
      
      // Create center-to-end ripple effect
      createCenterRippleEffect();
    }
    else if (command == "NOTIFY") {
      currentState = NOTIFICATION_ALERT;
      stateChangeTime = millis();
    }
    else if (command == "IDLE") {
      currentState = IDLE_KNIGHT_RIDER;
      stateChangeTime = millis();
    }
  }
  
  // Auto return to idle after keyboard inactivity
  if (currentState == KEYBOARD_ACTIVITY && 
      millis() - lastKeyboardActivity > 5000) { // 5 seconds
    currentState = IDLE_KNIGHT_RIDER;
    stateChangeTime = millis();
  }
  
  // Auto return to idle after notification
  if (currentState == NOTIFICATION_ALERT && 
      millis() - stateChangeTime > 10000) { // 10 seconds
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
  }
  
  FastLED.show();
  delay(20); // Control animation speed - reduced for smoother effects
}

void knightRiderAnimation() {
  if (millis() - lastUpdate > 100) { // Update every 100ms
    // Clear all LEDs
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Create trailing effect
    for (int i = 0; i < 5; i++) {
      int pos = knightRiderPos - i;
      if (pos >= 0 && pos < NUM_LEDS) {
        leds[pos] = CRGB(255 - (i * 50), 0, 0); // Red with fade
      }
      pos = knightRiderPos + i;
      if (pos >= 0 && pos < NUM_LEDS) {
        leds[pos] = CRGB(255 - (i * 50), 0, 0); // Red with fade
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
  if (millis() - lastUpdate > 30) { // Fast update
    // Clear all LEDs first
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Update and draw random blink effects
    updateBlinkEffects();
    
    // Update and draw center ripple effects
    updateRippleEffects();
    
    // No background effects - only the key press effects
    
    lastUpdate = millis();
  }
}

void createRandomBlinkEffect() {
  // Create random position blink effect
  KeyEffect* effect = &keyEffects[nextEffectIndex];
  effect->position = random(0, NUM_LEDS);
  effect->maxRadius = random(3, 8);
  effect->currentRadius = 0;
  effect->color = CHSV(random(0, 255), 255, 255); // Random bright color
  effect->startTime = millis();
  effect->active = true;
  
  nextEffectIndex = (nextEffectIndex + 1) % MAX_KEY_EFFECTS;
}

void createCenterRippleEffect() {
  // Create center-to-end ripple effect
  RippleEffect* ripple = &ripples[nextRippleIndex];
  ripple->centerPos = NUM_LEDS / 2; // Center of strip
  ripple->currentRadius = 0;
  ripple->maxRadius = NUM_LEDS / 2;
  ripple->color = CHSV(random(0, 255), 255, 200); // Random color
  ripple->startTime = millis();
  ripple->active = true;
  ripple->expandingOut = true;
  
  nextRippleIndex = (nextRippleIndex + 1) % MAX_RIPPLES;
}

void updateBlinkEffects() {
  for (int i = 0; i < MAX_KEY_EFFECTS; i++) {
    if (keyEffects[i].active) {
      KeyEffect* effect = &keyEffects[i];
      unsigned long elapsed = millis() - effect->startTime;
      
      if (elapsed < 500) { // Effect duration 500ms
        // Calculate current radius based on time
        effect->currentRadius = map(elapsed, 0, 500, 0, effect->maxRadius);
        
        // Draw expanding circle around position
        for (int r = 0; r <= effect->currentRadius; r++) {
          // Calculate brightness based on distance from center
          int brightness = map(r, 0, effect->maxRadius, 255, 50);
          
          // Draw left side
          int leftPos = effect->position - r;
          if (leftPos >= 0 && leftPos < NUM_LEDS) {
            leds[leftPos] = effect->color;
            leds[leftPos].nscale8(brightness);
          }
          
          // Draw right side
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
      
      if (elapsed < 800) { // Ripple duration 800ms
        // Calculate current radius
        ripple->currentRadius = map(elapsed, 0, 800, 0, ripple->maxRadius);
        
        // Draw ripple expanding from center to both ends
        int brightness = map(elapsed, 0, 800, 255, 80);
        
        // Expand to the right
        int rightPos = ripple->centerPos + ripple->currentRadius;
        if (rightPos < NUM_LEDS) {
          leds[rightPos] = ripple->color;
          leds[rightPos].nscale8(brightness);
          
          // Add trailing effect
          for (int trail = 1; trail <= 3 && (rightPos - trail) >= ripple->centerPos; trail++) {
            leds[rightPos - trail] += ripple->color;
            leds[rightPos - trail].nscale8(brightness / (trail + 1));
          }
        }
        
        // Expand to the left
        int leftPos = ripple->centerPos - ripple->currentRadius;
        if (leftPos >= 0) {
          leds[leftPos] = ripple->color;
          leds[leftPos].nscale8(brightness);
          
          // Add trailing effect
          for (int trail = 1; trail <= 3 && (leftPos + trail) <= ripple->centerPos; trail++) {
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
void notificationAlertAnimation() {
  if (millis() - lastUpdate > 30) { // Fast update for smooth wave effect
    // Clear LEDs
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    
    // Calculate wave position based on time
    int waveSpeed = 2; // Controls how fast waves move
    int waveWidth = 8; // Width of each wave
    unsigned long time = millis();
    int waveOffset = (time / 30) % (NUM_LEDS * 2); // Cycle through strip length
    
    // Create waves moving outward from center
    int center = NUM_LEDS / 2;
    for (int i = 0; i < NUM_LEDS; i++) {
      int distFromCenter = abs(i - center);
      int wavePos = (waveOffset + distFromCenter) % (NUM_LEDS * 2);
      
      // Calculate brightness based on wave position
      if (wavePos < waveWidth) {
        int brightness = map(wavePos, 0, waveWidth, 255, 50);
        
        // Cycle through rainbow colors based on time
        uint8_t hue = (time / 50) % 255; // Change color every 50ms
        leds[i] = CHSV(hue, 255, brightness);
        
        // Add trailing effect
        for (int trail = 1; trail <= 3; trail++) {
          int trailPos = i + (i < center ? trail : -trail);
          if (trailPos >= 0 && trailPos < NUM_LEDS) {
            leds[trailPos] += CHSV(hue, 255, brightness / (trail + 1));
          }
        }
      }
    }
    
    lastUpdate = millis();
  }
}