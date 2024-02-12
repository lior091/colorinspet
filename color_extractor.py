import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))

def is_grey(color, threshold=30):
    r, g, b = color
    return abs(r - g) < threshold and abs(g - b) < threshold and abs(b - r) < threshold

def calculate_contrast_ratio(color1, color2):
    def adjust_color(color):
        color = color / 255.0
        return color / 12.92 if color <= 0.04045 else ((color + 0.055) / 1.055) ** 2.4

    luminance1 = 0.2126 * adjust_color(color1[0]) + 0.7152 * adjust_color(color1[1]) + 0.0722 * adjust_color(color1[2])
    luminance2 = 0.2126 * adjust_color(color2[0]) + 0.7152 * adjust_color(color2[1]) + 0.0722 * adjust_color(color2[2])

    brighter = max(luminance1, luminance2)
    darker = min(luminance1, luminance2)

    contrast_ratio = (brighter + 0.05) / (darker + 0.05)

    return contrast_ratio

st.title("Image Color Analyzer")

uploaded_file = st.file_uploader("Choose an image")

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    img_array = np.array(img)
    flat_array = img_array.reshape((-1, 3))

    color_counts = {}
    for color in flat_array:
        color_tuple = tuple(color.astype(int))
        color_counts[color_tuple] = color_counts.get(color_tuple, 0) + 1

    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Filter out black, white, and grey shades
    filtered_colors = [(hex_code, count) for (hex_code, count) in sorted_colors
                       if hex_code not in [(0, 0, 0), (255, 255, 255)] and not is_grey(hex_code)]

    # Limit to the top 15 colors
    filtered_colors = filtered_colors[:15]

    # Display the image
    st.image(img, width=300)

    # Display the color information
    st.subheader("Prominent Colors:")
    for color, count in filtered_colors:
        hex_code = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        st.write(f"- **Hex Code:** {hex_code} ({count} pixels)")

        # Display color preview using matplotlib
        plt.figure(figsize=(15, 5))
        plt.bar([0], [1], color=[np.array(color) / 255], width=1)
        plt.axis('off')
        st.pyplot(plt)

    # Summary bar chart of all found colors by dominance ratio
    st.subheader("Color Dominance Summary:")
    colors, counts = zip(*filtered_colors)
    total_pixels = sum(counts)
    dominance_ratios = [count / total_pixels for count in counts]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(filtered_colors)), dominance_ratios, color=[np.array(color) / 255 for color in colors])
    ax.set_xticks(range(len(filtered_colors)))
    ax.set_xticklabels([f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}" for color in colors], rotation=45)
    ax.set_xlabel("Colors")
    ax.set_ylabel("Dominance Ratio")
    ax.set_title("Color Dominance Summary")
    st.pyplot(fig)

    # WCAG Success Criterion 1.4.3 Contrast Analysis
    st.subheader("WCAG Success Criterion 1.4.3 Contrast Analysis:")
    background_color = (255, 255, 255)  # White background for demonstration, adjust as needed

    wcag_data = []
    for color, _ in filtered_colors:
        hex_code = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        contrast_ratio = calculate_contrast_ratio(color, background_color)
        wcag_compliance = "Pass" if contrast_ratio >= 4.5 else "Fail"

        # Thumbnail preview
        thumbnail_color = np.array(color) / 255
        thumbnail = np.full((15, 15, 3), thumbnail_color * 255, dtype=np.uint8)

        # Convert thumbnail to base64
        thumbnail_pil = Image.fromarray(thumbnail)
        thumbnail_byte_array = BytesIO()
        thumbnail_pil.save(thumbnail_byte_array, format="PNG")
        thumbnail_base64 = base64.b64encode(thumbnail_byte_array.getvalue()).decode('utf-8')

        wcag_data.append({
            "Hex Code": hex_code,
            "Contrast Ratio": contrast_ratio,
            "WCAG 2.1 Compliance": wcag_compliance,
            "Preview": thumbnail_base64,
        })

    # Convert wcag_data to DataFrame and sort by Contrast Ratio
    wcag_df = pd.DataFrame(wcag_data).set_index("Hex Code")
    wcag_df = wcag_df.sort_values(by="Contrast Ratio", ascending=False)

    # Display WCAG table with thumbnail in Preview column
    st.write(wcag_df.style.format(
        {
            'Preview': lambda x: f'<img src="data:image/png;base64,{x}" alt="Color Preview" width="15" height="15">'
        }, escape='html').to_html(escape=False), unsafe_allow_html=True)

