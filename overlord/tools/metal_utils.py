"""
Metal GPU acceleration utilities for image processing and ML workloads.
Provides Metal device management, optimized image processing, and CoreML integration.
"""

import numpy as np
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Check if we're on macOS/Apple Silicon
IS_MACOS = platform.system() == "Darwin"
IS_APPLE_SILICON = platform.machine() == "arm64" and IS_MACOS

# Conditionally import Metal-related modules to avoid errors on non-Mac platforms
if IS_MACOS:
    try:
        # Import Metal-related modules
        import Metal
        import MetalKit
        import MetalPerformanceShaders as MPS
        from PIL import Image
        HAS_METAL = True
    except ImportError:
        HAS_METAL = False
else:
    HAS_METAL = False

# Global Metal device and command queue
_metal_device = None
_command_queue = None
_metal_initialized = False

def get_metal_device():
    """Get the default Metal device or None if Metal is not available"""
    global _metal_device, _metal_initialized
    
    if _metal_initialized:
        return _metal_device
        
    _metal_initialized = True
    
    if not HAS_METAL:
        print("Metal frameworks not available")
        return None
        
    try:
        # Create Metal device
        devices = Metal.MTLCopyAllDevices()
        if not devices:
            print("No Metal devices found")
            return None
            
        # Prefer high-performance GPU if available
        for device in devices:
            if device.isLowPower() == False:
                _metal_device = device
                break
                
        # Fall back to first available device
        if _metal_device is None and len(devices) > 0:
            _metal_device = devices[0]
            
        if _metal_device:
            print(f"Using Metal device: {_metal_device.name()}")
        else:
            print("No suitable Metal device found")
            
        return _metal_device
    except Exception as e:
        print(f"Error initializing Metal: {e}")
        return None

def get_command_queue():
    """Get the command queue for the default Metal device"""
    global _command_queue, _metal_device
    
    if _command_queue:
        return _command_queue
        
    device = get_metal_device()
    if not device:
        return None
        
    try:
        _command_queue = device.newCommandQueue()
        return _command_queue
    except Exception as e:
        print(f"Error creating command queue: {e}")
        return None

def can_use_metal():
    """Check if Metal is available and initialized"""
    return HAS_METAL and get_metal_device() is not None

def process_image_with_metal(image_path: str, output_path: str = None, 
                           max_width: int = None, max_height: int = None) -> bool:
    """
    Process an image using Metal for optimal performance
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the processed image (defaults to input path)
        max_width: Maximum width to resize to (keeping aspect ratio)
        max_height: Maximum height to resize to (keeping aspect ratio)
        
    Returns:
        True if processing was successful
    """
    if not can_use_metal():
        print("Metal not available, falling back to PIL")
        return False
        
    if not output_path:
        output_path = image_path
        
    try:
        # Load image using MetalKit
        device = get_metal_device()
        loader = MetalKit.MTKTextureLoader.alloc().initWithDevice_(device)
        
        # Load image from path
        texture_options = {
            MetalKit.MTKTextureLoaderOptionSRGB: False
        }
        texture = loader.newTextureWithContentsOfURL_options_error_(
            Path(image_path).as_posix(), 
            texture_options, 
            None
        )[0]
        
        if not texture:
            print("Failed to load texture")
            return False
            
        # Resize if needed
        if max_width and max_height:
            # Calculate new dimensions while preserving aspect ratio
            src_width = texture.width()
            src_height = texture.height()
            
            # Calculate scale factor based on max dimensions
            scale_w = max_width / src_width if src_width > max_width else 1.0
            scale_h = max_height / src_height if src_height > max_height else 1.0
            scale = min(scale_w, scale_h)
            
            # Only resize if needed
            if scale < 1.0:
                new_width = int(src_width * scale)
                new_height = int(src_height * scale)
                
                # Create MPS scale transform
                scaler = MPS.MPSImageBilinearScale.alloc().initWithDevice_(device)
                
                # Create destination texture
                texture_descriptor = Metal.MTLTextureDescriptor.texture2DDescriptorWithPixelFormat_width_height_mipmapped_(
                    texture.pixelFormat(),
                    new_width,
                    new_height,
                    False
                )
                dest_texture = device.newTextureWithDescriptor_(texture_descriptor)
                
                # Execute scaling
                command_buffer = get_command_queue().commandBuffer()
                scaler.encodeToCommandBuffer_sourceTexture_destinationTexture_(
                    command_buffer,
                    texture,
                    dest_texture
                )
                command_buffer.commit()
                command_buffer.waitUntilCompleted()
                
                # Update texture to the resized version
                texture = dest_texture
        
        # Save processed image
        # Since Metal doesn't have direct image saving, we need to extract pixel data
        # and save using another library
        
        # Create a buffer to hold texture data
        bytes_per_pixel = 4  # RGBA
        bytes_per_row = bytes_per_pixel * texture.width()
        total_bytes = bytes_per_row * texture.height()
        
        # Create a buffer to hold the data
        buffer = Metal.MTLBuffer.alloc().initWithDevice_length_options_(
            device,
            total_bytes,
            Metal.MTLResourceStorageModeShared
        )
        
        # Copy texture to buffer
        command_buffer = get_command_queue().commandBuffer()
        blit_encoder = command_buffer.blitCommandEncoder()
        region = Metal.MTLRegionMake2D(0, 0, texture.width(), texture.height())
        blit_encoder.copyFromTexture_sourceSlice_sourceLevel_sourceOrigin_sourceSize_toBuffer_destinationOffset_destinationBytesPerRow_(
            texture,
            0,
            0,
            (0, 0, 0),
            (texture.width(), texture.height(), 1),
            buffer,
            0,
            bytes_per_row
        )
        blit_encoder.endEncoding()
        command_buffer.commit()
        command_buffer.waitUntilCompleted()
        
        # Convert buffer to numpy array
        data = np.frombuffer(buffer.contents(), dtype=np.uint8)
        data = data.reshape(texture.height(), texture.width(), 4)
        
        # Create PIL image from numpy array and save
        img = Image.fromarray(data, 'RGBA')
        img.save(output_path)
        
        return True
    except Exception as e:
        print(f"Error processing image with Metal: {e}")
        return False

def accelerate_screenshot(input_path: str, output_path: str = None, 
                        max_width: int = None, max_height: int = None) -> bool:
    """
    Optimize screenshot processing using Metal acceleration
    
    Args:
        input_path: Path to the screenshot
        output_path: Path to save the processed screenshot (defaults to input path)
        max_width: Maximum width to resize to
        max_height: Maximum height to resize to
        
    Returns:
        True if Metal acceleration was used, False if fallback was used
    """
    # Try to use Metal first
    if process_image_with_metal(input_path, output_path, max_width, max_height):
        return True
        
    # Fall back to traditional methods (sips command)
    if not output_path:
        output_path = input_path
        
    try:
        if max_width and max_height:
            # Use sips for resizing (macOS built-in)
            subprocess.run(
                ["sips", "-Z", str(max(max_width, max_height)), input_path, "--out", output_path],
                check=True,
                capture_output=True,
                text=True
            )
        elif input_path != output_path:
            # Just copy the file
            subprocess.run(
                ["cp", input_path, output_path],
                check=True,
                capture_output=True,
                text=True
            )
        return False
    except Exception as e:
        print(f"Error processing image with fallback method: {e}")
        return False

# Performance measurement utilities
def benchmark_metal_vs_traditional(image_path: str, width: int = 1280, height: int = 800, 
                                 iterations: int = 5):
    """
    Compare performance between Metal and traditional image processing
    
    Args:
        image_path: Path to the test image
        width: Target width for resizing
        height: Target height for resizing
        iterations: Number of iterations for the benchmark
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "metal": {"available": False, "times": [], "avg_time": 0},
        "traditional": {"times": [], "avg_time": 0}
    }
    
    # Create temp files
    metal_output = "/tmp/metal_benchmark.png"
    trad_output = "/tmp/trad_benchmark.png"
    
    # Test Metal performance
    if can_use_metal():
        results["metal"]["available"] = True
        for i in range(iterations):
            start_time = time.time()
            process_image_with_metal(image_path, metal_output, width, height)
            elapsed = time.time() - start_time
            results["metal"]["times"].append(elapsed)
        
        results["metal"]["avg_time"] = sum(results["metal"]["times"]) / iterations
    
    # Test traditional performance
    for i in range(iterations):
        start_time = time.time()
        subprocess.run(
            ["sips", "-Z", str(max(width, height)), image_path, "--out", trad_output],
            check=True,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start_time
        results["traditional"]["times"].append(elapsed)
    
    results["traditional"]["avg_time"] = sum(results["traditional"]["times"]) / iterations
    
    # Calculate speedup
    if results["metal"]["available"]:
        speedup = results["traditional"]["avg_time"] / results["metal"]["avg_time"]
        results["speedup"] = speedup
    
    # Clean up
    for path in [metal_output, trad_output]:
        if os.path.exists(path):
            os.remove(path)
    
    return results
