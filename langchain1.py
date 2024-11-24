from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase 
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
import os
import re
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Database configuration
db_uri = f"mysql+mysqlconnector://root@localhost:3306/billmanag"
db = SQLDatabase.from_uri(db_uri)

# LLM Configuration
def get_llm(temperature=0):
    """Get configured LLM instance"""
    return ChatGroq(
        api_key=os.getenv("DB_groq_API"),
        model="mixtral-8x7b-32768",
        temperature=temperature
    )

# Templates
QUERY_CLASSIFIER_TEMPLATE = """
    You are interacting with a user who is asking you questions about his expenses based on a data available stored in the database or just having normal conversation with you.
    Based on the table schema bellow, write 0 if the user is asking questions about the databse or write 1 if its just a normal conversational question.

    <SCHEMA>{schema}</SCHEMA>

    Write only 0 or 1 and nothing else. Do not wrap the number in any other text, not even backticks.

    For example:
    Question: how much have i spent?
    Response: 0
    Question: how many tawouk sandwiches have i bought?
    Response: 0
    Question: how much have i spent on taouk sandwiches?
    Response: 0
    Question: how much have i spent in total last month?
    Response: 0
    Question: how much have i spent since 2022?
    Response: 0
    Question: how much have i spent by category?
    Response: 0
    Question: how much have i spent at roadster diner?
    Response: 0
    Question: hi
    Response: 1
    Question: hello
    Response: 1
    Question: where is paris located?
    Response: 1

    Your turn:

    Question: {question}
    Response:
"""

CONVERSATION_TEMPLATE = """
    You are a helpful assistant.
    Users will ask you questions about their expenses based on the data available in the database
    or just chat with you, and you should answer them in a formal way without too much details.

    User question: {question}
"""

SQL_QUERY_TEMPLATE = """
    You are a data analyst. You are interacting with a user who is asking you questions about his expenses based on the data available in the database.
    Based on the table schema below, write a SQL query that would answer the user's question. 
    whenever the user asks about his total spending give him a detailed answer.
    Don't change the methode used in the queries given as example.
    Don't use \ when generating the query.
    Don't use _ when generating the query.
    For example:
    WRONG: total\_spent
    RIGHT: totalspent
    WRONG: business\_name
    RIGHT: businessname
    
    <SCHEMA>{schema}</SCHEMA>
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    
    For example:
    Questioin: give me a detailed report of my spendings.
    Question: how much have i spent in total?
    SQL Query: SELECT Total,businessname,Date,category From billinfo WHERE userid = {user_id};
    Question: how much have i spent on kabab?
    SQL Query: SELECT SUM(price) FROM billitems WHERE name like '%kabab%' and userid = {user_id};
    Question: how much have i spent on tawouk?
    SQL Query: SELECT SUM(price) FROM billitems WHERE  name LIKE '%tawouk%' and userid = {user_id};
    Question: how much have i spent at roadster diner?
    SQL Query: SELECT SUM(total) FROM billinfo WHERE businessname LIKE '%roadster diner%' and userid = {user_id};
    Question: how much have i spent since 2022?
    SQL Query: SELECT SUM(total) FROM billinfo WHERE date >= '2022-01-01' and userid = {user_id};
    Question: how much have i spent at restaurant?
    SQL Query: SELECT SUM(total) FROM billinfo WHERE category = 'Restaurant' and userid = {user_id};
    
    Your turn:
    
    Question: {question}
    SQL Query:
"""

RESPONSE_TEMPLATE = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.Do not mention the userid of the user.give the number as it is writen and add LL after it, do not convert any number to united states dollars on your own.Keep your responses very breif and don't go into details.
    Add LL after any amount of money which is the Lebanses currency.
    add , if the number is more than 999 for example is the number is 1000000 wirte it 1,000,000 LL.
    
    <SCHEMA>{schema}</SCHEMA>
    
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}
"""

def create_chain(template, assign_vars=None):
    """Create a chain with the given template and optional variable assignments"""
    prompt = ChatPromptTemplate.from_template(template)
    llm = get_llm()
    
    if assign_vars:
        chain = (
            RunnablePassthrough.assign(**assign_vars)
            | prompt
            | llm
            | StrOutputParser()
        )
    else:
        chain = prompt | llm | StrOutputParser()
    
    return chain

def is_query(user_input: str):
    """Determine if the input is a database query or conversation"""
    def get_schema(_):
        return db.get_table_info()
    
    chain = create_chain(
        QUERY_CLASSIFIER_TEMPLATE,
        {"schema": get_schema}
    )
    return chain.invoke({"question": user_input})

def handle_conv(user_input: str):
    """Handle conversational inputs"""
    chain = create_chain(CONVERSATION_TEMPLATE)
    return chain.invoke({"question": user_input}), 1

def get_sql_chain(db, user_id: int):
    """Create SQL query chain"""
    def get_schema(_):
        return db.get_table_info()
    
    def get_user_id(_):
        return user_id
    
    return create_chain(
        SQL_QUERY_TEMPLATE,
        {
            "schema": get_schema,
            "user_id": get_user_id
        }
    )

def get_response(user_query: str, user_id: int):
    """Process user query and return appropriate response"""
    a = is_query(user_query)
    
    if a == "0" or "0" in a:
        sql_chain = get_sql_chain(db, user_id)
        query = sql_chain.invoke({"question": user_query})
        
        # Check if query is requesting image
        i1 = query.index("SELECT")
        i2 = query.index("FROM")
        select_clause = query[i1+len("SELECT")+1:i2]
        if "image" in select_clause:
            return query, 0
            
        # Create response chain
        chain = create_chain(
            RESPONSE_TEMPLATE,
            {
                "query": lambda _: sql_chain.invoke({"question": user_query}),
                "schema": lambda _: db.get_table_info(),
                "response": lambda vars: db.run(vars["query"])
            }
        )
        
        return chain.invoke({"question": user_query}), 1
    else:
        return handle_conv(user_query)