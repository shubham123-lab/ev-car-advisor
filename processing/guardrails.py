from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")

SUPPORTED_CARS = [
    "Tata Sierra EV", "Tata Harrier EV",
    "Mahindra BE 6", "Mahindra XEV 9e", "Mahindra XEV 9s"
]

car_detect_prompt = PromptTemplate(
    template="""
We have data ONLY for these 5 EV cars:
{car_list}

Recent conversation:
{chat_history}

Current question: {question}

Using the conversation context, determine:
- If ONE car from the list is being discussed (even if not named in the
  current question but clear from context), respond with ONLY that car name.
- If TWO cars from the list are being compared, respond with: COMPARE: [Car A], [Car B]
- If the question is a follow-up about cars from our list but unclear which
  one, respond with: FOLLOWUP
- If a car NOT in the list is mentioned, or the topic is unrelated to these
  cars, respond with ONLY: NOT_COVERED
- If it's a general EV question not about a specific car, respond with
  ONLY: GENERAL_EV

Answer:
""",
    input_variables=["question", "car_list", "chat_history"]
)

car_detect_chain = car_detect_prompt | llm | StrOutputParser()

fallback_prompt = PromptTemplate(
    template="""
Generate a short, friendly message in the SAME language as the user's
original question below. The message should say (adapt naturally,
don't translate word-for-word):

"I'm an EV Car Advisor, and right now I only have detailed data on
these 5 cars. Which one would you like to know about?"

Then list these 5 cars as a numbered list. IMPORTANT: Keep the car
names in the list EXACTLY as given below, in English/Roman script -
do NOT translate or transliterate the car names into any other
language or script, even if the rest of your message is in a
different language.

{car_list}

User's original question (match this language/script for your message,
but NOT for the car names): {question}

Message:
""",
    input_variables=["question", "car_list"]
)

fallback_chain = fallback_prompt | llm | StrOutputParser()


def handle_query(question, chat_history=None):
    car_list_str = "\n".join(f"- {c}" for c in SUPPORTED_CARS)

    history_str = "No previous conversation."
    if chat_history:
        history_str = "\n".join(
            f"{m['role']}: {m['content'][:300]}" for m in chat_history[-4:]
        )

    detection = car_detect_chain.invoke({
        "question": question,
        "car_list": car_list_str,
        "chat_history": history_str
    }).strip()

    if detection == "NOT_COVERED":
        numbered_list = "\n".join(f"{i+1}. {c}" for i, c in enumerate(SUPPORTED_CARS))
        message = fallback_chain.invoke({
            "question": question,
            "car_list": numbered_list
        })
        return {"status": "not_covered", "response": message}

    return {"status": "proceed", "detected_car": detection}


if __name__ == "__main__":
    test_questions = [
        "Sierra EV ki range kya hai?",
        "Grand Vitara ke baare me batao",
        "iPhone 17 kab launch hoga?",
    ]

    for q in test_questions:
        result = handle_query(q)
        print(f"Q: {q}")
        print(f"-> {result}")
        print("---")