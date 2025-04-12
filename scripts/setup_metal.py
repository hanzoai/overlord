#!/usr/bin/env python3
"""
Setup script for Metal GPU acceleration
This script installs the necessary dependencies for Metal GPU acceleration
and verifies that they're working correctly.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(cmd, verbose=True):
    """Execute a shell command and return the success status"""
    if verbose:
        print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=False, 
                               capture_output=True, text=True)
        if result.returncode != 0:
            if verbose:
                print(f"Error: {result.stderr}")
            return False
        else:
            if verbose:
                print(f"Success: {result.stdout}")
            return True
    except Exception as e:
        if verbose:
            print(f"Exception: {str(e)}")
        return False


def is_metal_available():
    """Check if Metal is available on the system"""
    if platform.system() != "Darwin":
        print("Metal GPU acceleration is only available on macOS")
        return False
    
    try:
        # Try to import the Metal module
        import Metal
        return True
    except ImportError:
        return False


def install_metal_dependencies():
    """Install the necessary dependencies for Metal GPU acceleration"""
    if platform.system() != "Darwin":
        print("Metal GPU acceleration is only available on macOS")
        return False
    
    print("\n=== Installing Metal GPU acceleration dependencies ===\n")
    
    dependencies = [
        "pip install -U pip",
        "pip install -U wheel setuptools",
        "pip install -U numpy pillow",
        "pip install -U pyobjc-core",
        "pip install -U pyobjc-framework-Cocoa",
        "pip install -U pyobjc-framework-Quartz",
        "pip install -U pyobjc-framework-Metal",
        "pip install -U pyobjc-framework-MetalKit",
        "pip install -U pyobjc-framework-MetalPerformanceShaders",
    ]
    
    success = True
    for cmd in dependencies:
        if not run_command(cmd):
            print(f"Failed to install dependency with: {cmd}")
            success = False
    
    return success


def verify_metal_installation():
    """Verify that Metal dependencies are correctly installed"""
    print("\n=== Verifying Metal GPU acceleration setup ===\n")
    
    try:
        import Metal
        print("✅ Metal framework is installed")
    except ImportError:
        print("❌ Metal framework is not installed")
        return False
    
    try:
        import MetalKit
        print("✅ MetalKit framework is installed")
    except ImportError:
        print("❌ MetalKit framework is not installed")
        return False
    
    try:
        import MetalPerformanceShaders
        print("✅ MetalPerformanceShaders framework is installed")
    except ImportError:
        print("❌ MetalPerformanceShaders framework is not installed")
        return False
    
    # Check if we can actually get a Metal device
    try:
        devices = Metal.MTLCopyAllDevices()
        if devices and len(devices) > 0:
            print(f"✅ Found {len(devices)} Metal device(s):")
            for i, device in enumerate(devices):
                print(f"  {i+1}. {device.name()} ({device.registryID()})")
        else:
            print("❌ No Metal devices found")
            return False
    except Exception as e:
        print(f"❌ Failed to enumerate Metal devices: {e}")
        return False
    
    return True


def test_metal_performance():
    """Run a simple benchmark to test Metal performance"""
    print("\n=== Testing Metal GPU performance ===\n")
    
    try:
        # Add the parent directory to the sys.path so we can import the metal_utils module
        current_dir = Path(__file__).resolve().parent
        project_dir = current_dir.parent
        overlord_dir = project_dir / "overlord"
        
        sys.path.insert(0, str(project_dir))
        
        # Test image path - create a simple test image if it doesn't exist
        test_image_dir = project_dir / "tests" / "data"
        test_image_dir.mkdir(parents=True, exist_ok=True)
        test_image_path = test_image_dir / "test_image.png"
        
        # Create a test image if it doesn't exist
        if not test_image_path.exists():
            try:
                from PIL import Image, ImageDraw
                img = Image.new('RGB', (1280, 800), color=(73, 109, 137))
                d = ImageDraw.Draw(img)
                d.rectangle([(100, 100), (1180, 700)], fill=(255, 128, 0))
                d.ellipse([(400, 200), (880, 600)], fill=(0, 0, 0))
                img.save(test_image_path)
                print(f"Created test image at {test_image_path}")
            except Exception as e:
                print(f"Failed to create test image: {e}")
                test_image_path = None
        
        if test_image_path and test_image_path.exists():
            try:
                from overlord.tools.metal_utils import benchmark_metal_vs_traditional
                
                # Run the benchmark
                print("Running benchmark (this may take a few seconds)...")
                results = benchmark_metal_vs_traditional(str(test_image_path))
                
                # Print results
                if results["metal"]["available"]:
                    metal_time = results["metal"]["avg_time"]
                    trad_time = results["traditional"]["avg_time"]
                    speedup = results["speedup"]
                    
                    print(f"\nMetal GPU acceleration benchmark results:")
                    print(f"- Metal processing time: {metal_time:.4f}s")
                    print(f"- Traditional processing time: {trad_time:.4f}s")
                    print(f"- Speedup: {speedup:.2f}x")
                    
                    if speedup > 1.0:
                        print("\n✅ Metal GPU acceleration is working and provides a speedup!")
                    else:
                        print("\n⚠️ Metal GPU acceleration is working but provides no speedup.")
                else:
                    print("\n❌ Metal GPU acceleration is not available for benchmarking.")
            except Exception as e:
                print(f"Error during benchmark: {e}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        print(f"Failed to run performance test: {e}")


def main():
    """Main entry point for the script"""
    print(f"=== Metal GPU Acceleration Setup ===")
    print(f"System: {platform.system()} {platform.version()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {platform.python_version()}")
    
    # Check if we're on macOS
    if platform.system() != "Darwin":
        print("Metal GPU acceleration is only available on macOS")
        return 1
    
    # Check if Metal is already available
    if is_metal_available():
        print("Metal GPU acceleration is already available!")
    else:
        print("Metal GPU acceleration is not available, installing dependencies...")
        if not install_metal_dependencies():
            print("Failed to install some Metal dependencies.")
            # Continue anyway to see what worked
    
    # Verify the installation
    if verify_metal_installation():
        print("\n✅ Metal GPU acceleration setup completed successfully!")
        
        # Run the performance test
        test_metal_performance()
        
        print("\nYou can now use Metal GPU acceleration in Overlord!")
    else:
        print("\n❌ Metal GPU acceleration setup failed.")
        print("Please check the errors above and try again.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
