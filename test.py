import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cairo
import time
import subprocess
import os
import pyperclip
import threading
from paddleocr import PaddleOCR
import pychrome
import io


temp_text_image_path = "temp_text_image.png"

# Step 1: Run OCR and extract text from the image
def detect_text_from_image(image_path):
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(image_path, cls=True)
        if not result or not result[0]:  # Ensure result is not None or empty
            raise ValueError("No text detected in the image.")
        return "\n".join([line[1][0] for line in result[0]])
    except Exception as e:
        messagebox.showerror("OCR Error", f"Error in text detection: {e}")
        return None

# Step 2: Send text to ChatGPT and get formatted response
def open_chatgpt_in_browser_and_input(ocr_text):
    start_chrome()
    browser = pychrome.Browser(url="http://localhost:9223")
    tab = browser.list_tab()[0]
    tab.start()
    tab.Page.navigate(url="https://chat.openai.com")
    time.sleep(5)
    send_message_to_chatgpt(tab, "explain and text format for exam pov and don't include the preceding line in response " + ocr_text)
    
    return get_chatgpt_response(tab)

def start_chrome():
    subprocess.Popen(["google-chrome", "--remote-debugging-port=9223"])
    time.sleep(3)

def send_message_to_chatgpt(tab, message):
    script = f"""
        const inputField = document.querySelector('div[contenteditable="true"]');
        if (inputField) {{
            inputField.textContent = `{message}`;
            inputField.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    """
    tab.Runtime.evaluate(expression=script)
    time.sleep(2)
    tab.Runtime.evaluate(expression="document.querySelector('button[aria-label=\"Send prompt\"]').click()")

def get_chatgpt_response(tab):
    start_time = time.time()
    while time.time() - start_time < 60:
        result = tab.Runtime.evaluate(expression="document.body.innerText")
        response = result.get('result', {}).get('value', '')

        if response and "generating" not in response.lower():
            start_idx = response.lower().find("chatgpt says:")
            if start_idx != -1:
                chatgpt_response = response[start_idx + len("ChatGPT says:"):].strip()
                pyperclip.copy(chatgpt_response)
                return chatgpt_response

        time.sleep(2)

    return None

# Function to create an image from the text using Cairo
def create_text_image_cairo(text, font_size=24, font_color=(0, 0, 0), max_width=500, right_margin=100):
    # Initialize variables for layout
    lines = []
    words = text.split()
    line = []
    current_width = 0

    # Estimate font height
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    context = cairo.Context(surface)
    context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    context.set_font_size(font_size)

    space_width = context.text_extents(" ")[2]  # Width of a single space
    font_height = context.text_extents("Tg")[3]  # Approximate line height

    # Wrap text into lines
    for word in words:
        word_width = context.text_extents(word)[2]
        if current_width + word_width + (space_width if line else 0) > max_width:
            lines.append(" ".join(line))
            line = [word]
            current_width = word_width
        else:
            line.append(word)
            current_width += word_width + (space_width if line else 0)

    if line:
        lines.append(" ".join(line))

    # Calculate image dimensions
    image_width = int(max_width + right_margin)  # Ensure integer dimensions
    image_height = int(len(lines) * font_height + len(lines) * 5)  # Add padding and ensure integer dimensions

    # Create image surface
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, image_width, image_height)
    context = cairo.Context(surface)

    # Set background color
    context.set_source_rgb(1, 1, 1)  # White
    context.rectangle(0, 0, image_width, image_height)
    context.fill()

    # Set font and text color
    context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    context.set_font_size(font_size)
    context.set_source_rgb(font_color[0] / 255, font_color[1] / 255, font_color[2] / 255)

    # Draw the lines of text
    y_offset = font_height
    for line in lines:
        context.move_to(10, y_offset)
        context.show_text(line)
        y_offset += font_height + 5  # Line height + padding

    surface.flush()
    return surface

# Function to resize the left image to match the height of the right image while maintaining high quality
def resize_left_image_to_match_right(left_image, right_image):
    right_width, right_height = right_image.size
    left_width, left_height = left_image.size
    new_width = int(left_width * (right_height / left_height))  # Resize maintaining aspect ratio
    
    # Resize using a high-quality filter (LANCZOS or ANTIALIAS for better quality)
    left_image_resized = left_image.resize((new_width, right_height), Image.LANCZOS)
    return left_image_resized

# Function to combine the left and right images
def combine_images(left_image_path, right_image):
    try:
        # Load the left image
        left_image = Image.open(left_image_path)
        
        # Resize the left image to match the right image height, maintaining aspect ratio
        left_image_resized = resize_left_image_to_match_right(left_image, right_image)
        
        # Get dimensions of the resized left image and the right image
        left_width, left_height = left_image_resized.size
        right_width, right_height = right_image.size

        # Determine the total dimensions of the combined image
        total_width = left_width + right_width
        total_height = max(left_height, right_height)

        # Add padding to align images vertically
        padded_left_image = Image.new("RGB", (left_width, total_height), (255, 255, 255))
        padded_left_image.paste(left_image_resized, (0, (total_height - left_height) // 2))

        padded_right_image = Image.new("RGB", (right_width, total_height), (255, 255, 255))
        padded_right_image.paste(right_image, (0, (total_height - right_height) // 2))

        # Create the combined image
        combined_image = Image.new("RGB", (total_width, total_height), (255, 255, 255))
        combined_image.paste(padded_left_image, (0, 0))
        combined_image.paste(padded_right_image, (left_width, 0))

        return combined_image
    except Exception as e:
        messagebox.showerror("Error", f"Error combining images: {e}")
        return None

# Function to update the displayed text image based on typed input
def update_text_image():
    text = text_input.get("1.0", "end-1c")  # Get text from the text widget

    # Create the composite image from the text using Cairo
    surface = create_text_image_cairo(text, font_size=24, font_color=(0, 0, 0))
    surface.write_to_png(temp_text_image_path)

    # Convert the Cairo-generated image to Tkinter-compatible format
    img = Image.open(temp_text_image_path)
    img_tk = ImageTk.PhotoImage(img)
    img_label.config(image=img_tk)
    img_label.image = img_tk

    # Save the generated image globally for later use in the combination process
    global right_image_for_combination
    right_image_for_combination = img

# Step 4: Combine original image and text image
def combine_image_and_text(original_image_path, text_image_path):
    try:
        # Open images
        original_image = Image.open(original_image_path)
        text_image = Image.open(text_image_path)

        # Dimensions
        left_width, left_height = original_image.size
        right_width, right_height = text_image.size

        # Compute padding for smaller image
        total_height = max(left_height, right_height)
        total_width = left_width + right_width

        # Add padding to smaller image (top and bottom for height, left and right for width)
        padded_left_image = Image.new("RGB", (left_width, total_height), (255, 255, 255))  # White padding
        padded_left_image.paste(original_image, (0, (total_height - left_height) // 2))

        padded_right_image = Image.new("RGB", (right_width, total_height), (255, 255, 255))  # White padding
        padded_right_image.paste(text_image, (0, (total_height - right_height) // 2))

        # Create final combined image
        combined_image = Image.new("RGB", (total_width, total_height), (255, 255, 255))  # White background
        combined_image.paste(padded_left_image, (0, 0))
        combined_image.paste(padded_right_image, (left_width, 0))

        return combined_image
    except Exception as e:
        messagebox.showerror("Error", f"Error combining images: {e}")
        return None

# Step 5: Show progress and final output
def process_image(file_path):
    try:
        loading_screen.pack()

        # Step 1: Run OCR
        text = detect_text_from_image(file_path)

        # Fill the text_output widget with the extracted OCR text
        text_output.delete(1.0, tk.END)
        text_output.insert(tk.END, f"Extracted Text:\n{text}\n\n")

        # Step 2: Send text to ChatGPT
        gpt_response = open_chatgpt_in_browser_and_input(text)
        if not gpt_response:
            raise Exception("Failed to get response from ChatGPT")

        # Fill the text_output widget with the ChatGPT response
        text_output.insert(tk.END, f"ChatGPT Response:\n{gpt_response}\n\n")

        # Step 3: Create text image using the updated text image creation method
        # Create the text image using Cairo
        surface = create_text_image_cairo(gpt_response, font_size=24, font_color=(0, 0, 0))
        surface.write_to_png(temp_text_image_path)

        # Convert the Cairo-generated image to Tkinter-compatible format
        img = Image.open(temp_text_image_path)
        img_tk = ImageTk.PhotoImage(img)
        img_label.config(image=img_tk)
        img_label.image = img_tk

        # Save the generated image globally for later use in the combination process
        global right_image_for_combination
        right_image_for_combination = img

        # Step 4: Combine original and text images
        global combined_image
        combined_image = combine_image_and_text(file_path, temp_text_image_path)
        if not combined_image:
            raise Exception("Failed to combine images")

        # Step 5: Ask user where to save the combined image
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png", 
            filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")],
            title="Save Combined Image"
        )

        if not save_path:
            messagebox.showwarning("No Save Path", "No file path selected. The image was not saved.")
            return

        # Save the final combined image
        combined_image.save(save_path)

        # Step 6: Display success message
        loading_screen.pack_forget()
        messagebox.showinfo("Success", f"Processing completed!\nImage saved at: {save_path}")

    except Exception as e:
        loading_screen.pack_forget()
        messagebox.showerror("Error", f"Error processing image: {e}")

def savep():
    save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")],title="Save Combined Image")

    if not save_path:
        messagebox.showwarning("No Save Path", "No file path selected. The image was not saved.")
        return

    # Save the final combined image
    combined_image.save(save_path)
    # Step 6: Display success message
    loading_screen.pack_forget()
    messagebox.showinfo("Success", f"Processing completed!\nImage saved at: {save_path}")
# UI Elements for Tkinter
def open_file_explorer():
    file_paths = filedialog.askopenfilenames(title="Select Files", filetypes=[("All Files", "*.*")])  # Allow all file types
    if file_paths:
        global original_image_path
        original_image_path = file_paths[0]
        threading.Thread(target=process_image, args=(file_paths[0],)).start()
root = tk.Tk()
root.title("OCR and ChatGPT Image Processing")
root.geometry("850x650")

frame_top = tk.Frame(root)
frame_top.pack(pady=20)

load_button = tk.Button(frame_top, text="Open Files", command=open_file_explorer, bg="#0078d7", fg="white", font=("Arial", 12, "bold"))
load_button.pack(side=tk.LEFT, padx=5)

create_image_button = tk.Button(frame_top, text="Create Combined Image", command=savep, bg="#28a745", fg="white", font=("Arial", 12, "bold"))
create_image_button.pack(side=tk.LEFT, padx=5)

text_frame = tk.Frame(root)
text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

text_output = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Consolas", 12), bg="#ffffff", fg="#333333", bd=2, relief="groove")
text_output.pack(fill=tk.BOTH, expand=True)

loading_screen = tk.Label(root, text="Processing...", font=("Arial", 14, "bold"))
loading_screen.pack_forget()  # Initially hidden

# Image display setup
img_label = tk.Label(root)
img_label.pack(pady=20)
root.mainloop()
