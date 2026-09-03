from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = FAISS.load_local("../data/faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 12})

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

prompt = PromptTemplate(
    template="""
You are an experienced EV advisor helping an Indian car buyer. You have
access to real owner reviews and expert content below.

Your response style:
- Synthesize across sources — find patterns, not just quote facts
- Lead with the specific answer (numbers, verdict), then explain why
- Mention trade-offs honestly, not just positives
- If owners disagree, say so and explain both sides
- Keep it conversational, like an expert friend explaining
- End with a natural follow-up question or suggestion of what to
  explore next

Never mention "according to the context" or cite sources.

Context:
{context}

Question: {question}
""",
    input_variables=['context', 'question']
)

def format_docs(retrieved_docs):
    return "\n\n".join(doc.page_content for doc in retrieved_docs)

parser = StrOutputParser()

parallel_chain = RunnableParallel({
    'context': retriever | RunnableLambda(format_docs),
    'question': RunnablePassthrough()
})

rag_chain = parallel_chain | prompt | llm | parser

if __name__ == "__main__":
    question = "Sierra EV ki real world range kitni hai?"
    answer = rag_chain.invoke(question)
    print(answer)