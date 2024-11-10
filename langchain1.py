from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase 
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
import re

db_uri = f"mysql+mysqlconnector://root@localhost:3306/billmanag"
db = SQLDatabase.from_uri(db_uri)

#llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

def is_query(user_input: str):
  template = """
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
  def get_schema(_):
    return db.get_table_info()
  
  prompt = ChatPromptTemplate.from_template(template)

  #llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed", temperature=0)
  llm = ChatGroq(api_key="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", model="mixtral-8x7b-32768", temperature=0)

  chain =  (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm
    | StrOutputParser()
  )
  x = chain.invoke({"question": user_input })
  return x

def handle_conv(user_input: str):
  template = """
    You are a helpful assistant.
    Users will ask you questions about their expenses based on the data available in the database
    or just chat with you, and you should answer them in a formal way without too much details.

    User question: {question}
  """
  prompt = ChatPromptTemplate.from_template(template)
  #llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed", temperature=0)
  llm = ChatGroq(api_key="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", model="mixtral-8x7b-32768", temperature=0)

  chain = prompt | llm | StrOutputParser()
  return chain.invoke({"question": user_input}),1
  
def get_sql_chain(db, user_id: int):
  template = """
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
    
  prompt = ChatPromptTemplate.from_template(template)
  
  #llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed", temperature=0)
  llm = ChatGroq(api_key="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", model="mixtral-8x7b-32768", temperature=0)
  
  def get_schema(_):
    return db.get_table_info()
  
  def get_user_id(_):
    return user_id
  
  return (
    RunnablePassthrough.assign(schema=get_schema).assign(user_id=get_user_id)
    | prompt
    | llm
    | StrOutputParser()
  )

def get_response(user_query: str, user_id: int):
  
  a = is_query(user_query)
  if a == 0 or "0" in a:
    sql_chain = get_sql_chain(db, user_id)
    
    template = """
      You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
      Based on the table schema below, question, sql query, and sql response, write a natural language response.Do not mention the userid of the user.give the number as it is writen and add LL after it, do not convert any number to united states dollars on your own.Keep your responses very breif and don't go into details.
      Add LL after any amount of money which is the Lebanses currency.
      add , if the number is more than 999 for example is the number is 1000000 wirte it 1,000,000 LL.
      
      <SCHEMA>{schema}</SCHEMA>
      
      SQL Query: <SQL>{query}</SQL>
      User question: {question}
      SQL Response: {response}"""
    
    prompt = ChatPromptTemplate.from_template(template)

    #llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed", temperature=0)
    llm = ChatGroq(api_key="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", model="mixtral-8x7b-32768", temperature=0)
    
    chain = (
      RunnablePassthrough.assign(query=sql_chain).assign(
        schema=lambda _: db.get_table_info(),
        response=lambda vars: db.run(vars["query"]),
      )
      | prompt
      | llm
      | StrOutputParser()
    )

    query = sql_chain.invoke({"question": user_query })
    i1 = query.index("SELECT")
    i2 = query.index("FROM")
    str = query[i1+len("SELECT")+1:i2]
    if "image" in str:
      return query,0
    return chain.invoke({"question": user_query }),1
  else:
    return handle_conv(user_query)