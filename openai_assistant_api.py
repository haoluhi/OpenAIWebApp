# https://learn.microsoft.com/en-us/azure/ai-services/openai/assistants-reference?tabs=python

import os
import time
import json
from openai import AzureOpenAI
  
client = AzureOpenAI(
    azure_endpoint = os.getenv("AZURE_OAI_ENDPOINT"),
    api_key= os.getenv("AZURE_OAI_KEY"),
    api_version="2024-02-15-preview"
)

# list assistants
my_assistants = client.beta.assistants.list(
    order="desc",
    limit="20",
)
print(my_assistants.data)

# Example retrieve assistant
# asst_7gh7ePNufIuMsWVY0Nn4Gkfj is one of the assistants
assistant_id = "asst_7gh7ePNufIuMsWVY0Nn4Gkfj"
assistant = client.beta.assistants.retrieve(assistant_id)
print(assistant)
print(assistant.id)

# Create a thread
thread = client.beta.threads.create()

# Add a user question to the thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content='''Is there anything to change or improve for the following documents:
"
Ralph W Savings Bank
Lock In Great Rates with Our CDs!
Secure your financial future with Ralph W Savings Bank's high-yield Certificates of Deposit!
Unbeatable CD Rates:
• 12-month CD: 2.75% APY
• 24-month CD: 3.00% APY
• 36-month CD: 3.25% APY
Why Choose Our CDs?
• FDIC insured up to $250,000
• Guaranteed returns
• Flexible terms from 3 months to 5 years
• Low minimum deposit of just $1,000
Open your CD today and watch your savings grow!
Visit any Ralph W Savings Bank branch or call 1-888-RALPHWB to get started.
Rates current as of August 1, 2024. $1,000 minimum balance to open and obtain APY.
Ralph W Savings Bank - Member FDIC | Equal Housing Lender
"
''' # Replace this with your prompt
)

        
# Run the thread
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id
)

# Looping until the run completes or fails
while run.status in ['queued', 'in_progress', 'cancelling']:
    time.sleep(1)
    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )

if run.status == 'completed':
  messages = client.beta.threads.messages.list(
    thread_id=thread.id
  )
  print(messages)
  print([messages.data[0].content[0].text.value])
elif run.status == 'requires_action':
  # the assistant requires calling some functions
  # and submit the tool outputs back to the run
  pass
else:
  print(run.status)
