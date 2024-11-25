import streamlit as st
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent, create_react_agent
from langchain import hub
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from io import StringIO


# Show title and description.
st.title("💬 Chatbot")

syllabus_corpus_path = "https://raw.githubusercontent.com/AdobakBU/Course-Advisor_Chatbot-IS883/main/data/"

def load_pdf_and_csv(folder_path): #our function to chunk the data
    filenames = ["example.pdf", "example.csv"]  # Replace with actual filenames in your folder
    chunks = []
    
    for filename in filenames:
        file_url = f"{folder_path}{filename}"  # Construct the full file URL
        
        # Handle PDF files
        if filename.endswith('.pdf'):
            try:
                response = requests.get(file_url)
                response.raise_for_status()  # Raise an error for failed requests
                
                # Process the PDF
                with fitz.open(stream=response.content, filetype="pdf") as doc:
                    for page_number in range(len(doc)):
                        page = doc.load_page(page_number)
                        text = page.get_text()
                        # Create a Document object for each chunk
                        chunks.append(Document(page_content=text, metadata={"source": filename, "page": page_number + 1}))
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        # Handle CSV files
        #elif filename.endswith('.csv'):
        #   try:
        #        response = requests.get(file_url)
        #        response.raise_for_status()  # Raise an error for failed requests
                
                # Process the CSV
        #        csv_file = StringIO(response.text)  # Create an in-memory file-like object
        #        reader = csv.reader(csv_file)
        #        for row_number, row in enumerate(reader):
        #            text = ', '.join(row)  # Combine CSV fields into a single string
        #            # Create a Document object for each row
        #            chunks.append(Document(page_content=text, metadata={"source": filename, "row": row_number + 1}))
        #    except Exception as e:
        #        print(f"Error loading {filename}: {e}")
    
    return chunks
### Important part.
# Create a session state variable to flag whether the app has been initialized.
# This code will only be run first time the app is loaded.
if "memory" not in st.session_state: ### IMPORTANT.
    model_type="gpt-4o-mini"

    # initialize the momory
    max_number_of_exchanges = 10
    st.session_state.memory = ConversationBufferWindowMemory(memory_key="chat_history", k=max_number_of_exchanges, return_messages=True) ### IMPORTANT to use st.session_state.memory.

    # LLM
    chat = ChatOpenAI(openai_api_key=st.secrets["OpenAI_API_KEY"], model=model_type)

    # tools
    from langchain.agents import tool
    from datetime import date
    @tool
    def datetoday(dummy: str) -> str:
        """Returns today's date, use this for any \
        questions that need today's date to be answered. \
        This tool returns a string with today's date.""" #This is the desciption the agent uses to determine whether to use the time tool.
        return "Today is " + str(date.today())

    tools = [datetoday]
    
    # Now we add the memory object to the agent executor
    # prompt = hub.pull("hwchase17/react-chat")
    # agent = create_react_agent(chat, tools, prompt)
    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    agent = create_tool_calling_agent(chat, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(agent=agent, tools=tools,  memory=st.session_state.memory, verbose= True)  # ### IMPORTANT to use st.session_state.memory and st.session_state.agent_executor.

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.memory.buffer:
    # if (message.type in ["ai", "human"]):
    st.chat_message(message.type).write(message.content)

# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if prompt := st.chat_input("What is up?"):
    
    # question
    st.chat_message("user").write(prompt)

    # Generate a response using the OpenAI API.
    response = st.session_state.agent_executor.invoke({"input":prompt})['output']

    # response
    st.chat_message("assistant").write(response)
    # st.write(st.session_state.memory.buffer)
