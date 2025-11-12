#!/usr/bin/env python3
"""
SeeDream Image Generator Script
Generates images using the Doubao SeeDream API and downloads them to the /pic folder.
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime
from openai import OpenAI


def generate_images(
    prompt: str,
    api_key: str,
    size: str = "2K",
    watermark: bool = True,
    max_images: int = 1,
    output_dir: str = None
):
    """
    Generate images using the SeeDream API.

    Args:
        prompt: The text prompt for image generation
        api_key: ARK API key
        size: Image size (e.g., "2K", "2048x2048")
        watermark: Whether to add watermark
        max_images: Maximum number of images to generate (1-4)
        output_dir: Output directory for downloaded images

    Returns:
        List of downloaded image file paths
    """
    # Initialize OpenAI client with ARK endpoint
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )

    # Prepare API call parameters
    extra_body = {"watermark": watermark}

    # Add sequential image generation options if max_images > 1
    if max_images > 1:
        extra_body["sequential_image_generation"] = "auto"
        extra_body["sequential_image_generation_options"] = {
            "max_images": max_images
        }

    print(f"🎨 Generating {max_images} image(s) with prompt: {prompt[:50]}...")

    # Call the image generation API
    try:
        images_response = client.images.generate(
            model="doubao-seedream-4-0-250828",
            prompt=prompt,
            size=size,
            response_format="url",
            extra_body=extra_body,
        )
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        sys.exit(1)

    # Determine output directory
    if output_dir is None:
        # Find project root (look for common project markers)
        current_dir = Path.cwd()
        project_root = current_dir

        # Try to find project root by looking for .git, .claude, or other markers
        while project_root.parent != project_root:
            if any((project_root / marker).exists() for marker in ['.git', '.claude', 'package.json', 'pyproject.toml']):
                break
            project_root = project_root.parent

        output_dir = project_root / "pic"
    else:
        output_dir = Path(output_dir)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")

    # Download images
    downloaded_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for idx, image_data in enumerate(images_response.data):
        image_url = image_data.url
        image_size = image_data.size if hasattr(image_data, 'size') else size

        print(f"🔗 Image {idx + 1} URL: {image_url}")
        print(f"📐 Size: {image_size}")

        # Download image
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Generate filename
            if max_images > 1:
                filename = f"seedream_{timestamp}_{idx + 1}.png"
            else:
                filename = f"seedream_{timestamp}.png"

            file_path = output_dir / filename

            # Save image
            with open(file_path, 'wb') as f:
                f.write(response.content)

            print(f"✅ Downloaded: {file_path}")
            downloaded_files.append(str(file_path))

        except Exception as e:
            print(f"❌ Error downloading image {idx + 1}: {e}")

    # Print usage statistics if available
    if hasattr(images_response, 'usage'):
        usage = images_response.usage
        print(f"\n📊 Usage Statistics:")
        print(f"   Generated images: {usage.generated_images}")
        print(f"   Total tokens: {usage.total_tokens}")

    return downloaded_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Doubao SeeDream API"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text prompt for image generation"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("ARK_API_KEY"),
        help="ARK API key (defaults to ARK_API_KEY environment variable)"
    )
    parser.add_argument(
        "--size",
        type=str,
        default="2K",
        help="Image size (e.g., '2K', '2048x2048'). Default: 2K"
    )
    parser.add_argument(
        "--no-watermark",
        action="store_true",
        help="Disable watermark on generated images"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=1,
        help="Maximum number of images to generate (1-4). Default: 1"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for images (defaults to project_root/pic)"
    )

    args = parser.parse_args()

    # Validate API key
    if not args.api_key:
        print("❌ Error: ARK API key is required.")
        print("   Provide it via --api-key argument or ARK_API_KEY environment variable.")
        sys.exit(1)

    # Validate max_images range
    if args.max_images < 1 or args.max_images > 4:
        print("❌ Error: max_images must be between 1 and 4")
        sys.exit(1)

    # Generate and download images
    downloaded_files = generate_images(
        prompt=args.prompt,
        api_key=args.api_key,
        size=args.size,
        watermark=not args.no_watermark,
        max_images=args.max_images,
        output_dir=args.output_dir
    )

    print(f"\n✨ Successfully generated and downloaded {len(downloaded_files)} image(s)!")


if __name__ == "__main__":
    main()
