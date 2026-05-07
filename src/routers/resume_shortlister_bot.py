from fastapi import APIRouter
from src.schema.bot_schema import ChatRequest, ChatResponse
#from src.services.retrieval import retrieve_chunks, generate_answer
from src.services.hybrid_retrieval import retrieve_final_chunks, generate_answer
from src.services.query_intent_detection import parse_query_llm, get_resumes_for_download, format_download_response, search_resumes
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    query = request.question.lower()

    parsed = parse_query_llm(query)
    print("parsed_llm````````````````````````````````````",parsed)
    intent = parsed.get("intent")
    filters = parsed.get("filters", {})

    #1. DOWNLOAD FLOW
    if intent == "download":
        resumes = get_resumes_for_download(request.selected_resume_ids)
        print("resume for download``````````````````````````````",resumes)
        return ChatResponse(
            answer=format_download_response(resumes),  # string goes here
            candidates=[],
            used_resume_ids=[]
        )

    #2. FILTER FLOW
    elif intent == "filter":
        resumes = search_resumes(filters)
        print("filter resume for download``````````````````````````````",resumes)
        return ChatResponse(
            answer=format_download_response(resumes),  # string goes here
            candidates=[],
            used_resume_ids=[]
        )
    
    else:
        chunks = retrieve_final_chunks(
            request.question,
            request.selected_resume_ids
        )
        print("retrieved_chunks``````````````````````````````````````",chunks)
        answer, candidates = generate_answer(
            request.question,
            chunks
        )

        return ChatResponse(
            answer=answer,
            candidates=candidates,
            used_resume_ids=request.selected_resume_ids or []
        )

