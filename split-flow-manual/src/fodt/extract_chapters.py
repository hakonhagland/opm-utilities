import io
import logging
import re
import xml.sax
import xml.sax.handler
import xml.sax.xmlreader
import xml.sax.saxutils

from pathlib import Path

from fodt.constants import AutomaticStyles, Directories, FileNames, FileExtensions
from fodt.exceptions import HandlerDoneException, InputException

class ChapterHandler(xml.sax.handler.ContentHandler):
    def __init__(self, outputdir: str, chapters: list[int]) -> None:
        self.outputdir = outputdir
        self.chapters = chapters
        self.outline_level = "1"
        self.current_section = 0
        self.next_section = self.chapters.pop(0)
        self.styles = set()
        self.section = None
        self.in_section = False
        self.style_attrs = AutomaticStyles.attr_names

    def add_section_start(
        self,
        name:str,
        attrs: xml.sax.xmlreader.AttributesImpl,
    ) -> None:
        self.section.write(f"<{name}")
        for (key, value) in attrs.items():
            evalue = xml.sax.saxutils.escape(value)
            self.section.write(f" {key}=\"{evalue}\"")
        self.section.write(">")

    def collect_styles(self, attrs: xml.sax.xmlreader.AttributesImpl) -> None:
        for (key, value) in attrs.items():
            if key in self.style_attrs:
                self.styles.add(value)

    def startElement(self, name:str, attrs: xml.sax.xmlreader.AttributesImpl):
        # logging.info(f"startElement: {name}")
        if name == "text:h":
            if "text:outline-level" in attrs.getNames():
                level = attrs.getValue("text:outline-level")
                if level == self.outline_level:
                    if self.in_section:
                        self.write_section_to_file()
                        self.write_styles_to_file()
                        self.in_section = False
                        if len(self.chapters) > 0:
                            self.next_section = self.chapters.pop(0)
                        else:
                            raise HandlerDoneException(f"Done extracting parts.")
                    self.current_section += 1
                    if self.current_section == self.next_section:
                        # NOTE: we will use io.StringIO, since appending
                        #   is much faster than appending to a string.
                        #  See: https://waymoot.org/home/python_string/
                        self.section = io.StringIO()
                        self.styles = set()
                        self.in_section = True
        if self.in_section:
            self.add_section_start(name, attrs)
            self.collect_styles(attrs)

    def endElement(self, name: str):
        if self.in_section:
            self.section.write(f"</{name}>")

    def characters(self, content: str):
        if self.in_section:
            self.section.write(xml.sax.saxutils.escape(content))

    def write_section_to_file(self):
        subsection = self.current_section
        filename = f"{subsection}.{FileExtensions.xml}"
        dir_ = Path(self.outputdir) / Directories.chapters
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / filename
        if path.exists():
            logging.info(f"Section {subsection} : File {filename} already exists, skipping.")
        else:
            with open(path, "w", encoding='utf8') as f:
                f.write(self.section.getvalue())
            logging.info(f"Wrote section {subsection} to file {filename}.")
        self.section = None

    def write_styles_to_file(self) -> None:
        subsection = self.current_section
        filename = f"{subsection}.{FileExtensions.txt}"
        dir_ = Path(self.outputdir) / Directories.styles
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / filename
        if path.exists():
            logging.info(f"Section {subsection} : File {filename} already exists, skipping.")
        else:
            with open(path, "w", encoding='utf8') as f:
                for style in sorted(self.styles):
                    f.write(f"{style}\n")
            logging.info(f"Wrote styles to file {filename}.")


class ExtractChapterParts():
    def __init__(self, maindir: str, filename: str, chapters: list[int]) -> None:
        logging.info(f"Extracting parts {chapters} from {filename}.")
        parser = xml.sax.make_parser()
        if len(chapters) == 0:
            raise InputException("No chapter numbers specified.")
        if min(chapters) < 1:
            raise InputException("Chapter numbers should be >= 1.")
        outputdir = Path(maindir) / Directories.info
        handler = ChapterHandler(outputdir, chapters)
        parser.setContentHandler(handler)
        try:
            parser.parse(filename)
        except HandlerDoneException as e:
            pass
        logging.info(f"Done extracting chapters.")
