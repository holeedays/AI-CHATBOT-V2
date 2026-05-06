import os
import json
from typing import Any
from ... import models as mdls 

from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Parse JSON files and stores them as document objects; Currently only for my ARS essay"

    # add argv arguments that we can feed to our handle method
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--path", 
                            type=str, 
                            help="File path to the directory containing the documents. Absolute path should be used")

    def handle(self, *args: Any, **kwargs: Any) -> None:
        dir_path: str = kwargs.get("path") # type: ignore
        self.store_essay_contents_in_db(dir_path)
    
    # this is specifically to store the contents of my essay
    def store_essay_contents_in_db(self, dir_path_to_essay: str):
        for dirpath, dirname, files in os.walk(os.path.normpath(dir_path_to_essay)):
            for file in files:
                # even for file writes, we have to use absolute pathing; relative pathing doesn't work prob
                # cause we're referring to a different root
                abs_path: str = os.path.normpath(dirpath + "/" + file)
                match(file):
                    case("1_introduction.json"):
                        self.create_unique_document_in_db(abs_path, 
                                                    "ARS Essay Introduction", 
                                                    "Intro to my ARS essay, including thesis and title.")
                    case("2_body.json"):
                        self.create_unique_document_in_db(abs_path, 
                                                    "ARS Essay Body", 
                                                    "Body of my ARS essay.")
                    case("3_conclusion.json"):
                        self.create_unique_document_in_db(abs_path, 
                                                    "ARS Essay Conclusion", 
                                                    "Conclusion of my ARS essay.")
                    case("4_footnotes.json"):
                        self.create_unique_document_in_db(abs_path, 
                                                    "ARS Essay Footnotes", 
                                                    "Footnotes of my ARS essay.")
                    case("5_bibliography.json"):
                        self.create_unique_document_in_db(abs_path, 
                                                    "ARS Essay Bibliography", 
                                                    "Bibliography of my ARS essay. Similar to the footnotes.")
                    # default method if none of the other case statements are resolved
                    case("6_image_appendix_local_links.json"):
                        self.create_unique_document_in_db(abs_path, 
                                                    "ARS Essay Image Appendix", 
                                                    "Image appendix of my ARS essay, contains links and citations.")
                    case _:
                        self.stdout.write("There was another file detected or path is invalid. Check!")
                        pass

    # just a generic method to create other documents in my database
    def create_unique_document_in_db(self, abs_path_to_file: str, name: str, description: str = "") -> None:
        if (mdls.Document.objects.filter(name=name).exists()):
            self.stdout.write(f"{name} is already stored in the database") # print's more sturdy equivalent
            return
        
        with open(abs_path_to_file, "b+r") as json_f:
            mdls.Document(name=name, 
                            description=description,
                            contents=json.load(json_f)).save()
        self.stdout.write(self.style.SUCCESS(f"{name} is now stored!"))