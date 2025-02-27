📜 Notes Summarizer with AI & OCR
🚀 Extract, Summarize & Format Text from Images Using AI
This Python-based Notes Summarizer with AI & OCR allows users to extract text from images using PaddleOCR, summarize and format it using ChatGPT, and generate a structured text-image output for efficient note-taking and studying.

✨ Features
✅ OCR Text Extraction – Uses PaddleOCR to extract text from images.
✅ AI Summarization – Sends extracted text to ChatGPT for a structured, exam-friendly summary.
✅ Formatted Output – Generates an image with the summarized text using Cairo graphics.
✅ Image Combination – Merges the original image with the AI-generated formatted text.
✅ Clipboard Integration – Automatically copies the AI response for quick use.
✅ User-Friendly GUI – Built with Tkinter, featuring file selection and live processing.

🖥️ How It Works
1️⃣ Select an image containing handwritten or printed text.
2️⃣ OCR extracts text using PaddleOCR.
3️⃣ ChatGPT formats and summarizes the extracted text (via browser automation).
4️⃣ A formatted text image is generated using Cairo.
5️⃣ The original and text images are combined into a single output.
6️⃣ Save the final image for easy reference and study.

📸 Screenshots
![temp_text_image](https://github.com/user-attachments/assets/b7a506d2-4bd1-406c-ae9f-9f59c5e57759)
the above summary is of an error i encountered in the process of devoloping this app


🛠️ Installation
🔹 Prerequisites
Ensure you have Python 3.8+ installed.
🔹 Install Required Dependencies
pip install tkinter pillow cairo paddleocr pyperclip pychrome
🔹 Run the Application
python main.py


🔗 Technologies Used
Python 
Tkinter (GUI) 
PaddleOCR (Optical Character Recognition) 
ChatGPT (via browser automation) 
PyChrome (Web automation) 
Pillow (Image processing) 
Cairo (Graphics & Text Rendering) 


🔧 Future Enhancements
🚀 Replace browser automation with ChatGPT API for direct AI responses.
📱 Develop a mobile version using Flutter & Firebase.
☁️ Deploy as a web app using Flask or FastAPI.
📝 Add speech-to-text functionality for voice-based notes.
💾 Implement a backend to store extracted and summarized data for future reference and searchability.


📜 License
This project is licensed under the MIT License.
