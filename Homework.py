import time
import requests
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from config import HF_API_KEY

MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    "CompVis/stable-diffusion-v1-4",
]

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}", "Accept": "image/png"}


def generate_image_from_text(prompt):
    """prompt -> PIL.Image (or raises Exception)."""
    payload, last_err = {"inputs": prompt}, None

    for model in MODELS:
        url = f"https://router.huggingface.co/hf-inference/models/{model}"

        for _ in range(3):
            r = requests.post(url, headers=HEADERS, json=payload, timeout=120)
            ct = (r.headers.get("content-type") or "").lower()

            if r.status_code == 503 and "application/json" in ct:
                try:
                    wait_s = int(r.json().get("estimated_time", 5))
                except Exception:
                    wait_s = 5
                time.sleep(wait_s + 1)
                continue

            if r.status_code == 200 and "application/json" not in ct:
                try:
                    return Image.open(BytesIO(r.content)).convert("RGB")
                except Exception as e:
                    last_err = f"Request failed with status code 200: Could not decode image bytes: {e}"
                    break

            try:
                body = r.json() if "application/json" in ct else r.text
            except Exception:
                body = r.text
            last_err = f"Request failed with status code {r.status_code}: {body}"
            break
    raise Exception(last_err or "Request failed with status code 500: Unknown error")


def create_daylight_edition(image):
    """Brighter, moderate contrast, and softer blur for daylight tones."""
    img = ImageEnhance.Brightness(image).enhance(1.25)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    return img.filter(ImageFilter.GaussianBlur(radius=1.5))


def create_night_mood(image):
    """Lower brightness, higher contrast, and subtle blur for a moody night aesthetic."""
    img = ImageEnhance.Brightness(image).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    return img.filter(ImageFilter.GaussianBlur(radius=0.8))


def main():
    print("Welcome to the Post-Processing Magic Workshop!")
    print("This program generates an AI image and produces two post-processed variations:")
    print("1. Daylight Edition (brighter and softer)")
    print("2. Night Mood (higher contrast and subtle blur)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Enter a description for the image (or 'exit' to quit):\n").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            print("\nGenerating base image...")
            base_image = generate_image_from_text(user_input)

            print("Applying post-processing effects for Daylight Edition and Night Mood...")
            daylight_img = create_daylight_edition(base_image)
            night_img = create_night_mood(base_image)

            daylight_img.show(title="Daylight Edition")
            night_img.show(title="Night Mood")

            save_option = input("\nDo you want to save both processed images? (yes/no): ").strip().lower()
            if save_option == 'yes':
                base_name = input("Enter a base name for the image files (without extension): ").strip()
                daylight_filename = f"{base_name}_daylight.png"
                night_filename = f"{base_name}_night.png"

                daylight_img.save(daylight_filename)
                night_img.save(night_filename)

                print(f"Saved: {daylight_filename}")
                print(f"Saved: {night_filename}\n")

            print("-" * 80 + "\n")

        except Exception as e:
            print(f"An error occurred: {e}\n")


if __name__ == "__main__":
    main()