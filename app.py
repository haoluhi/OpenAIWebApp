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
azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
azure_search_key = os.getenv("AZURE_SEARCH_KEY")
azure_search_index = os.getenv("AZURE_SEARCH_INDEX")

# Create an OpenAI client
azureOpenApiClient = AzureOpenAI(
    azure_endpoint = azure_oai_endpoint, 
    api_key=azure_oai_key,  
    api_version="2024-02-15-preview"
    )

# Configure your data source
extension_config = dict(dataSources = [  
    { 
        "type": "AzureCognitiveSearch", 
        "parameters": { 
            "endpoint":azure_search_endpoint, 
            "key": azure_search_key, 
            "indexName": azure_search_index,
        }
    }]
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
        # return render_template('result.html', extracted_text=text, response_text=response_text)
        return render_template('result.html', response_text=response_text)
        
#         response_text = """
#         Write-up from the Product Manager
# This mockup deposit advertisement has a couple of compliance issues that the AI should be able to detect based on the checklist from the previous document:
# 	•	The advertisement fails to use the full term "annual percentage yield" or spell out the abbreviation "APY" at least once, as required by the checklist.
# 	•	The ad doesn't include a statement that the rate may change after the account is opened, which is necessary for variable rate accounts (assuming this is a variable rate account, which is common for money market accounts).
# These omissions violate the requirements outlined in the checklist:
# 	•	"If the ad states a rate of return, does it state the rate as an 'annual percentage yield', using that term? The abbreviation 'APY' may be used, provided that the term 'annual percentage yield' is stated at least once in the ad."
# 	•	"For variable rate accounts, a statement that the rate may change after the account is opened?"
# The rest of the advertisement follows most of the other guidelines, such as including the minimum balance to open the account, mentioning that fees could reduce earnings, and including the "Member FDIC" designation.
#  
# This PoC will demonstrate that, given compliance rules, decision trees, etc., that the AI can analyze a document, make judgments/decisions, and ideally even make the corrections for the user in a few seconds.
#          """
        
        # return render_template('result.html', extracted_text=text, response_text=response_text)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_openai_response(user_message, model, client):
    messages =[
         {"role": "system", "content": "You are an AI assistant that examines content provided against the information in marketingcompliancechecklistvector and notify the user about the compliant issues in the information provided"},
         {"role": "user", "content": user_message},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000,
        extra_body={
        "data_sources":[
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": azure_search_endpoint,
                    "index_name": azure_search_index,
                    "authentication": {
                        "type": "api_key",
                        "key": azure_search_key,
                    }
                }
            }
        ],
    } 
    )
    
    print("Response: " + response.choices[0].message.content + "\n")
    
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True)
