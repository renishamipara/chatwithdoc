from flask import Flask, render_template, request, redirect, url_for, jsonify

import PyPDF2
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key="AIzaSyAqxVIKyLPplBCNp_QLXPF0T1gAmuh7wbk")

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)
initial_summary_generated = False
pdf_text = ""

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global initial_summary_generated, pdf_text  # Uncomment this line

    if request.method == 'POST':
        try:
            print("Received POST request")
            
            # if 'file' not in request.files:
            #     print("No file part in the request")
            #     return jsonify({"error": "No file part"}), 400

            # if 'file' in request.files:
            file = request.files['file']


            if file.filename != '':
                pdf_text = extract_text_from_pdf(file)

                if not initial_summary_generated:
                    print("Generating initial summary")
                    # Generate summary using the language model for the first time
                    convo = model.start_chat(history=[])
                    convo.send_message(pdf_text + "Summerise the above")
                    model_response = convo.last.text
                    initial_summary_generated = True
            print("Returning response")
            return jsonify({"extracted_text": pdf_text, "model_response": model_response})    

        except Exception as e:
            print(f"Exception: {str(e)}")  # Log the exception for debugging
            return jsonify({"error": str(e)}), 500

    # Handle GET request (render your HTML template)
    return render_template('home.html', user_question="", model_response="", extracted_text="")

@app.route('/userQues', methods=['POST'])
def chat():
    try:
        user_question = request.form['user_question']
        convo = model.start_chat(history=[])
        response = convo.send_message(pdf_text + " Use above text and give the following question answer: " + user_question)
        model_response = convo.last.text
        return jsonify({"model_response": model_response})
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500

def extract_text_from_pdf(file):
    text = ""
    with file.stream as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

    

if __name__ == '__main__':
    app.run(debug=True)