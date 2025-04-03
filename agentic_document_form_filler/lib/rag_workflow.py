import json
import logging
import os
import shutil

import nest_asyncio
from llama_index.core import (  # StorageContext,; load_index_from_storage,
    Settings,
    VectorStoreIndex,
)
from llama_index.core.workflow import (
    Context,
    HumanResponseEvent,
    InputRequiredEvent,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_parse import LlamaParse

from agentic_document_form_filler.events.feedback_event import FeedbackEvent
from agentic_document_form_filler.events.generate_questions_event import (
    GenerateQuestionsEvent,
)
from agentic_document_form_filler.events.parse_form_event import ParseFormEvent
from agentic_document_form_filler.events.query_event import QueryEvent
from agentic_document_form_filler.events.response_event import ResponseEvent
from agentic_document_form_filler.lib.config import default_config as config

logger = logging.getLogger(config.name)
nest_asyncio.apply()

Settings.embed_model = HuggingFaceEmbedding(
    model_name=config.embedding_model,
)


class RAGWorkflow(Workflow):
    """
    A workflow that uses a RAG (retrieval-augmented generation) approach
    to fill in a job application form using a resume document.
    The workflow is divided into several steps:
    1. Set up the workflow by loading the resume document and
       creating a query engine to answer questions about it.
    2. Parse the application form using LlamaParse and return a list of
         fields to fill in.
    3. Generate questions for each of the fields to fill in.
    4. Ask the query engine a question about the resume document.
    5. Combine the responses to the questions into a single response
       to the application form. Then ask the human for feedback on
       the filled form.
    6. Get feedback from the human on the filled form. If the human
       says everything is OK, stop the workflow. Otherwise, return
       the feedback to the previous step.
    The workflow is designed to be run in an asynchronous environment.
    The workflow uses the Groq LLM to answer questions about the
    resume document and the LlamaParse library to parse the
    application form.
    """

    storage_dir = config.storage_dir
    llm = Groq(model=config.groq_model, api_key=config.groq_api_key)
    query_engine: VectorStoreIndex

    @step
    async def set_up(self, ev: StartEvent) -> ParseFormEvent:
        """
        Set up the workflow by loading the resume document and
        creating a query engine to answer questions about it.
        The resume document is stored in the storage directory.
        If the document is already there, load it from storage.
        If not, parse it and store it in the storage directory.
        The query engine is created using the Groq LLM.
        The workflow is then passed to the next step to parse the
        application form.
        """

        if not ev.resume_file:
            raise ValueError("No resume file provided")

        if not ev.application_form:
            raise ValueError("No application form provided")

        # define the LLM to work with
        self.llm = Groq(model=config.groq_model, api_key=config.groq_api_key)

        # # ingest the data and set up the query engine
        # if os.path.exists(self.storage_dir):
        #     # you've already ingested the resume document
        #     storage_context = StorageContext.from_defaults(
        #         persist_dir=self.storage_dir)
        #     index = load_index_from_storage(storage_context)
        # else:
        # parse and load the resume document
        documents = LlamaParse(
            api_key=config.llama_index_api_key,
            base_url=os.getenv("LLAMA_CLOUD_BASE_URL"),
            result_type="markdown",
            content_guideline_instruction="This is a resume, gather "
            "related facts together and format it as bullet points "
            "with headers",
        ).load_data(ev.resume_file)

        # embed and index the documents
        index = VectorStoreIndex.from_documents(
            documents, embed_model=Settings.embed_model
        )

        # Always create fresh index instead of using stored one
        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)

        index.storage_context.persist(persist_dir=self.storage_dir)

        # create a query engine
        self.query_engine = index.as_query_engine(llm=self.llm,
                                                  similarity_top_k=5)

        # let's pass the application form to a new step to parse it
        return ParseFormEvent(application_form=ev.application_form)

    # form parsing
    @step
    async def parse_form(
        self, ctx: Context, ev: ParseFormEvent
    ) -> GenerateQuestionsEvent:
        """
        Parse the application form using LlamaParse and return a list of
        fields to fill in.
        """
        parser = LlamaParse(
            api_key=config.llama_index_api_key,
            base_url=os.getenv("LLAMA_CLOUD_BASE_URL"),
            result_type="markdown",
            content_guideline_instruction="This is a job application form. "
            "Create a list of all the fields that need to be filled in.",
            formatting_instruction="Return bulleted list of the fields ONLY.",
        )

        # get the LLM to convert the parsed form into JSON
        result = parser.load_data(ev.application_form)[0]

        raw_json = self.llm.complete(
            f"""This is a parsed form. Convert it into a JSON object containing
            only the list of fields to be filled in, in the form
            {{ fields: [...] }}. <form>{result.text}</form>. Return a valid
            JSON object only, no markdown code blocks or other formatting."""
        )

        # Clean the response by removing markdown code block markers
        json_str = raw_json.text.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1]  # Remove first line
        if json_str.endswith("```"):
            json_str = json_str.rsplit("\n", 1)[0]  # Remove last line

        json_str = json_str.strip()
        data = json.loads(json_str)
        fields = data["fields"]

        await ctx.set("fields_to_fill", fields)

        return GenerateQuestionsEvent()

    # generate questions
    @step
    async def generate_questions(
        self, ctx: Context, ev: GenerateQuestionsEvent | FeedbackEvent
    ) -> QueryEvent:
        """
        Generate questions for each of the fields to fill in.
        If the human has provided feedback, include it in the
        questions.
        """

        # get the list of fields to fill in
        fields = await ctx.get("fields_to_fill")

        # generate one query for each of the fields, and fire them off
        for field in fields:
            question = f"""How would you answer this question about the
            candidate? <field>{field}</field>"""

            if hasattr(ev, "feedback"):
                question += f"""
                \nWe previously got feedback about how we answered the
                questions. It might not be relevant to this particular field,
                but here it is: <feedback>{ev.feedback}</feedback>
                """

            ctx.send_event(QueryEvent(field=field, query=question))

        # store the number of fields so we know how many to wait for later
        await ctx.set("total_fields", len(fields))
        return

    @step
    async def ask_question(self, ev: QueryEvent) -> ResponseEvent:
        """
        Ask the query engine a question about the resume document.
        The question is about a specific field in the application form.
        The response is a string.
        """
        response = self.query_engine.query(
            f"""This is a question about the
                                           specific resume we have in our
                                           database: {ev.query}"""
        )
        return ResponseEvent(field=ev.field, response=response.response)

    # Get feedback from the human
    @step
    async def fill_in_application(
        self, ctx: Context, ev: ResponseEvent
    ) -> InputRequiredEvent:
        """
        Combine the responses to the questions into a single
        response to the application form. Then ask the human for
        feedback on the filled form.
        """
        # get the total number of fields to wait for
        total_fields = await ctx.get("total_fields")

        responses = ctx.collect_events(ev, [ResponseEvent] * total_fields)

        if responses is None:
            return None  # do nothing if there's nothing to do yet

        # we've got all the responses!
        response_list = "\n".join(
            "Field:" + r.field + "\n" + "Response:" + r.response
            for r in responses
        )

        result = self.llm.complete(
            f"""
            You are given a list of fields in an application form and
            responses to questions about those fields from a resume.
            Combine the two into a list of fields and succinct, factual
            answers to fill in those fields.
            <responses>
            {response_list}
            </responses>
        """
        )

        # save the result for later
        await ctx.set("filled_form", str(result))

        # Fire off the feedback request
        return InputRequiredEvent(
            prefix="How does this look? Give me any feedback you have on any"
            "of the answers.",
            result=result,
        )

    # Accept the feedback when a HumanResponseEvent fires
    @step
    async def get_feedback(
        self, ctx: Context, ev: HumanResponseEvent
    ) -> FeedbackEvent | StopEvent:
        """
        Get feedback from the human on the filled form. If the human
        says everything is OK, stop the workflow. Otherwise, return
        the feedback to the previous step.
        """

        result = self.llm.complete(
            f"""
            You have received some human feedback on the form-filling task
            you've done. Does everything look good, or is there more work to
            be done?
            <feedback>
            {ev.response}
            </feedback>
            If everything is fine, respond with just the word 'OKAY'.
            If there's any other feedback, respond with just the
            word 'FEEDBACK'.
        """
        )

        verdict = result.text.strip()

        logger.info(f"LLM says the verdict was {verdict}")
        if verdict == "OKAY":
            return StopEvent(result=await ctx.get("filled_form"))

        return FeedbackEvent(feedback=ev.response)
