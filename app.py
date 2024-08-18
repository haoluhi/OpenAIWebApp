import os
from flask import Flask, request, render_template, redirect, url_for
import fitz  # PyMuPDF
from dotenv import load_dotenv
from openai import AzureOpenAI

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Azure OpenAI configuration
# Get configuration settings 
load_dotenv()
azure_oai_endpoint = os.getenv("AZURE_OAI_ENDPOINT")
azure_oai_key = os.getenv("AZURE_OAI_KEY")
azure_oai_deployment = os.getenv("AZURE_OAI_DEPLOYMENT")

# Create an OpenAI client
azureOpenApiClient = AzureOpenAI(
    azure_endpoint = azure_oai_endpoint, 
    api_key=azure_oai_key,  
    api_version="2024-02-15-preview"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Extract text from PDF
        text = extract_text_from_pdf(filepath)

        # Send text to Azure OpenAI
        response_text = get_openai_response(
                                    user_message = text, 
                                    model=azure_oai_deployment, 
                                    client=azureOpenApiClient
                                    )
        
        # Display the extracted text and AI response
        return render_template('result.html', extracted_text=text, response_text=response_text)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_openai_response(user_message, model, client):
    messages =[
         {"role": "system", "content": "You are an AI assistant that acts as advertisement compliance validator"},
         {"role": "user", "content": user_message},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    print("Response: " + response.choices[0].message.content + "\n")
    
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True)
