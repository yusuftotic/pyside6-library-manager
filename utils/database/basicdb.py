import json
import os
import uuid
import copy

class BasicDB:

    def __init__(self, collection_name: str, root_dir : str):
        self.collection_name = collection_name

        self.base_dir = os.path.join(os.path.dirname(root_dir), "data")
        self.file_path = os.path.join(self.base_dir, f"{self.collection_name}.json")

        self._ensure_data_directory_exists()
        self._ensure_collection_file_exists()
        


    def _ensure_data_directory_exists(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            print(f"[INFO] - '{self.base_dir}' directory was created.")
            

    def _read_all_documents(self) -> list:
        try:
            with open(self.file_path, mode="r", encoding="utf-8") as file:
                return json.load(file)
            
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
    def _write_all_documents(self, documents: list):
        try:
            with open(self.file_path, mode="w", encoding="utf-8") as file:
                json.dump(documents, file, ensure_ascii=True, indent=2)
        
        except IOError as err:
            print(f"[ERROR] - {self.collection_name}.json dosyasına yazma hatası: {err}")
            raise


    def _ensure_collection_file_exists(self):
        if not os.path.exists(self.file_path):
            self._write_all_documents([])
            print(f"[INFO] - '{self.collection_name}.json' file was created.")


    # CREATE Opearations

    def create(self, doc: dict) -> dict:
        
        if not isinstance(doc, dict):
            raise ValueError("Documents must be a dictionary.")
        
        _id = uuid.uuid4().hex
        
        documents = self._read_all_documents()

        new_doc = copy.deepcopy(doc)
        new_doc["_id"] = _id

        documents.append(new_doc)

        self._write_all_documents(documents)
        
        print(f"[INFO] - Belge eklendi: {new_doc.get('title', new_doc.get('name', new_doc['_id']))}")
        
        return new_doc
        
    
    # READ Operations

    def find(self, query: dict=None) -> list:
        
        documents = self._read_all_documents()

        if not query:
            return documents

        results = []
        for doc in documents:
            query_bools = []
            for key, value in query.items():
                if key in doc and doc[key] == value:
                    query_bools.append(True)
                else:
                    query_bools.append(False)
            if all(query_bools):
                results.append(doc)

        # results = [
        #     doc for doc in documents
        #     if all(key in doc and doc[key] == value for key, value in query.items())
        # ]

        if results:
            return results

        return None
    
    
    def find_by_id(self, _id: str) -> dict | None:
        
        documents = self._read_all_documents()

        # result = [
        #     doc for doc in documents if doc and doc["_id"] == _id
        # ]

        result = None

        for doc in documents:
            if doc["_id"] == _id:
                result = doc
            
        return result


    # UPDATE Operations

    def find_by_id_and_update(self, _id: str, update: dict) -> dict | None:

        documents = self._read_all_documents()
        
        doc = self.find_by_id(_id)

        if not doc:
            return None

        doc_index = documents.index(doc)

        update["_id"] = _id

        documents[doc_index] = update

        self._write_all_documents(documents)

        return update


    # DELETE Operations

    def find_by_id_and_delete(self, _id: str):
        
        documents = self._read_all_documents()
        
        doc = self.find_by_id(_id)

        doc_index = documents.index(doc)

        documents.pop(doc_index)

        self._write_all_documents

