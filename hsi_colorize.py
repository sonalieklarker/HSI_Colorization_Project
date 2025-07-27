import cv2
import numpy as np

def hsi_to_rgb(H, S, I):
    """
    Convert HSI image to RGB image.
    H in degrees (0-360), S and I in [0,1]
    Returns RGB image in uint8 format (0-255)
    """
    H = H % 360  # wrap-around

    R = np.zeros_like(H)
    G = np.zeros_like(H)
    B = np.zeros_like(H)

    # Sector 0: 0 <= H < 120
    idx = (H >= 0) & (H < 120)
    h_rad = np.deg2rad(H[idx])

    B[idx] = I[idx] * (1 - S[idx])
    R[idx] = I[idx] * (1 + (S[idx] * np.cos(h_rad)) / (np.cos(np.deg2rad(60) - h_rad)))
    G[idx] = 3 * I[idx] - (R[idx] + B[idx])

    # Sector 1: 120 <= H < 240
    idx = (H >= 120) & (H < 240)
    h_rad = np.deg2rad(H[idx] - 120)

    R[idx] = I[idx] * (1 - S[idx])
    G[idx] = I[idx] * (1 + (S[idx] * np.cos(h_rad)) / (np.cos(np.deg2rad(60) - h_rad)))
    B[idx] = 3 * I[idx] - (R[idx] + G[idx])

    # Sector 2: 240 <= H < 360
    idx = (H >= 240) & (H < 360)
    h_rad = np.deg2rad(H[idx] - 240)

    G[idx] = I[idx] * (1 - S[idx])
    B[idx] = I[idx] * (1 + (S[idx] * np.cos(h_rad)) / (np.cos(np.deg2rad(60) - h_rad)))
    R[idx] = 3 * I[idx] - (G[idx] + B[idx])

    # Clip to [0,1]
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    rgb_img = np.dstack((R, G, B)) * 255
    return rgb_img.astype(np.uint8)

def main():
    # Step 1: Load and convert color image to grayscale automatically
    color_img = cv2.imread('any_color_image.jpeg')  # updated to .jpeg
    if color_img is None:
        print("Error: 'any_color_image.jpeg' not found!")
        return

    gray_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('grayscale_image.jpg', gray_img)  # Save grayscale for reference

    # Step 2: Normalize intensity
    I = gray_img.astype(np.float32) / 255.0

    # Step 3: Map intensity to full rainbow hue (0°-360°)
    H = 360 * I  # full hue circle based on intensity

    # Step 4: Use strong constant saturation for vivid colors
    S = 0.9 * np.ones_like(I)

    # Step 5: Convert HSI to RGB
    colorized_img = hsi_to_rgb(H, S, I)

    # Step 6: Display and save output
    cv2.imshow('Original Color Image', color_img)
    cv2.imshow('Converted Grayscale', gray_img)
    cv2.imshow('Rainbow Colorized Image', colorized_img)
    cv2.imwrite('colorized_rainbow_output.jpg', colorized_img)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
