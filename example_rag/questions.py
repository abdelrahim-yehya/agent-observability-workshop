"""Scripted questions for the course RAG app, with expectations written BEFORE any run.

expected      reference answer taken from docs/course*_script.txt (the source named in `source`)
expected_tools tools a correct run should call (empty list = none needed)
Questions of one session id form one conversation (the app keeps the last 2 messages as history).
"""

SESSIONS = {
    "S1": [dict(
        q="Who is the instructor of the MCP course?",
        expected="Elie Schoppik.",
        expected_tools=["search_course_content"],
        source="course2_script.txt header (Course Instructor)",
    )],
    "S2": [dict(
        q="Who teaches the Advanced Retrieval for AI with Chroma course?",
        expected="Anton Troynikov.",
        expected_tools=["search_course_content"],
        source="course3_script.txt header (Course Instructor)",
    )],
    "S3": [dict(
        q="In the Advanced Retrieval course, what is query expansion with generated answers?",
        expected=("Take the query, prompt an LLM to generate a hypothetical (imagined) answer to it, concatenate the "
                  "query with that answer, and use the result as the new query for the retrieval system."),
        expected_tools=["search_course_content"],
        source="course3_script.txt, Lesson 3: Query Expansion",
    )],
    "S4": [dict(
        q="What does cross encoder re-ranking do after retrieval?",
        expected=("The retrieved results are passed together with the query to a re-ranking model, which scores each "
                  "result's relevance to the query; the highest-scoring results are kept as most relevant."),
        expected_tools=["search_course_content"],
        source="course3_script.txt, Lesson 4: Cross Encoder Re Ranking",
    )],
    "S5": [dict(
        q="Why does the prompt compression lesson say prompt compression is valuable?",
        expected=("It cuts cost and latency: using the full context window of large-context LLMs is expensive "
                  "(e.g. 10 USD per million tokens at high volume) and slower; useful for RAG and agentic systems."),
        expected_tools=["search_course_content"],
        source="course4_script.txt, Lesson 5: Prompt Compression",
    )],
    "S6": [dict(
        q="List the lessons of the Prompt Compression and Query Optimization course.",
        expected=("Lessons 0 to 6: Introduction, Vanilla Vector Search, Filtering With Metadata, Projections, "
                  "Boosting, Prompt Compression, Conclusion."),
        expected_tools=["get_course_outline"],
        source="course4_script.txt lesson headers",
    )],
    "S7": [dict(
        q="What do the courses say about deploying MCP servers on Kubernetes?",
        expected=("Nothing: 'kubernetes' does not appear in any transcript. A correct answer says the course "
                  "materials do not cover it."),
        expected_tools=["search_course_content"],
        source="grep over docs/course*_script.txt: 0 matches",
    )],
    "S8": [dict(
        q="What is the capital of Australia?",
        expected="Canberra, answered from general knowledge without searching (system prompt: general knowledge needs no tool).",
        expected_tools=[],
        source="system prompt rule for general-knowledge questions",
    )],
    "S9": [
        dict(q="My project is called Atlas and it uses Chroma as its vector database.",
             expected="Acknowledge; nothing to look up.", expected_tools=[],
             source="conversation turn 1"),
        dict(q="What is a cross encoder re-ranker, in the Advanced Retrieval course?",
             expected="A model that scores each retrieved result against the query, used to re-rank results.",
             expected_tools=["search_course_content"], source="course3_script.txt, Lesson 4"),
        dict(q="What is my project called, and which vector database does it use?",
             # Before the run I predicted the app would forget (MAX_HISTORY=2 read as 2 messages). Wrong: the app keeps
             # 2 exchanges, so turn 1 is still in its history at turn 3. Expectation corrected to the user-facing truth.
             expected="Atlas, using Chroma.",
             expected_tools=[], source="conversation turn 1 (user-stated fact)"),
        dict(q="No, I told you that at the start. Why did you forget?",
             expected="Apologise or explain; user is frustrated.", expected_tools=[],
             source="conversation turn 4 (user frustration)"),
    ],
}
