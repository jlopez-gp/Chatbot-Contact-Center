import time
import pandas as pd
import logging
from openai import AzureOpenAI
from openai.types.beta.threads.run import Run
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent_qa_automated.log", mode="w", encoding="utf-8")
    ]
)


AZURE_OPENAI_ENDPOINT = "https://cog-gpn-chatgpt-dev-openai-02.openai.azure.com/"
AZURE_OPENAI_API_KEY = "74d9fff52c024d91a6500f37d4002144"
ASSISTANT_ID = "asst_P3GFW4uWQ2EWCSbZro8hkUZo"

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-05-01-preview"
)



def wait_for_response(thread_id: str, run_id: str, max_retries=8, wait_seconds=2) -> Optional[str]:
    """Waits for the assistant's response in the given thread."""
    for attempt in range(max_retries):
        try:
            run: Run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            while run.status in ["queued", "in_progress", "cancelling"]:
                logging.debug(f"Run status: {run.status}")
                time.sleep(wait_seconds)
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                assistant_messages = [m for m in messages.data if m.role == "assistant" and m.content]
                if assistant_messages:
                    longest_message = max(
                        assistant_messages,
                        key=lambda m: len(m.content[0].text.value) if m.content and hasattr(m.content[0], 'text') and hasattr(m.content[0].text, 'value') else 0
                    )
                    return longest_message.content[0].text.value
                return "ERROR: No assistant response found."
            elif run.status == "requires_action":
                logging.warning(f"Run requires action for run_id={run_id}")
                return "ERROR: requires_action"
            else:
                logging.warning(f"Attempt {attempt+1}/{max_retries} failed: {run.status}")
                time.sleep(wait_seconds)
        except Exception as exc:
            logging.error(f"Error retrieving run: {exc}")
            time.sleep(wait_seconds)
    logging.error(f"No response after several attempts for run_id={run_id}")
    return "ERROR: no response after several attempts"



def get_openai_response(question: str) -> str:
    """Queries the OpenAI API and returns the response using the thread/run pattern."""
    try:
        # Create a thread
        thread = client.beta.threads.create()
        # Add a user question to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )
        # Run the thread
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        # Loop until the run completes or fails
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_messages = [m for m in messages.data if m.role == "assistant" and m.content]
            if assistant_messages:
                # Return the longest message (as in previous logic)
                longest_message = max(
                    assistant_messages,
                    key=lambda m: len(m.content[0].text.value) if m.content and hasattr(m.content[0], 'text') and hasattr(m.content[0].text, 'value') else 0
                )
                return longest_message.content[0].text.value
            return "ERROR: No assistant response found."
        elif run.status == "requires_action":
            # the assistant requires calling some functions and submit the tool outputs back to the run
            return "ERROR: requires_action"
        else:
            return f"ERROR: run status {run.status}"
    except Exception as exc:
        logging.error(f"Error processing question: {exc}")
        return f"ERROR: {exc}"


def process_question(question: str) -> str:
    """Processes a question using get_openai_response."""
    return get_openai_response(question)


def process_dataset(df: pd.DataFrame, question_limit: Optional[int] = None) -> pd.DataFrame:
    """Processes all questions in the DataFrame and returns the DataFrame with the 'Respuesta' column."""
    if 'Pregunta' not in df.columns:
        logging.error("The file must have a column named 'Pregunta'.")
        raise ValueError("The file must have a column named 'Pregunta'.")
    if question_limit:
        df = df.head(question_limit)
    questions = list(df['Pregunta'])
    responses = []
    for idx, question in enumerate(questions, start=1):
        logging.info(f"Processing question {idx}/{len(questions)}")
        response = process_question(question)
        responses.append(response)
        logging.info(f"Response received for question {idx}: {response}")
    # Retry if there are errors or empty responses
    for idx, resp in enumerate(responses):
        if not resp or resp.startswith("ERROR"):
            logging.info(f"Retrying question {idx+1} due to empty response or error...")
            responses[idx] = process_question(questions[idx])
    df['Respuesta'] = responses
    return df


def evaluate_questions(input_file: str, output_file: str, question_limit: Optional[int] = 2):
    """Reads the input file, processes the questions, and saves the result to output_file."""
    logging.info(f"Reading input file: {input_file}")
    df = pd.read_excel(input_file)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed:')]
    df_result = process_dataset(df, question_limit)
    df_result.to_excel(output_file, index=False)
    logging.info(f"Process completed. File generated: {output_file}")


def update_responses_by_case(output_file: str, cases: list):
    """Updates the response of specific questions in output_file using the IDs from the 'Caso' column."""
    logging.info(f"Updating responses in file: {output_file} for cases: {cases}")
    df = pd.read_excel(output_file)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed:')]
    if 'Caso' not in df.columns or 'Pregunta' not in df.columns:
        logging.error("The file must have columns 'Caso' and 'Pregunta'.")
        raise ValueError("The file must have columns 'Caso' and 'Pregunta'.")
    for case_id in cases:
        idxs = df.index[df['Caso'] == case_id].tolist()
        if not idxs:
            logging.warning(f"Case {case_id} not found in the file.")
            continue
        for idx in idxs:
            question = df.at[idx, 'Pregunta']
            logging.info(f"Updating case {case_id} (index {idx})...")
            logging.info(f"Question sent: {question}")
            new_response = process_question(question)
            df.at[idx, 'Respuesta'] = new_response
            logging.info(f"Response updated for case {case_id}: {new_response}")
    df.to_excel(output_file, index=False)
    logging.info(f"Responses updated in file: {output_file}")


if __name__ == "__main__":
    input_file = "Iteraciones de Pruebas Web.xlsx"
    output_file = "sol_test_evaluation.xlsx"
    # Main process: process all questions
    evaluate_questions(
        input_file=input_file,
        output_file=output_file,
        question_limit=None
    )

    # Example manual usage to update responses for specific cases:
    # cases_to_update = [22, 35, 113]
    # update_responses_by_case(output_file, cases_to_update)
