"""
Motor Control Module
L298N Driver control for 4 DC motors via GPIO PWM
Provides both manual and automatic tracking control
"""

import logging
import threading
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class MotorController:
    """
    Control 4 DC motors via L298N driver.
    Supports manual direction control and automatic tracking.
    """
    
    def __init__(
        self,
        pin_config: Dict = None,
        enable_gpio: bool = False,
        pwm_frequency: int = 1000
    ):
        """
        Initialize motor controller.
        
        Args:
            pin_config: GPIO pin configuration
            enable_gpio: Enable actual GPIO control (False for testing)
            pwm_frequency: PWM frequency in Hz
        """
        self.pin_config = pin_config or {}
        self.enable_gpio = enable_gpio
        self.pwm_frequency = pwm_frequency
        
        self.motor_threads: Dict[str, threading.Thread] = {}
        self.current_speeds = {
            "motor_1": {"forward": 0, "backward": 0},
            "motor_2": {"forward": 0, "backward": 0},
            "motor_3": {"forward": 0, "backward": 0},
            "motor_4": {"forward": 0, "backward": 0}
        }
        
        self.gpio_initialized = False
        self.running = True
        
        self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Initialize GPIO pins for motor control."""
        if not self.enable_gpio:
            logger.info("GPIO control disabled (testing mode)")
            return
        
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup pins
            for motor, pins in self.pin_config.items():
                if motor == "buzzer":
                    GPIO.setup(pins, GPIO.OUT, initial=GPIO.LOW)
                else:
                    GPIO.setup(pins["IN1"], GPIO.OUT, initial=GPIO.LOW)
                    GPIO.setup(pins["IN2"], GPIO.OUT, initial=GPIO.LOW)
                    GPIO.setup(pins["ENA"], GPIO.OUT, initial=GPIO.LOW)
            
            logger.info("✓ GPIO initialized for motor control")
            self.gpio_initialized = True
        
        except ImportError:
            logger.warning("RPi.GPIO not available - motor control disabled")
            self.enable_gpio = False
        except Exception as e:
            logger.error(f"GPIO initialization error: {str(e)}")
            self.enable_gpio = False
    
    def move(self, direction: str, speed: int = 128):
        """
        Move motors in specified direction.
        
        Args:
            direction: "up", "down", "left", "right", "stop"
            speed: Motor speed 0-255
        """
        speed = max(0, min(255, speed))  # Clamp speed
        
        logger.debug(f"Motor move: {direction} @ {speed}")
        
        if direction == "stop":
            self._stop_all()
        elif direction == "up":
            self._move_up(speed)
        elif direction == "down":
            self._move_down(speed)
        elif direction == "left":
            self._move_left(speed)
        elif direction == "right":
            self._move_right(speed)
    
    def _move_up(self, speed: int):
        """Move camera/platform upward."""
        # Motors 3&4 control vertical movement
        self._set_motor_speed("motor_3", speed, 0)
        self._set_motor_speed("motor_4", speed, 0)
    
    def _move_down(self, speed: int):
        """Move camera/platform downward."""
        self._set_motor_speed("motor_3", 0, speed)
        self._set_motor_speed("motor_4", 0, speed)
    
    def _move_left(self, speed: int):
        """Pan camera/platform left."""
        # Motors 1&2 control horizontal movement
        self._set_motor_speed("motor_1", speed, 0)
        self._set_motor_speed("motor_2", speed, 0)
    
    def _move_right(self, speed: int):
        """Pan camera/platform right."""
        self._set_motor_speed("motor_1", 0, speed)
        self._set_motor_speed("motor_2", 0, speed)
    
    def _stop_all(self):
        """Stop all motors."""
        for motor in ["motor_1", "motor_2", "motor_3", "motor_4"]:
            self._set_motor_speed(motor, 0, 0)
    
    def _set_motor_speed(self, motor: str, forward: int, backward: int):
        """
        Set motor speed.
        
        Args:
            motor: Motor name
            forward: Forward speed 0-255
            backward: Backward speed 0-255
        """
        self.current_speeds[motor] = {
            "forward": forward,
            "backward": backward
        }
        
        if not self.enable_gpio or not self.gpio_initialized:
            return
        
        try:
            import RPi.GPIO as GPIO
            
            pins = self.pin_config.get(motor, {})
            if not pins:
                return
            
            # Set direction
            if forward > 0:
                GPIO.output(pins["IN1"], GPIO.HIGH)
                GPIO.output(pins["IN2"], GPIO.LOW)
            elif backward > 0:
                GPIO.output(pins["IN1"], GPIO.LOW)
                GPIO.output(pins["IN2"], GPIO.HIGH)
            else:
                GPIO.output(pins["IN1"], GPIO.LOW)
                GPIO.output(pins["IN2"], GPIO.LOW)
            
            # Set speed via PWM
            speed = forward or backward
            # PWM would be set here (requires additional PWM setup)
        
        except Exception as e:
            logger.error(f"Motor control error: {str(e)}")
    
    def auto_track(self, motor_control: Dict):
        """
        Automatic tracking based on target position.
        
        Args:
            motor_control: Dict with motor speeds from tracker
        """
        try:
            # Left/right movement
            left_speed = motor_control.get("left_motor_speed", 128)
            right_speed = motor_control.get("right_motor_speed", 128)
            
            # Up/down movement
            up_speed = motor_control.get("up_motor_speed", 128)
            down_speed = motor_control.get("down_motor_speed", 128)
            
            # Apply with smoothing/deadband
            self._apply_smooth_movement(left_speed, right_speed, up_speed, down_speed)
        
        except Exception as e:
            logger.error(f"Auto-track error: {str(e)}")
    
    def _apply_smooth_movement(self, left: int, right: int, up: int, down: int):
        """Apply smooth motor movement with deadband."""
        deadband = 10  # Prevent jitter near center
        
        if abs(left - 128) < deadband:
            left = right = 128
        if abs(up - 128) < deadband:
            up = down = 128
        
        # Set motor speeds
        if left > 128:
            self._set_motor_speed("motor_1", left - 128, 0)
        else:
            self._set_motor_speed("motor_1", 0, 128 - left)
        
        if right > 128:
            self._set_motor_speed("motor_2", 0, right - 128)
        else:
            self._set_motor_speed("motor_2", 128 - right, 0)
        
        if up > 128:
            self._set_motor_speed("motor_3", up - 128, 0)
        else:
            self._set_motor_speed("motor_3", 0, 128 - up)
        
        if down > 128:
            self._set_motor_speed("motor_4", 0, down - 128)
        else:
            self._set_motor_speed("motor_4", 128 - down, 0)
    
    def buzzer(self, duration: float = 0.2):
        """Sound buzzer for alert."""
        if not self.enable_gpio or not self.gpio_initialized:
            return
        
        try:
            import RPi.GPIO as GPIO
            
            buzzer_pin = self.pin_config.get("buzzer")
            if not buzzer_pin:
                return
            
            GPIO.output(buzzer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(buzzer_pin, GPIO.LOW)
        
        except Exception as e:
            logger.error(f"Buzzer error: {str(e)}")
    
    def get_status(self) -> Dict:
        """Get current motor status."""
        return {
            "enabled": self.enable_gpio and self.gpio_initialized,
            "motors": self.current_speeds
        }
    
    def stop(self):
        """Stop all motors and cleanup GPIO."""
        logger.info("Stopping motor controller...")
        
        self.running = False
        self._stop_all()
        
        if self.enable_gpio and self.gpio_initialized:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
                logger.info("GPIO cleaned up")
            except Exception as e:
                logger.error(f"GPIO cleanup error: {str(e)}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.stop()
