import numpy as np
import pandas as pd
import regex as re
import os
import torch
from datasets import Dataset



class Datasetloader:

    kaggle:bool = False

    def __init__(self):
        self.kaggle = os.path.exists('/kaggle/input/csnlp-processed/data')

    def load_data(self, name, question_type="all"):
        if self.kaggle:
            data = pd.read_parquet(f'/kaggle/input/csnlp-processed/data/{name}.pq')
        else:
            if os.path.exists(f'./data/{name}.pq'):
                data = pd.read_parquet(f'./data/{name}.pq')
            else:
                data = pd.read_parquet(f'../data/{name}.pq')

        print(data.columns)

        def get_id(row):
            if name == "khan":
                return f"{row.id}_{row.Book}"
            if "Book" in data.columns:
                return f"{row.Chapter}_{row.Book}"
            return f"{row.Chapter}"
        

        lectures = {}

        for row in data.itertuples():
            id = get_id(row)
            if len(id) < 3:
                continue
            if "good" in row._fields and getattr(row, "good") == 0:
                continue
            if len(row.text) < 200:
                continue
            text = re.sub(r'\n', '', row.text, flags=re.MULTILINE)
            if text.__contains__("Here you'll learn"):
                print("found one in " + name)
            if id in lectures:
                if len(text) > len(lectures[id]):
                    lectures[id] = text
            else:
                lectures[id] = text

        # change the lectures dict so that each entry is an object with the lecture text and an empty array (for the questions)
        for key in lectures:
            lectures[key] = [lectures[key], []]

        for row in data.itertuples():
            id = get_id(row)
            if len(id) < 3:
                continue
            if "good" in row._fields and getattr(row, "good") == 0:
                continue
            if id in lectures:
                blacklist = ["CC", "Attribution", "__", "—", "true", "True", "false", "False", "http"]
                if len(row.text) < len(lectures[id][0]) and len(row.text) > 20 and len(row.text) < 200 and not any(x in row.text for x in blacklist) and not row.text.startswith("I ") and not row.text.startswith("My "):
                    text = re.sub(r'\n', '', row.text, flags=re.MULTILINE)
                    if question_type == "all":
                        lectures[id][1].append(text)
                    else:
                        #check if the row tuple contains field question_type and it is 1
                        if question_type in row._fields and getattr(row, question_type) == 1:
                            lectures[id][1].append(text)
                            
            else:
                print(f"Missing lecture for question: {id}")
                # print(row)

        # remove lectures with no questions
        lectures = {k: v for k, v in lectures.items() if len(v[1]) > 0}

        return lectures
    

    def load_all_raw_data(self, question_type="all"):
        lectures_dict = {}
        for dataset in ['openstax', 'opentext', 'ck12']: 
        # for dataset in ['opentext']: 
        # for dataset in ['opentext']: 
            lectures = self.load_data(dataset, question_type=question_type)
            questions_count = 0
            for key in lectures:
                questions_count+=len(lectures[key][1])
            print("loaded " + dataset + " with " + str(len(lectures)) + " lectures and " + str(questions_count) + " questions")
            lectures_dict.update(lectures)

        return lectures_dict



    def get_info(self, lectures_dict):
        print(len(lectures_dict))
        # print some random lectures followed by their questions
        for i in range(20):
            lecture = lectures_dict[np.random.randint(len(lectures_dict))]
            print("lecture: " + lecture[0][:200])
            print("questions: ")
            for question in lecture[1]:
                print(question[:200])
            print("")





    def load_all_data_for_hf_GPT(self, tokenizer, generate_prompt, model_name="", max_lecture_len=3200, max_question_group_len=1000, tokenizer_max_len=1000, cache=False, question_type="all", max_lectures_returned=-1):
        clean_name = model_name.replace("/","_")

        if cache:
            if os.path.exists(f'./data/{clean_name}_cache.pt'):
                stuff = torch.load(f'./data/{clean_name}_cache.pt')
                return stuff['train_questions'], stuff['val_questions'], stuff['lectures_dict'], stuff['train_dataset'], stuff['val_dataset']
            
        


        def tokenize_function(example,tokenizer=tokenizer, tokenizer_max_len=tokenizer_max_len):
            return tokenizer(example['text'], truncation=True, padding='max_length', max_length=tokenizer_max_len)
        def create_dataset(lectures):
            data = []
            for text, questions in lectures:
                question_group = "\n".join(questions)
                prompt = generate_prompt(text, question_group, max_lecture_len, max_question_group_len)
                # print(prompt)
                data.append({'text': prompt})
                # break
            dataset = Dataset.from_dict({"text": [example["text"] for example in data]})
            tokenized_dataset = dataset.map(tokenize_function, batched=True, num_proc=4, remove_columns=["text"])
            return tokenized_dataset

        
        lectures_dict = self.load_all_raw_data(question_type=question_type)

        # each element in lectures is a tuple of (lecture_text, [question1, question2, ...])
        lectures = list(lectures_dict.values())
        # print(lectures[0][0][:200])
        # print(lectures[0][1])

        if max_lectures_returned != -1:
            lectures = lectures[:max_lectures_returned]
        
        np.random.seed(43)
        np.random.shuffle(lectures) 

        train_lectures = lectures[:int(len(lectures)*0.8)]
        val_lectures = lectures[int(len(lectures)*0.8):]

        train_dataset = create_dataset(lectures)
        val_dataset = create_dataset(lectures)

        #save to cache
        folder = "./data/" if os.path.exists("./data/") else "../data/"
        torch.save({'train_lectures': train_lectures, 'val_lectures': val_lectures, 'train_dataset': train_dataset, 'val_dataset': val_dataset}, f'{folder}{clean_name}_cache.pt')

        return train_lectures, val_lectures, train_dataset, val_dataset



    def load_all_data_for_bert(self, model_name="", max_lecture_len=3200, tokenizer_max_len=1000, cache=False, question_type="all"):
        pass