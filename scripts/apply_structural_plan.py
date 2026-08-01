#!/usr/bin/env python3
"""Apply the matrix-approved spine additions, removals, and section merges."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
I18N = CONTENT / "i18n" / "en-GB"

REMOVE_SECTIONS = {
    "qz001", "qz002", "qz003", "qz004", "qz005", "qz006", "qz007",
    "pg037_sec002", "pg050_sec001", "pg054_sec001", "pg059_sec001",
}
INSERTED_SECTIONS = {"pg002_sec001", "pg004_sec001", "pg088_sec001"}

NEW_TEXT = {
    "pg002_n0001": "© Tanzania Institute of Education 2023",
    "pg002_n0002": "Published 2023",
    "pg002_n0003": "ISBN: 978-9987-09-968-9",
    "pg002_n0004": "Tanzania Institute of Education",
    "pg002_n0005": "Mikocheni Area, 132 Ali Hassan Mwinyi Road, P.O. Box 35094, 14112 Dar es Salaam",
    "pg002_n0006": "Telephone:",
    "pg002_n0007": "+255 735 041 170 / 735 041 168",
    "pg002_n0008": "Email:",
    "pg002_n0009": "director.general@tie.go.tz",
    "pg002_n0010": "Website:",
    "pg002_n0011": "www.tie.go.tz",
    "pg002_n0012": "All rights reserved. No part of this textbook may be reproduced, stored in any retrieval system or transmitted in any form or by any means, electronic, mechanical, photocopying, recording or otherwise, without a prior written permission from the Tanzania Institute of Education.",
    "pg004_n0001": "Acknowledgements",
    "pg004_n0002": "The Tanzania Institute of Education (TIE) acknowledges the contributions of all the organisations and individuals who participated in the designing and development of this textbook. In particular, TIE wishes to thank the University of Dar es Salaam (UDSM), Jordan University College (JUCo), the School Quality Assurance (SQA) Department, Teachers’ Colleges and Primary Schools. Besides, the following individuals are acknowledged:",
    "pg004_n0003": "Writers:",
    "pg004_n0004": "Dr Christopher M. William, Dr Clement M. Mromba, Mr Karani H. Mdee, Ms Blandina F. Ajali, and Ms Selestina C. Lwanga",
    "pg004_n0005": "Editors:",
    "pg004_n0006": "Dr Lydia A. Kimaryo, Dr Verdiana T. Tilumanywa, Dr Johnstone M. Andrea, Dr Jackson R. Sawe, Ms Ndimbwumi J. Mboneke and Ms Dalia C. Kilamlya",
    "pg004_n0007": "Designer:",
    "pg004_n0008": "Ms Mariam Matotola",
    "pg004_n0009": "Illustrators:",
    "pg004_n0010": "Mr Fikiri A. Msimbe and Mr Yohana P. Mwenda",
    "pg004_n0011": "Photographer:",
    "pg004_n0012": "Mr Chrisant A. Ignas",
    "pg004_n0013": "Coordinator:",
    "pg004_n0014": "Mr Karani H. Mdee",
    "pg004_n0015": "TIE also appreciates contributions from primary school teachers and pupils who participated in the trial phase of the textbook. The Institute would like to thank the National",
    "pg088_n0001": "Bibliography",
    "pg088_n0002": "Engler, H. J., Matthews, T., Bushaw, W., & Stooksberry, L. (2018). Geography framework for the 2018 national assessment of educational progress. U.S. Department of Education.",
    "pg088_n0003": "Joseph H. (2010). An introduction to physical Geography and the environment. Pearson education Limited.",
    "pg088_n0004": "KICD. (2021). Republic of Kenya upper primary level designs subject social studies grade 6 (1st ed.). Kenya Institute of Curriculum Development.",
    "pg088_n0005": "Leslie, A. D. (2021). Environmental Geography: People and the Environment. Understanding our World.",
    "pg088_n0006": "Taasisi ya Elimu Tanzania. (2018). Maarifa ya Jamii, Kitabu cha Mwanafunzi Darasa la 3. Taasisi ya Elimu Tanzania.",
    "pg088_n0007": "Taasisi ya Elimu Tanzania. (2018). Maarifa ya Jamii, Kitabu cha Mwanafunzi Darasa la 4. Taasisi ya Elimu Tanzania.",
    "pg088_n0008": "Taasisi ya Elimu Tanzania. (2018). Maarifa ya Jamii, Kitabu cha Mwanafunzi Darasa la 5. Taasisi ya Elimu Tanzania.",
    "pg088_n0009": "Wizara ya Elimu, Sayansi na Teknolojia. (2023). Muhtasari wa Somo la Jiografia na Mazingira Elimu ya Msingi Darasa la III–VI. Taasisi ya Elimu Tanzania.",
}

CHANGED_TEXT = {
    "pg050_n0007": "1. With examples, give a summary of the condition of the land in your environment; and",
    "pg050_n0008": "2. Suggest ways to conserve the land in the area you live in.",
    "pg059_n0004": "1. Identify different human activities undertaken near or in the water source; and",
    "pg059_n0005": "2. Give a summary explaining how the activities destroy the water source.",
}


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_pages() -> list[dict]:
    pages_path = CONTENT / "pages.json"
    pages = [
        entry
        for entry in json.loads(pages_path.read_text(encoding="utf-8"))
        if entry["section_id"] not in REMOVE_SECTIONS | INSERTED_SECTIONS
    ]

    def insert_after(section_id: str, entry: dict) -> None:
        index = next(i for i, value in enumerate(pages) if value["section_id"] == section_id)
        pages.insert(index + 1, entry)

    insert_after("pg001_sec001", {"section_id": "pg002_sec001", "href": "pg002_sec001.html"})
    insert_after("pg003_sec001", {"section_id": "pg004_sec001", "href": "pg004_sec001.html"})
    pages.append({"section_id": "pg088_sec001", "href": "pg088_sec001.html", "page_number": 82})
    write_json(pages_path, pages)
    return pages


def update_toc() -> None:
    toc_path = CONTENT / "toc.json"
    original = json.loads(toc_path.read_text(encoding="utf-8"))
    toc = []
    for item in original:
        section_id = item["section_id"]
        if section_id in INSERTED_SECTIONS:
            continue
        if section_id in REMOVE_SECTIONS:
            if section_id == "pg050_sec001":
                item = {**item, "section_id": "pg050_sec002", "href": "pg050_sec002.html"}
            elif section_id == "pg054_sec001":
                item = {**item, "section_id": "pg054_sec002", "href": "pg054_sec002.html"}
            else:
                continue
        if section_id == "pg054_sec002":
            continue
        toc.append(item)

    toc.insert(0, {
        "section_id": "pg004_sec001", "href": "pg004_sec001.html",
        "title": "Acknowledgements", "chapter_id": "pg004_n0001", "level": 1,
    })
    toc.append({
        "section_id": "pg088_sec001", "href": "pg088_sec001.html",
        "title": "Bibliography", "chapter_id": "pg088_n0001", "level": 1,
    })
    write_json(toc_path, toc)


def renumber_html(pages: list[dict]) -> None:
    pattern = re.compile(r'(<meta\s+name="page-section-id"\s+content=")[^"]*(")')
    for position, entry in enumerate(pages, 1):
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        updated, count = pattern.subn(rf"\g<1>{position}\g<2>", source, count=1)
        if count != 1:
            raise ValueError(f"Could not renumber {entry['href']}")
        path.write_text(updated, encoding="utf-8")


def update_manifest(pages: list[dict]) -> None:
    path = ROOT / "imsmanifest.xml"
    source = path.read_text(encoding="utf-8")
    block = "\n".join(f'      <file href="{entry["href"]}"/>' for entry in pages)
    updated, count = re.subn(
        r'      <file href="index\.html"/>.*?      <file href="pg087_sec001\.html"/>',
        block,
        source,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise ValueError("Could not replace manifest page list")
    path.write_text(updated, encoding="utf-8")


def update_localization() -> None:
    texts_path = I18N / "texts.json"
    texts = json.loads(texts_path.read_text(encoding="utf-8"))
    for key in list(texts):
        if re.match(r"^qz\d{3}", key):
            del texts[key]
    for key, value in {**NEW_TEXT, **CHANGED_TEXT}.items():
        texts[key] = value
        texts[f"{key}_easy_read"] = value
    write_json(texts_path, texts)

    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    for key in list(audios):
        if re.match(r"^qz\d{3}", key):
            del audios[key]
    write_json(audios_path, audios)


def update_scorm() -> None:
    path = ROOT / "assets" / "scorm.js"
    source = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"var ALL_ACTIVITY_IDS = \[[^\]]*\];",
        "var ALL_ACTIVITY_IDS = [];",
        source,
        count=1,
    )
    if count != 1:
        raise ValueError("Could not update SCORM activity list")
    path.write_text(updated, encoding="utf-8")


def main() -> None:
    pages = update_pages()
    update_toc()
    renumber_html(pages)
    update_manifest(pages)
    update_localization()
    update_scorm()
    print(f"Structural plan applied: {len(pages)} spine entries.")


if __name__ == "__main__":
    main()
