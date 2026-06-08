
import inspect
import json

from dotenv import load_dotenv
import httpx
from openai import OpenAI
import os

first_tools = [
    # Tool 1 - Get Exchange Rate
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the current exchange rate of a base currency and target currency",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "description": "The base currency for exchange rate calculations, i.e. USD, EUR, RUB",
                    },
                    "target_currency": {
                        "type": "string",
                        "description": "The target currency for exchange rate calculations, i.e. USD, EUR, RUB",
                    },
                    "date": {
                        "type": "string",
                        "description": "A specific day to reference, in YYYY-MM-DD format.",
                    },
                },
                "required": ["base_currency", "target_currency"],
            },
        },
    },
  
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": "Get internet search results for real time information",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The query to search the web for",
                    }
                },
                "required": ["search_query"],
            },
        },
    },
]
load_dotenv()

client = OpenAI(api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1",

)
messages=[{"role": "user","content": "How much is a indian rupee cost in japan?"}]

response=client.chat.completions.create(
    messages= messages,
    model=os.getenv("LLM_MODEL"),
    tools=first_tools,
    tool_choice="auto",
       
)

def pprint_response(response):
    print("--- Full Response ---\n")
    print(response, "\n")
    
    print("--- Chat Completion Message ---\n")
    print(response.choices[0].message, "\n")
    
    if response.choices[0].message.tool_calls:
        for i in range(0, len(response.choices[0].message.tool_calls)):
            print(f"--- Tool Call {i+1} ---\n")
            print(f"Function: {response.choices[0].message.tool_calls[i].function.name}\n")
            print(f"Arguments: {response.choices[0].message.tool_calls[i].function.arguments}\n")


def exhchange_rates(base_currency : str,target_currency:str,date : str="latest"):
    url=f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base_currency.lower()}.json"
    response=httpx.get(url)
    if response.status_code==200:
       return response.json()
    else:
        raise Exception(f"The link gave an error response {response.status_code}")
    
def function_calling(llm_response : str):
    tool_calls=llm_response.tool_calls
    
    if tool_calls:
        functions={
            "get_exchange_rate":exhchange_rates,
        
        }
        messages.append(llm_response)
        for tool_call in tool_calls:
            function_name=tool_call.function.name
            function_to_call=functions[function_name]
            function_args=json.loads(tool_call.function.arguments)
            
            sig = inspect.signature(function_to_call)
            
            caller_args={
                k:function_args.get(k, v.default)
                for k, v in sig.parameters.items()
                if k in function_args or v.default is not inspect.Parameter.empty
            }
            
            print(f"\n Calling the function {function_to_call} with args {function_args}")
            
            function_response=str(function_to_call(**caller_args))
           
            
            print(f"Function response {function_response}")
            
            tool_stats={
                "tool_call_id":tool_call.id,
                "role":"tool",
                "name":function_name,
                "content":function_response,
            }
            messages.append(tool_stats)
        second_response=client.chat.completions.create(
                model=os.getenv("LLM_MODEL"),
                messages=messages
                
            )
        print(f"llm response {second_response}")
            
            
        print("\n---Formatted LLM Response---")
        print("\n",second_response.choices[0].message.content)
    
function_calling(response)