import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
llm = ChatGroq(model='llama-3.3-70b-versatile', api_key=os.getenv('GROQ_API_KEY'), temperature=0.2, max_tokens=2048)
print(llm.invoke('say hi').content)