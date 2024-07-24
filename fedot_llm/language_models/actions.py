import os
import json
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from requests.exceptions import RequestException
import pandas as pd
from fedot_llm.data.data import Dataset, Split
import random
import re
import ast
from tenacity import retry, stop_after_attempt
from typing import Dict

_MAX_RETRIES = 6

class ModelAction():
    
    def __init__(self, model) -> None:
        self.model = model

    def run_model_call(self, system, context, task):
        """Run a prompt on model
        """
        self.model.set_sys_prompt(system)
        self.model.set_context(context)
        response = self.model(task, as_json=True)
        return response

    def run_model_multicall(self, prompts):
        """Run a list of prompts on web model
        """
        responses = {}
        for task in prompts:
            response = self.run_model_call(
                system = prompts[task]["system"],
                context = prompts[task]["context"],
                task = prompts[task]["task"]
            )
            responses[task] = response
        return responses
    
    @staticmethod
    def process_model_responses(responses, operations):
        for key in operations:
            responses[key] = operations[key](responses[key])
        return responses

    @classmethod
    def process_model_responses_for_v1(cls, responses):
        operations = {
            "categorical_columns": lambda x : x.split("\n"),
            "task_type": lambda x : x.lower()
        }
        responses = cls.process_model_responses(responses, operations)
        return responses

    @staticmethod
    def save_model_responses(responses, path):
        with open(os.sep.join([path, 'model_responses.json']), 'w') as json_file:
            json.dump(responses, json_file)
            
    @retry(
        stop=stop_after_attempt(_MAX_RETRIES),
        reraise=True
    )
    def __generate_column_description(self, column: pd.Series, split: Split, dataset: Dataset):
        """
        Generate a description for a column.

        Args:
        - column (pd.Series): The column for which the description is generated.
        - dataset (Dataset): The dataset containing the column.

        Returns:
        dict: A dictionary containing the generated description for the column.

        Raises:
        RuntimeError: If the answer is not found in the response or if the 'data' node is not found in the response.
        """
        FIND_ANSWER = re.compile(
            r"\{['\"]data['\"]\s*:\s*\{['\"]type['\"]\s*:\s*['\"]string['\"]\s*\,\s*['\"]description['\"]\s*:\s*['\"].*['\"]\}\}")

        user_template = """Dataset Title: {title}
        Dataset description: {ds_descr}
        Column name: {col_name}
        Column hint: {hint}
        Column values: 
        ```
        {values}
        ```
        """

        self.model.set_context(column.head(30).to_markdown(index=False))
        column_uniq_vals = column.unique().tolist()
        column_vals = pd.Series(column_uniq_vals if len(
            column_uniq_vals) < 30 else random.sample(column_uniq_vals, k=30), name=column.name)
        user_prompt = user_template.format(
            title=dataset.name,
            ds_descr=dataset.description,
            col_name=column.name,
            hint=split.get_column_hint(column.name),
            values=column_vals.to_markdown(index=False)
        )
        response = self.model(user_prompt, as_json=True)
        response = response.strip().replace('\n', '').capitalize()

        answer = re.findall(FIND_ANSWER, response)
        if not answer:
            raise RuntimeError("Answer not found in: ", response)

        dict_resp = ast.literal_eval(answer[0])
        if "data" not in dict_resp:
            raise RuntimeError("Data node not found in: ", response)
        return dict_resp

    def generate_all_column_description(self, split: Split, dataset: Dataset) -> Dict[str, str]:
        """ Generate descriptions for all columns in the provided table.

        Args:
            split (pd.DataFrame): A split representing the table with columns to describe.
            dataset (Dataset): The dataset used for generating column descriptions.

        Returns:
            A dictionary where keys are column names and values are descriptions generated for each column.
        """

        schema = {
            "data": {
                "type": "string",
                "description": "one line plain text"
            }
        }

        sys_prompt = """You are helpful AI assistant.
        User will enter one column from dataset, and the assistant will make one sentence discription of data in this column.
        Don't make assumptions about what values to plug into functions. Use column hint.
        Output format: only JSON using the schema defined here: {schema}""".format(schema=json.dumps(schema))

        self.model.set_sys_prompt(sys_prompt)

        result = {}

        for col_name in split.data.columns:
            result[col_name] = self.__generate_column_description(column=split.data[col_name],
                                                                  split=split,
                                                                  dataset=dataset)['data']['description']
        return result



# def run_model_multicall(model, tokenizer, generation_config, prompts):
#     """Run all prompts on local model

#     TODO: transform to an interaction with local model helper class
#     """
    
#     responses = {}
#     for task in prompts:
#         messages = [
#             {"role": "system", "content": prompts[task]["system"]},
#             {"role": "context", "content": prompts[task]["context"]},
#             {"role": "user", "content": prompts[task]["task"]},
#         ]
        
#         input_ids = tokenizer.apply_chat_template(
#             messages,
#             add_generation_prompt=True,
#             return_tensors="pt"
#         ).to(model.device)
        
#         outputs = model.generate(
#             input_ids,
#             **generation_config
#         )
#         response = outputs[0][input_ids.shape[-1]:]
#         responses[task] = tokenizer.decode(response, skip_special_tokens=True)

#     return responses
